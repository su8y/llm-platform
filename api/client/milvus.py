import asyncio
import json
import logging
import math
import os
from dataclasses import dataclass
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel
from pymilvus import DataType, Function, FunctionType
from pymilvus import MilvusClient as MilvusConnection

from utils.error import AppError, VectorDBError


class MilvusResponse(BaseModel):
    id: str | int
    score: float
    metadata: dict


class MilvusClientConnector:
    _client: MilvusConnection | None = None
    _lock = asyncio.Lock()
    _collections: dict[str, bool] = {}

    @classmethod
    async def connect(cls) -> None:
        async with cls._lock:
            if cls._client is None:
                try:
                    cls._client = await asyncio.to_thread(
                        MilvusConnection,
                        uri=os.getenv("VECTOR_DB_URI", "http://vector:19530"),
                        token=os.getenv("VECTOR_DB_TOKEN", "root:Milvus"),
                        timeout=10.0,
                    )
                except Exception as error:
                    raise VectorDBError("Failed to connect to Milvus") from error

    @classmethod
    async def disconnect(cls) -> None:
        async with cls._lock:
            if cls._client is not None:
                try:
                    await asyncio.to_thread(cls._client.close)
                except Exception as error:
                    raise VectorDBError("Failed to close Milvus") from error
                finally:
                    cls._client = None
                    cls._collections.clear()

    @classmethod
    async def get_client(cls) -> MilvusConnection:
        await cls.connect()
        return cls._client


