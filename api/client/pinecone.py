import os
import time
import logging
import asyncio
from dataclasses import dataclass
from typing import ClassVar, Optional
from pinecone.grpc import PineconeGRPC, Vector
from utils.error import VectorDBError
from utils.constants import REAL



class PineconeClientConnector:
    _client: ClassVar[Optional[PineconeGRPC]] = None
    _index: ClassVar[PineconeGRPC.Index] = None
    _current_index: ClassVar[str] = None
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @classmethod
    async def connect(cls):
        async with cls._lock:
            if cls._client is None:
                try:
                    cls._client = PineconeGRPC(api_key=os.getenv("PINECONE_API_KEY"))
                    logging.info("✅ connected Pinecone")
                except Exception as e:
                    logging.error(f"[PineconeClient.connect] 🔴 Exception: {e}")
                    raise VectorDBError(f"Failed to connect to Pinecone: {e}")


    @classmethod
    async def disconnect(cls):
        async with cls._lock:
            cls._client = None
            cls._index = None
            logging.info("🔴 disconnected Pinecone")


    @classmethod
    async def get_connection(cls):
        try:
            if cls._client is None:
                logging.info("[client.pinecone.PineconeClient.get_client] Try to connect")
                await cls.connect()
                logging.info("[client.pinecone.PineconeClient.get_client] Success to connect")
                return cls._client
            else:
                logging.info("[client.pinecone.PineconeClient.get_client] Connection is established")
                return cls._client
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.get_client] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to check connection to Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.get_client] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to check connection to Pinecone: {e}")


    @classmethod
    async def get_index(cls, index_name:str):
        try:
            if cls._client is None:
                await cls.connect()
            if cls._index is None or cls._current_index != index_name:
                cls._index = cls._client.Index(index_name)
                cls._current_index = index_name
            return cls._index

        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.get_index] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to check connection to Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.get_index] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to check connection to Pinecone: {e}")


    @classmethod
    async def initialize(cls):
        try:
            server_stage = os.getenv("SERVER_STAGE")
            default_index_name = "llm-platform" if server_stage == REAL else "llm-platform-staging"
            await cls.get_index(default_index_name)
            cls._current_index = default_index_name

        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.get_index] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to check connection to Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.get_index] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to check connection to Pinecone: {e}")



