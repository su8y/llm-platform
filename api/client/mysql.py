import os
import logging
import asyncio
from dataclasses import dataclass

import asyncmy
from contextlib import asynccontextmanager
from utils.error import DBError



@dataclass
class MySQLClient:
    _pool = None
    _lock = asyncio.Lock()

    @classmethod
    async def connect(cls, host:str=None, port:int=None, user:str=None, password:str=None, db:str=None):
        host = host or os.getenv("DB_HOST")
        port = port or os.getenv("DB_PORT")
        user = user or os.getenv("DB_USERNAME")
        password = password or os.getenv("DB_PASSWORD")
        db = db or os.getenv("DB_DATABASE")
        
        async with cls._lock:
            if cls._pool is None:
                try:
                    cls._pool = await asyncmy.create_pool(
                        host=host,
                        port=int(port),
                        user=user,
                        password=password,
                        db=db,
                        minsize=10,
                        maxsize=30,
                        pool_recycle=9
                    )
                    logging.info(f"✅ Connected to MySQL: {db}@{host}:{port}")
                except Exception as e:
                    logging.error(f"[BaseMySQLClient.connect] 🔴 Failed to connect MySQL: {e}")
                    raise DBError(f"Failed to connect MySQL: {e}")

    @classmethod
    async def disconnect(cls):
        async with cls._lock:
            if cls._pool:
                cls._pool.close()
                await cls._pool.wait_closed()
                cls._pool = None
                logging.info("🔴 MySQL connection closed")

    @classmethod
    async def _acquire_connection(cls):
        if cls._pool is None:
            raise DBError("MySQL pool is not initialized")

        max_retries = 3
        retry_count = 0

        for try_count in range(max_retries):
            conn = await cls._pool.acquire()
            try:
                await conn.ping()
                return conn
            except Exception as e:
                logging.info(f"[MySQLClient] 🔁 retry_count is {retry_count+1}. Error Message is {e}")
                try:
                    conn.close()
                    await conn.ensure_closed()
                except Exception as e:
                    logging.error(f"[MySQLClient] Can not release connection. Error Message is {e}")
            retry_count += 1
            await asyncio.sleep(0.1 * (try_count + 1))

        logging.error(f"[MySQLClient._acquire_connection] 🔴 Failed to acquire and validate MySQL connection")
        raise DBError(f"Failed to acquire and validate MySQL connection")

    @classmethod
    @asynccontextmanager
    async def _get_connection(cls):
        conn = None
        try:
            conn = await cls._acquire_connection()
            yield conn
        except DBError as e:
            logging.error(f"[MySQLClient._get_connection] 🔴 Failed to get or use MySQL connection: {e}")
            raise DBError(f"Failed to get or use MySQL connection: {e}")
        except Exception as e:
            logging.error(f"[MySQLClient._get_connection] 🔴 Failed to get or use MySQL connection: {e}")
            raise DBError(f"Failed to get or use MySQL connection: {e}")
        finally:
            logging.info(f"[MySQLClient._get_connection] 🔴 Try to Release connection")
            await conn.ensure_closed()
            await cls._pool.release(conn)
            logging.info(f"[MySQLClient._get_connection] ✅ Success to Release connection")

    @classmethod
    @asynccontextmanager
    async def transaction(cls):
        async with cls._get_connection() as conn:
            try:
                await conn.begin()
                yield conn
                await conn.commit()
            except DBError as e:
                await conn.rollback()
                logging.error(f"[MySQLClient.transaction] 🔴 Transaction failed: {e}")
                raise DBError("Transaction failed")
            except Exception as e:
                await conn.rollback()
                logging.error(f"[MySQLClient.transaction] 🔴 Transaction failed: {e}")
                raise DBError("Transaction failed")

    @classmethod
    async def execute(cls, query: str, params: list|tuple = None):
        try:
            async with cls._get_connection() as conn:
                async with conn.cursor() as cur:
                    if params:
                        await cur.execute(query, params)
                    else:
                        await cur.execute(query)
                    await conn.commit()
                    return cur.lastrowid
        except Exception as e:
            await conn.rollback()
            logging.error(f"[MySQLClient.execute] 🔴 Failed to execute query: {e}")
            raise DBError(f"Failed to execute query: {e}")
    
    @classmethod
    async def execute_many(cls, query: str, params_list: list):
        try:
            async with cls._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.executemany(query, params_list)
                    await conn.commit()
                    return cur.rowcount
        except Exception as e:
            await conn.rollback()
            logging.error(f"[MySQLClient.execute_many] 🔴 Failed to execute many: {e}")
            raise DBError(f"Failed to execute many: {e}")

    @classmethod
    async def fetch_one(cls, query: str, params: list|tuple = None):
        try:
            async with cls._get_connection() as conn:
                async with conn.cursor() as cur:
                    if params:
                        await cur.execute(query, params)
                    else:
                        await cur.execute(query)
                    return await cur.fetchone()
        except Exception as e:
            logging.error(f"[MySQLClient.fetch_one] 🔴 Failed to fetch one: {e}")
            raise DBError(f"Failed to fetch one: {e}")

    @classmethod
    async def fetch_all(cls, query: str, params: list|tuple = None):
        try:
            async with cls._get_connection() as conn:
                async with conn.cursor() as cur:
                    if params:
                        await cur.execute(query, params)
                    else:
                        await cur.execute(query)
                    return await cur.fetchall()
        except Exception as e:
            logging.error(f"[MySQLClient.fetch_all] 🔴 Failed to fetch all: {e}")
            raise DBError(f"Failed to fetch all: {e}")