@dataclass
class MilvusClient:
    collection_name: str
    namespace: str | None = None
    _hybrid: bool = False
    _semaphore = asyncio.Semaphore(30)

    async def exists(self) -> bool:
        try:
            client = await MilvusClientConnector.get_client()
            return await asyncio.to_thread(client.has_collection, self.collection_name, timeout=10.0)
        except AppError:
            raise
        except Exception as error:
            raise VectorDBError("Failed to check Milvus collection") from error

    async def iterate(self, company_key: str, batch_size: int = 100) -> AsyncIterator[list[dict]]:
        if not company_key or not 1 <= batch_size <= 1000:
            raise VectorDBError("Company scope and batch size are required")
        if not await self.exists():
            raise VectorDBError("Source collection does not exist")
        iterator = await self._call(
            "query_iterator", filter=self._make_search_filter({"company_key": company_key}),
            batch_size=batch_size, output_fields=["id", "metadata"], consistency_level="Strong",
        )
        try:
            while True:
                async with self._semaphore:
                    batch = await asyncio.to_thread(iterator.next)
                if not batch:
                    break
                yield batch
        except AppError:
            raise
        except Exception as error:
            raise VectorDBError("Failed to read Milvus collection") from error
        finally:
            try:
                await asyncio.to_thread(iterator.close)
            except Exception:
                logging.error("[client.milvus.MilvusClient.iterate] 🔴 Failed to close iterator")

    @staticmethod
    def _make_search_filter(filters: dict | None) -> str:
        fields = {
            "is_on": "is_on",
            "isOn": "is_on",
            "data_type": "data_type",
            "company_key": 'metadata["company_key"]',
            "upload_file_id": 'metadata["upload_file_id"]',
            "id": 'metadata["id"]',
        }
        conditions = []
        for key, value in (filters or {}).items():
            if key not in fields:
                raise VectorDBError("Unsupported vector search filter")
            if isinstance(value, dict):
                if key == "data_type" and set(value) == {"$in"}:
                    values = value["$in"]
                    if not isinstance(values, list) or not values or not all(isinstance(item, str) for item in values):
                        raise VectorDBError("Invalid vector search filter value")
                    conditions.append(f"data_type in {json.dumps(values)}")
                    continue
                if set(value) != {"$eq"}:
                    raise VectorDBError("Unsupported vector search filter operator")
                value = value["$eq"]
            if not isinstance(value, (str, bool, int, float)):
                raise VectorDBError("Invalid vector search filter value")
            if isinstance(value, float) and not math.isfinite(value):
                raise VectorDBError("Invalid vector search filter value")
            if key in ("is_on", "isOn") and not isinstance(value, bool):
                raise VectorDBError("Active document filter must be boolean")
            conditions.append(f"{fields[key]} == {json.dumps(value, ensure_ascii=False)}")
        return " AND ".join(conditions)

    def _create_collection(self, client: MilvusConnection) -> None:
        try:
            dimension = int(os.getenv("VECTOR_DIMENSION", "1024"))
        except ValueError as error:
            raise VectorDBError("Vector dimension must be a positive integer") from error
        if dimension <= 0:
            raise VectorDBError("Vector dimension must be a positive integer")
        schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=10000)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dimension)
        schema.add_field("metadata", DataType.JSON)
        schema.add_field("data_type", DataType.VARCHAR, max_length=32)
        schema.add_field("is_on", DataType.BOOL)
        schema.add_field("text", DataType.VARCHAR, max_length=65535, enable_analyzer=True)
        schema.add_field("sparse", DataType.SPARSE_FLOAT_VECTOR)
        schema.add_function(Function(
            name="text_bm25", input_field_names=["text"],
            output_field_names=["sparse"], function_type=FunctionType.BM25,
        ))
        indexes = client.prepare_index_params()
        indexes.add_index("vector", index_type="AUTOINDEX", metric_type="COSINE")
        indexes.add_index("sparse", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")
        client.create_collection(
            collection_name=self.collection_name, schema=schema,
            index_params=indexes, timeout=10.0,
        )

    async def check_connection(self) -> MilvusConnection:
        client = await MilvusClientConnector.get_client()
        async with MilvusClientConnector._lock:
            collections = MilvusClientConnector._collections
            if self.collection_name not in collections:
                try:
                    if not await asyncio.to_thread(client.has_collection, self.collection_name, timeout=10.0):
                        await asyncio.to_thread(self._create_collection, client)
                    description = await asyncio.to_thread(
                        client.describe_collection, self.collection_name, timeout=10.0,
                    )
                    fields = {field["name"] for field in description["fields"]}
                    await asyncio.to_thread(client.load_collection, self.collection_name, timeout=10.0)
                    collections[self.collection_name] = {"text", "sparse"} <= fields
                    if not collections[self.collection_name]:
                        logging.warning(
                            "[client.milvus.MilvusClient.check_connection] 🔁 "
                            "Legacy collection uses dense search; reindex to enable BM25"
                        )
                except AppError:
                    raise
                except Exception as error:
                    raise VectorDBError("Failed to initialize Milvus collection") from error
            self._hybrid = collections[self.collection_name]
        return client

    async def _call(self, operation: str, **kwargs: Any) -> Any:
        try:
            client = await self.check_connection()
            async with self._semaphore:
                return await asyncio.to_thread(
                    getattr(client, operation), collection_name=self.collection_name,
                    timeout=10.0, **kwargs,
                )
        except AppError:
            raise
        except Exception as error:
            logging.error("[client.milvus.MilvusClient._call] 🔴 Milvus operation failed")
            raise VectorDBError("Milvus operation failed") from error

    async def insert_many(self, ids: list, values: list, metadatas: list, namespace: str | None = None) -> None:
        if not len(ids) == len(values) == len(metadatas):
            raise VectorDBError("Vector IDs, values and metadata must have equal lengths")
        if not ids:
            return
        records = [{
            "id": str(key), "vector": vector, "metadata": metadata,
            "data_type": metadata.get("data_type", "post"),
            "is_on": metadata.get("is_on", True), "text": metadata.get("content", ""),
        } for key, vector, metadata in zip(ids, values, metadatas)]
        await self._call("upsert", data=records)

    async def insert(self, id: str, value: list, metadata: dict, data_type: str, is_on: bool, namespace: str | None = None) -> None:
        await self.insert_many([id], [value], [{**metadata, "data_type": data_type, "is_on": is_on}])

    async def _search(self, data: list, field: str, metric: str, k: int, filters: dict | None) -> list[MilvusResponse]:
        expression = self._make_search_filter(filters)
        results = await self._call(
            "search", data=data, anns_field=field, limit=k, filter=expression,
            search_params={"metric_type": metric, "params": {}}, output_fields=["metadata"],
            consistency_level="Strong",
        )
        return [MilvusResponse(id=hit["id"], score=hit["distance"], metadata=hit["entity"]["metadata"])
                for group in results for hit in group]

    async def find(self, vector: list, k: int = 4, filter: dict | None = None) -> list[MilvusResponse]:
        return await self._search([vector], "vector", "COSINE", k, filter)

    async def find_lexical(self, query: str, k: int = 4, filter: dict | None = None) -> list[MilvusResponse]:
        await self.check_connection()
        if not self._hybrid or not query.strip():
            return []
        return await self._search([query], "sparse", "BM25", k, filter)

    async def fetch(self, ids: list, namespace: str | None = None) -> dict:
        if not ids:
            return {"vectors": {}}
        rows = await self._call("get", ids=[str(key) for key in ids], output_fields=["vector", "metadata"], consistency_level="Strong")
        return {"vectors": {row["id"]: {
            "id": row["id"], "values": row["vector"], "metadata": row["metadata"],
        } for row in rows}}

    async def update(self, ids: list, metadatas: list) -> None:
        if len(ids) != len(metadatas):
            raise VectorDBError("Vector IDs and metadata must have equal lengths")
        rows = (await self.fetch(ids))["vectors"]
        keys, values, metadata = [], [], []
        for key, changes in zip(ids, metadatas):
            row = rows.get(str(key))
            if row is not None:
                keys.append(str(key))
                values.append(row["values"])
                metadata.append({**row["metadata"], **changes})
        await self.insert_many(keys, values, metadata)

    async def remove(self, id: list | None = None, delete_all: bool = False, filter: dict | None = None) -> bool:
        if delete_all:
            expression = 'id != ""'
        elif id:
            expression = f"id in {json.dumps([str(key) for key in id])}"
        elif filter:
            expression = self._make_search_filter(filter)
        else:
            return False
        await self._call("delete", filter=expression)
        return True
