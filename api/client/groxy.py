import os
import logging
import json
import base64
from dataclasses import dataclass
from uuid import uuid4

import httpx
import numpy as np
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from utils.error import AppError, LLMProxyError, LLMStreamingError
from utils.constants import EMBEDDING_MODEL, BASE_VENDOR, BASE_MODEL, BASE_MCP_VENDOR, BASE_MCP_MODEL


@dataclass
class LLMProxyClient:
    _base_url = None
    _clients = {
        "stream": None,
        "embedding": None,
        "function_calling": None,
        "file_search": None
    }
    _config = {
        "stream": {
            "limits": httpx.Limits(
                max_connections=50,
                max_keepalive_connections=15,
                keepalive_expiry=30.0
            ),
            "timeout": httpx.Timeout(
                connect=10.0,
                read=300.0,
                write=10.0,
                pool=5.0
            ),
            "semaphore": asyncio.Semaphore(30)
        },

        "embedding": {
            "limits": httpx.Limits(
                max_connections=50,
                max_keepalive_connections=15,
                keepalive_expiry=30.0
            ),
            "timeout": httpx.Timeout(
                connect=5.0,
                read=120.0,
                write=10.0,
                pool=5.0
            ),
            "semaphore": asyncio.Semaphore(10)
        },

        "function_calling": {
            "limits": httpx.Limits(
                max_connections=15,
                max_keepalive_connections=5,
                keepalive_expiry=30.0
            ),
            "timeout": httpx.Timeout(
                connect=5.0,
                read=60.0,
                write=5.0,
                pool=5.0
            ),
            "semaphore": asyncio.Semaphore(10)
        },

        "file_search": {
            "limits": httpx.Limits(
                max_connections=15,
                max_keepalive_connections=5,
                keepalive_expiry=30.0
            ),
            "timeout": httpx.Timeout(
                connect=5.0,
                read=60.0,
                write=5.0,
                pool=5.0
            ),
            "semaphore": asyncio.Semaphore(10)
        }

    }
    _default_headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }
    _lock = asyncio.Lock()


    @classmethod
    async def connect(cls) -> None:
        async with cls._lock:
            cls._base_url = os.getenv("LLM_PROXY_URL", "http://llm-proxy:9999/").rstrip("/") + "/"
            for name, config in cls._config.items():
                if cls._clients[name] is None or cls._clients[name].is_closed:
                    cls._clients[name] = httpx.AsyncClient(
                        limits=config["limits"], timeout=config["timeout"], headers=cls._default_headers,
                    )

    @classmethod
    async def disconnect(cls) -> None:
        async with cls._lock:
            clients = [client for client in cls._clients.values() if client is not None]
            try:
                await asyncio.gather(*(client.aclose() for client in clients))
            finally:
                cls._clients = dict.fromkeys(cls._clients)
                cls._base_url = None


    @classmethod
    async def _ensure_client(cls, type: str):
        """클라이언트가 없거나 닫혔으면 새로 생성"""
        if cls._clients[type] is None or cls._clients[type].is_closed:
            async with cls._lock:
                if cls._clients[type] is None or cls._clients[type].is_closed:
                    cls._clients[type] = httpx.AsyncClient(limits=cls._config[type]["limits"], timeout=cls._config[type]["timeout"], headers=cls._default_headers)


    @classmethod
    async def _close_client(cls, _type: str) -> None:
        async with cls._lock:
            if cls._clients[_type] is not None:
                await cls._clients[_type].aclose()
                cls._clients[_type] = None


    @classmethod
    @asynccontextmanager
    async def _get_client(cls, _type: str) -> AsyncIterator[httpx.AsyncClient]:
        await cls._ensure_client(_type)
        yield cls._clients[_type]

    @classmethod
    async def _embedding_request(cls, payload: dict) -> httpx.Response:
        """Retry this read-only operation once; a context manager cannot replay its body."""
        try:
            async with cls._get_client("embedding") as client:
                return await client.post(url=cls._base_url + "llm/embeddings", json=payload)
        except (httpx.ConnectError, httpx.RemoteProtocolError):
            await cls._close_client("embedding")
        async with cls._get_client("embedding") as client:
            return await client.post(url=cls._base_url + "llm/embeddings", json=payload)


    @classmethod
    async def stream(
        cls,
        service: str,
        vendor: str,
        model: str,
        system_message: str = None,
        system_message_placeholder: dict = None,
        conversation_history: list = None,
        human_message: str or None = None,
        temperature: float = None,
        callback: object = None,
        callback_args: object = None,
        time:float = None,
        mcp_token: str = None,
        store_name: str | None = None,
        session_key: str = None,
        **kwargs
    ):
        try:
            payload = {
                "service": service or "llm-platform-staging",
                "vendor": vendor or BASE_VENDOR,
                "model": model or BASE_MODEL,
                "question": human_message or "",
                "systemMessage": system_message or "",
                "systemMessagePlaceholder": system_message_placeholder or {},
                "conversationHistory": conversation_history or [],
                "temperature": temperature or 0.2,
            }
            if time:
                payload["time"] = time
            if mcp_token:
                payload["mcpToken"] = mcp_token
            if store_name:
                payload["storeName"] = store_name
            if session_key:
                payload["sessionKey"] = session_key

            await cls._ensure_client("stream")
            async with cls._config["stream"]["semaphore"]:
                async with cls._get_client("stream") as client:
                    async with client.stream(method="POST", url=cls._base_url+"llm/chat", headers=cls._default_headers, json=payload) as response:
                        response.raise_for_status()
                        current_use_model = None
                        full_dict = str()
                        full_response = str()
                        async for chunk in response.aiter_lines():
                            if chunk:
                                full_dict += chunk
                                if chunk[-1] == "}":
                                    try:
                                        if not full_dict.strip():
                                            full_dict = ""
                                            continue

                                        response_object = json.loads(full_dict)
                                        yield response_object

                                        # gathering data for callback.
                                        full_dict = ""
                                        text = response_object.get("text")
                                        model = response_object.get("model")
                                        if text:
                                            full_response += text
                                        if model and not current_use_model:
                                            current_use_model = model

                                    except json.JSONDecodeError:
                                        continue

                if callback:
                    if hasattr(callback_args, "message"):
                        callback_args.message = full_response
                    if hasattr(callback_args, "chat_info") and isinstance(callback_args.chat_info, dict):
                        callback_args.chat_info["model"] = current_use_model
                    await callback(callback_args)

        except Exception as e:
            logging.error(f"[client.llm_proxy.LLMProxyClient.stream] 🔴 Failed to send request to Proxy Server: {e}")
            raise LLMStreamingError(f"Failed to send request to Proxy Server: {e}")


    @classmethod
    async def stream_with_mcp(
        cls,
        mcp_server: str,
        mcp_token: str,
        mcp_allowed_tools: list | None,
        service: str,
        vendor: str,
        model: str,
        system_message: str = None,
        system_message_placeholder: dict = None,
        conversation_history: list = None,
        human_message: str | None = None,
        temperature: float = None,
        callback: object = None,
        callback_args: object = None,
        time:float = None,
        store_name: str | None = None,
        session_key: str = None
    ):
        try:
            payload = {
                "mcpServer": mcp_server,
                "mcpToken": mcp_token,
                "mcpAllowedTools": mcp_allowed_tools,
                "service": service or "llm-platform-staging",
                "vendor": vendor or BASE_MCP_VENDOR,
                "model": model or BASE_MCP_MODEL,
                "systemMessage": system_message or '', # 필수값
                "systemMessagePlaceholder": system_message_placeholder or {},
                "conversationHistory": conversation_history or [],
                "question": human_message or '', # 필수값
                "temperature": temperature or 0.2,
            }
            if time:
                payload["time"] = time
            if store_name:
                payload["storeName"] = store_name
            if session_key:
                payload["sessionKey"] = session_key

            await cls._ensure_client("stream")
            async with cls._config["stream"]["semaphore"]:
                async with cls._get_client("stream") as client:
                    async with client.stream(method="POST", url=cls._base_url+"llm/chat_mcp", headers=cls._default_headers, json=payload) as response:
                        response.raise_for_status()
                        full_response = str()
                        current_use_model = None
                        full_mcp_tools = list()
                        full_dict = str()
                        async for chunk in response.aiter_lines():
                            if chunk:
                                full_dict += chunk
                                if chunk[-1] == "}":
                                    try:
                                        response_object = json.loads(full_dict)
                                        yield response_object
                                        full_dict = ""
                                        text = response_object.get("text")
                                        model = response_object.get("model")
                                        mcp_tools = response_object.get("tool_name")
                                        if text:
                                            full_response += text
                                        if model and not current_use_model:
                                            current_use_model = model
                                        if mcp_tools:
                                            full_mcp_tools.append({mcp_tools: response_object.get("tool_text")})
                                    except json.JSONDecodeError:
                                        continue
                if callback:
                    if hasattr(callback_args, "message"):
                        callback_args.message = full_response
                    if hasattr(callback_args, "chat_info") and isinstance(callback_args.chat_info, dict):
                        callback_args.chat_info["model"] = current_use_model
                        callback_args.chat_info["mcp_tools"] = full_mcp_tools
                    await callback(callback_args)

        except Exception as e:
            logging.error(f"[client.llm_proxy.LLMProxyClient.stream] 🔴 Failed to send request to Proxy Server: {e}")
            raise LLMStreamingError(f"Failed to send request to Proxy Server: {e}")


    @classmethod
    async def func(
        cls,
        service: str,
        vendor: str,
        model: str,
        system_message:str,
        tools: list,
        question: str
    ):
        try:
            payload = {
                "service": service or "llm-platform",
                "vendor": vendor or "openai",
                "model": model or "gpt-4o",
                "systemMessage": system_message, # 필수값
                "tools": tools,
                "question": question, # 필수값
            }
            await cls._ensure_client("function_calling")
            async with cls._config["function_calling"]["semaphore"]:
                async with cls._get_client("function_calling") as client:
                    response = await client.post(url=cls._base_url+"llm/function_calling", headers=cls._default_headers, json=payload)
                    response.raise_for_status()
                    return response.json()
        except Exception as e:
            logging.error(f"[client.llm_proxy.LLMProxyClient.func] 🔴 Failed to send request to Proxy Server: {e}")
            raise LLMProxyError(f"Failed to send request to Proxy Server: {e}")


    @classmethod
    async def embeddings(
        cls,
        text: str | list[str],
        service: str,
        session_key: str | None = None,
    ) -> list:

        try:
            payload = {
                "service": service,
                "model": EMBEDDING_MODEL,
                "text": text,
                "debugId": str(uuid4())[:8]
            }
            logging.info(f"session_key: {session_key} | [client.groxy.LLMProxyClient.embeddings] debugId: {payload['debugId']}")
            await cls._ensure_client("embedding")
            async with cls._config["embedding"]["semaphore"]:
                response = await cls._embedding_request(payload)
                response.raise_for_status()
                response_json = response.json()
                vectors = response_json.get("vectors")
                debug_id = response_json.get("debugId")
                logging.info(f"session_key: {session_key} | [client.groxy.LLMProxyClient.embeddings] debugId: {debug_id}")

                if isinstance(vectors, list):
                    result = []
                    for base64_vector in vectors:
                        decoded_vector = base64.b64decode(base64_vector)
                        vector = np.frombuffer(decoded_vector, dtype=np.float32)
                        result.append(vector.tolist())  # numpy array를 list로 변환
                else:
                    # 단일 값 처리: base64 문자열을 직접 디코딩
                    decoded_vector = base64.b64decode(vectors)
                    vector = np.frombuffer(decoded_vector, dtype=np.float32)
                    result = vector.tolist()  # numpy array를 list로 변환
                return result
        except AppError:
            raise
        except Exception as error:
            logging.error(f"session_key: {session_key} | [client.groxy.LLMProxyClient.embeddings] 🔴 Embedding request failed")
            raise LLMProxyError("Embedding request failed") from error


    # FileSearch API
    @classmethod
    async def create_store(
            cls,
            service: str,
            display_name: str = None
    ) -> dict:
        try:
            payload = {"service": service}
            if display_name:
                payload["displayName"] = display_name

            await cls._ensure_client("file_search")
            async with cls._config["file_search"]["semaphore"]:
                async with cls._get_client("file_search") as client:
                    response = await client.post(
                        url=cls._base_url+"file/create_store",
                        headers=cls._default_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    data = response_json.get("data")
                    # {"storeName": str(store_name)} -> company_info에 기록! 회사별로 다른 store 쓸 예정
                    return data

        except Exception as e:
            logging.error(
                f"[client.llm_proxy.LLMProxyClient.create_store] 🔴 Failed to send request to Proxy Server: {e}"
            )
            raise LLMProxyError(f"Failed to send request to Proxy Server: {e}")


    @classmethod
    async def get_stores(
            cls,
            service: str,
    ):

        """
        get all stores.
        this method is for admin
        """

        try:
            payload = {"service": service}

            await cls._ensure_client("file_search")
            async with cls._config["file_search"]["semaphore"]:
                async with cls._get_client("file_search") as client:
                    response = await client.post(
                        url=cls._base_url+"file/get_store",
                        headers=cls._default_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    data = response_json.get("data")
                    # {"stores": stores} -> stores는 list.
                    return data

        except Exception as e:
            logging.error(
                f"[client.llm_proxy.LLMProxyClient.get_stores] 🔴 Failed to send request to Proxy Server: {e}"
            )
            raise LLMProxyError(f"Failed to send request to Proxy Server: {e}")


    @classmethod
    async def import_files(
            cls,
            service: str,
            store_name: str,
            buckets: list[str],
            keys: list[str]
    ):

        try:
            payload = {
                "service": service,
                "storeName": store_name,
                "buckets": buckets,
                "keys": keys
            }

            await cls._ensure_client("file_search")
            async with cls._config["file_search"]["semaphore"]:
                async with cls._get_client("file_search") as client:
                    response = await client.post(
                        url=cls._base_url+"file/import_files",
                        headers=cls._default_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    data = response_json.get("data")
                    # data = {"documentName": document_names, "status": status} -> document_names: list[str], status: list[bool]
                    return data

        except Exception as e:
            logging.error(
                f"[client.llm_proxy.LLMProxyClient.import_files] 🔴 Failed to send request to Proxy Server: {e}"
            )
            raise LLMProxyError(f"Failed to send request to Proxy Server: {e}")



    @classmethod
    async def get_files(
            cls,
            service: str,
            store_name: str
    ):

        try:
            payload = {
                "service": service,
                "storeName": store_name
            }

            await cls._ensure_client("file_search")
            async with cls._config["file_search"]["semaphore"]:
                async with cls._get_client("file_search") as client:
                    response = await client.post(
                        url=cls._base_url+"file/get_files",
                        headers=cls._default_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    data = response_json.get("data")
                    # {"documentNames": document_names} -> document_names: list[str]
                    return data

        except Exception as e:
            logging.error(
                f"[client.llm_proxy.LLMProxyClient.get_files] 🔴 Failed to send request to Proxy Server: {e}"
            )
            raise LLMProxyError(f"Failed to send request to Proxy Server: {e}")


    @classmethod
    async def delete_store(
            cls,
            service: str,
            store_name: str
    ):

        try:
            payload = {
                "service": service,
                "storeName": store_name
            }

            await cls._ensure_client("file_search")
            async with cls._config["file_search"]["semaphore"]:
                async with cls._get_client("file_search") as client:
                    response = await client.post(
                        url=cls._base_url+"file/delete_store",
                        headers=cls._default_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    data = response_json.get("data")
                    # {"documentNames": document_names} -> document_names: list[str]
                    return data

        except Exception as e:
            logging.error(
                f"[client.llm_proxy.LLMProxyClient.delete_store] 🔴 Failed to send request to Proxy Server: {e}"
            )
            raise LLMProxyError(f"Failed to send request to Proxy Server: {e}")


    @classmethod
    async def delete_document(
            cls,
            service: str,
            document_name: list | str
    ):
        try:
            payload = {
                "service": service,
                "documentName": document_name
            }

            await cls._ensure_client("file_search")
            async with cls._config["file_search"]["semaphore"]:
                async with cls._get_client("file_search") as client:
                    response = await client.post(
                        url=cls._base_url+"file/delete_document",
                        headers=cls._default_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    data = response_json.get("data")
                    # {"documentNames": document_names} -> document_names: list[str]
                    return data

        except Exception as e:
            logging.error(
                f"[client.llm_proxy.LLMProxyClient.delete_document] 🔴 Failed to send request to Proxy Server: {e}"
            )
            raise LLMProxyError(f"Failed to send request to Proxy Server: {e}")
