import os
import asyncio
import logging

from redis.asyncio import Redis

from utils.error import MemoryDBError



class RedisClient:
	_redis = None
	_lock = asyncio.Lock()

	@classmethod
	async def connect(cls):
		async with cls._lock:
			if cls._redis is None:
				try:
					cls._redis = await Redis(
						host=os.getenv("MEMORY_DB_HOST"),
						port=os.getenv("MEMORY_DB_PORT"),
						db=os.getenv("MEMORY_DB_NUMBER"),
						decode_responses=True
					)
					logging.info(f"✅ connected Redis: {os.getenv('MEMORY_DB_HOST')}:{os.getenv('MEMORY_DB_PORT')}")
				except Exception as e:
					logging.info(f"[client.redis.RedisClient.connect] 🔴 Failed to connect Redis: {e}")
					raise MemoryDBError(f"Failed to connect Redis: {e}")
	
	@classmethod
	async def disconnect(cls):
		async with cls._lock:
			if cls._redis:
				try:
					await cls._redis.close()
					cls._redis = None
					logging.info(f"🔴 disconnected Redis: {os.getenv('MEMORY_DB_HOST')}:{os.getenv('MEMORY_DB_PORT')}")
				except Exception as e:
					logging.info(f"[client.redis.RedisClient.disconnect] 🔴 Failed to disconnect Redis: {e}")
					raise MemoryDBError(f"Failed to disconnect Redis: {e}")
	
	@classmethod
	async def check_connection(cls):
		try:
			if cls._redis is None:
				await cls.connect()
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.check_connection] 🔴 Failed to check connection: {e}")
			raise MemoryDBError(f"Failed to check connection: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.check_connection] 🔴 Failed to check connection: {e}")
			raise MemoryDBError(f"Failed to check connection: {e}")

	@classmethod
	async def set(cls, key: str, value: str):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				await conn.set(key, value)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.set] 🔴 Failed to set data in Redis: {e}")
			raise MemoryDBError(f"Failed to set data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.set] 🔴 Failed to set data in Redis: {e}")
			raise MemoryDBError(f"Failed to set data in Redis: {e}")

	@classmethod
	async def rpush(cls, key: str, value: str):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				await conn.rpush(key, value)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.rpush] 🔴 Failed to push data into Redis: {e}")
			raise MemoryDBError(f"Failed to push data into Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.rpush] 🔴 Failed to push data into Redis: {e}")
			raise MemoryDBError(f"Failed to push data into Redis: {e}")

	@classmethod
	async def set_with_expire(cls, key: str, value: str, expire: int):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				await conn.set(key, value, ex=expire)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.set_with_expire] 🔴 Failed to set data in Redis: {e}")
			raise MemoryDBError(f"Failed to set data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.set_with_expire] 🔴 Failed to set data in Redis: {e}")
			raise MemoryDBError(f"Failed to set data in Redis: {e}")
	
	@classmethod
	async def expire(cls, key:str, time: int):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				await conn.expire(key, time)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.expire] 🔴 Failed to set data in Redis: {e}")
			raise MemoryDBError(f"Failed to set data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.expire] 🔴 Failed to set data in Redis: {e}")
			raise MemoryDBError(f"Failed to set data in Redis: {e}")
	
	@classmethod
	async def get(cls, key: str):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				return await conn.get(key)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.get] 🔴 Failed to get data in Redis: {e}")
			raise MemoryDBError(f"Failed to get data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.get] 🔴 Failed to get data in Redis: {e}")
			raise MemoryDBError(f"Failed to get data in Redis: {e}")
	

	@classmethod
	async def exists(cls, keys: list[str] | list[int]):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				return await conn.exists(*keys)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.exists] 🔴 Failed to check data in Redis: {e}")
			raise MemoryDBError(f"Failed to check data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.exists] 🔴 Failed to check data in Redis: {e}")
			raise MemoryDBError(f"Failed to check data in Redis: {e}")

	@classmethod
	async def keys(cls):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				return await conn.keys()
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.keys] 🔴 Failed to get data in Redis: {e}")
			raise MemoryDBError(f"Failed to get data in Redis: {e}")


	@classmethod
	async def lrange(cls, key: str, start: int= 0, end: int= -1):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				return await conn.lrange(key, start, end)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.lrange] 🔴 Failed to get data in Redis: {e}")
			raise MemoryDBError(f"Failed to get data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.lrange] 🔴 Failed to get data in Redis: {e}")
			raise MemoryDBError(f"Failed to get data in Redis: {e}")
	
	@classmethod
	async def llen(cls, key: str):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				return await conn.llen(key)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.llen] 🔴 Failed to get data in Redis: {e}")
			raise MemoryDBError(f"Failed to get data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.llen] 🔴 Failed to get data in Redis: {e}")
			raise MemoryDBError(f"Failed to get data in Redis: {e}")
	
	@classmethod
	async def delete(cls, key: str):
		try:
			await cls.check_connection()
			async with cls._redis.client() as conn:
				await conn.delete(key)
		except MemoryDBError as e:
			logging.info(f"[client.redis.RedisClient.delete] 🔴 Failed to delete data in Redis: {e}")
			raise MemoryDBError(f"Failed to delete data in Redis: {e}")
		except Exception as e:
			logging.info(f"[client.redis.RedisClient.delete] 🔴 Failed to delete data in Redis: {e}")
			raise MemoryDBError(f"Failed to delete data in Redis: {e}")