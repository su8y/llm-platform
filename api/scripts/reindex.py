"""Preview: python -m scripts.reindex --source old --target new --company key"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path


def read_texts(path: Path | None) -> dict[str, str]:
    from utils.error import DataError

    if path is None:
        return {}
    texts = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("content"), str):
                raise DataError("Each JSONL row needs string id and content fields")
            if item["id"] in texts:
                raise DataError("Duplicate chunk ID in text mapping")
            texts[item["id"]] = item["content"]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DataError("Cannot read chunk text mapping") from error
    return texts


async def run(args: argparse.Namespace) -> dict:
    from client.groxy import LLMProxyClient
    from client.milvus import MilvusClient, MilvusClientConnector
    from module.Retrieval.reindex import reindex

    texts = read_texts(args.texts)
    proxy_connected = False
    try:
        await MilvusClientConnector.connect()
        if args.write:
            await LLMProxyClient.connect()
            proxy_connected = True

        async def embed(text: str) -> list:
            return await LLMProxyClient.embeddings(text=text, service=args.service)

        result = await reindex(
            MilvusClient(args.source), MilvusClient(args.target), args.company,
            embed, texts=texts, write=args.write, batch_size=args.batch_size,
        )
        return asdict(result)
    finally:
        try:
            if proxy_connected:
                await LLMProxyClient.disconnect()
        finally:
            await MilvusClientConnector.disconnect()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reindex one company into a new BM25 collection")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--texts", type=Path, help="JSONL: id is the vector chunk ID; content is raw chunk text")
    parser.add_argument("--service", default="llm-platform-install")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--env", type=Path)
    parser.add_argument("--write", action="store_true", help="Write after preflight validation; default is preview only")
    args = parser.parse_args()
    if args.env is not None:
        from dotenv import load_dotenv
        load_dotenv(args.env, override=True)
    from utils.error import AppError
    try:
        print(json.dumps(asyncio.run(run(args))))
    except AppError:
        print("Reindex failed. The original collection remains active.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