@dataclass
class PineconeClient:
    index_name: str = None
    namespace: str | list | tuple = None


    async def create_index(self):
        try:
            pc = await PineconeClientConnector.get_connection()
            pc.create_index(self.index_name, dimension=3072, spec={"cloud":"aws", "region":"us-east-1"})
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.create_index] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to create index: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.create_index] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to get index: {e}")


    async def get_index_list(self):
        try:
            pc = await PineconeClientConnector.get_connection()
            return pc.list_indexes()
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.get_index_list] 🔴 VectorDBError: {e}")
            raise VectorDBError(e)
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.get_index_list] 🔴 Exception: {e}")
            raise VectorDBError(e)


    async def insert(self, id:str, value:list[float], metadata:dict, namespace:str=None):
        try:
            if namespace is None and isinstance(self.namespace, (list, tuple)):
                logging.info(f"check namespace. self.namespace: {type(self.namespace)}, namespace: {type(namespace)}")
                raise Exception("namespace should be str or None.")
            index = await PineconeClientConnector.get_index(self.index_name)
            vectors = [{"id": id, "values": value, 'metadata': metadata}]
            await asyncio.to_thread(index.upsert, vectors=vectors, namespace=self.namespace or namespace)
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.insert] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to insert data to Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.insert] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to insert data to Pinecone: {e}")


    async def insert_many(self, ids:list, values:list, metadatas:list, namespace:str=None):
        try:
            if namespace is None and isinstance(self.namespace, (list, tuple)):
                logging.info(f"check namespace. self.namespace: {type(self.namespace)}, namespace: {type(namespace)}")
                raise Exception("namespace should be str or None.")
            index = await PineconeClientConnector.get_index(self.index_name)
            vectors = [
                {
                    "id": id,
                    "values": value,
                    "metadata": metadata
                } for id, value, metadata in zip(ids, values, metadatas)
            ]
            await asyncio.to_thread(index.upsert, vectors=vectors, batch_size=32, namespace=self.namespace or namespace)
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.insert_many] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to insert data to Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.insert_many] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to insert data to Pinecone: {e}")


    async def find_lexical(self, query: str, k: int = 4, filter: dict | None = None) -> list:
        """Legacy Pinecone indexes support dense retrieval only."""
        return []

    async def find(self, vector, k:int=4, filter:dict=None):
        try:
            index = await PineconeClientConnector.get_index(self.index_name)

            if isinstance(self.namespace, str):
                response = await asyncio.to_thread(index.query,
                    vector=vector,
                    top_k=k,
                    include_values=False,
                    include_metadata=True,
                    filter=filter,
                    namespace=self.namespace or None
                )
                if hasattr(response, "matches"):
                    sorted_matches = sorted(response.matches, key=lambda x: x.score, reverse=True)
                else:
                    sorted_matches = sorted(response['matches'], key=lambda x: x['score'], reverse=True)

            elif isinstance(self.namespace, list) or isinstance(self.namespace, tuple):
                task_list = list()
                for namespace in self.namespace:
                    task_list.append(
                        asyncio.to_thread(
                            index.query,
                            vector=vector,
                            top_k=k,
                            include_values=False,
                            include_metadata=True,
                            filter=filter,
                            namespace=namespace or None
                        )
                    )
                all_responses = await asyncio.gather(*task_list)
                sorted_matches_before_sort = list()
                for response in all_responses:
                    if hasattr(response, "matches"):
                        sorted_matches_before_sort.extend(response.matches)
                    else:
                        sorted_matches_before_sort.extend(response['matches'])
                sorted_matches = sorted(sorted_matches_before_sort, key=lambda x: x.score, reverse=True)

            else:
                raise Exception(f"namespace must be str, list, tuple when query. but the type of namespace is {type(self.namespace)}")

            return sorted_matches
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.find] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to find data in Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.find] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to find data in Pinecone: {e}")


    async def fetch(self, ids:list, namespace:str|list[str]|tuple[str]=None):
        try:
            index = await PineconeClientConnector.get_index(self.index_name)
            response = await asyncio.to_thread(index.fetch, ids=ids, namespace=self.namespace or namespace)
            return response
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.fetch] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to fetch data from Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.fetch] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to fetch data from Pinecone: {e}")


    async def update(self, ids:list[str], metadatas:list[dict], namespace:str=None):
        try:
            if namespace is None and isinstance(self.namespace, (list, tuple)):
                logging.info(f"check namespace. self.namespace: {type(self.namespace)}, namespace: {type(namespace)}")
                raise Exception("namespace should be str or None.")

            index = await PineconeClientConnector.get_index(self.index_name)
            for id, metadata in zip(ids, metadatas):
                await asyncio.to_thread(index.update, id=id, set_metadata=metadata, namespace=self.namespace or namespace)

        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.update] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to update data in Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.update] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to update data in Pinecone: {e}")


    async def remove(self, id:list|str=None, delete_all:bool=False, filter:dict=None):
        try:
            if isinstance(self.namespace, (list, tuple)):
                logging.info(f"check namespace. self.namespace: {type(self.namespace)}")
                raise Exception("namespace should be str or None.")

            index = await PineconeClientConnector.get_index(self.index_name)
            if id:
                await asyncio.to_thread(index.delete, ids=id, namespace=self.namespace or None)
            elif id is None and filter is not None:
                await asyncio.to_thread(index.delete, filter=filter, namespace=self.namespace or None)
            else:
                raise VectorDBError("Failed to remove data from Pinecone: id or filter is required")
        except VectorDBError as e:
            logging.error(f"[client.pinecone.PineconeClient.remove] 🔴 VectorDBError: {e}")
            raise VectorDBError(f"Failed to remove data from Pinecone: {e}")
        except Exception as e:
            logging.error(f"[client.pinecone.PineconeClient.remove] 🔴 Exception: {e}")
            raise VectorDBError(f"Failed to remove data from Pinecone: {e}")