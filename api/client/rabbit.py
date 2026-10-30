import os
import json
import logging
import asyncio
import socket

import aio_pika

from utils.error import MessageQueueError


class RabbitMQClient:
    connection = None
    channel = None
    
    @classmethod
    async def connect(cls):
        try:
            if os.getenv("AMQP_BASE_URL"): # for saas
                cls.connection = await aio_pika.connect(
                    os.getenv("AMQP_BASE_URL"),
                    connection_attempts=3,
                    retry_delay=1.0,
                    timeout=30.0
                )
            else: # for docker
                cls.connection = await aio_pika.connect_robust(
                    host=os.getenv("MESSAGE_QUEUE_HOST", "message-queue"),
                    port=int(os.getenv("MESSAGE_QUEUE_PORT", 5672)),
                    login=os.getenv("MESSAGE_QUEUE_USER", "admin"),
                    password=os.getenv("MESSAGE_QUEUE_PASS", "admin123"),
                    connection_attempts=3,
                    retry_delay=1.0,
                    timeout=30.0
                )
            cls.channel = await cls.connection.channel()
            logging.info("✅ connected RabbitMQ")
        except Exception as e:
            logging.error(f"[RabbitMQClient.connect] Exception: {e}")
            raise MessageQueueError

    @classmethod
    async def disconnect(cls):
        if cls.connection and not cls.connection.is_closed:
            await cls.connection.close()
            logging.info("🔴 disconnected RabbitMQ")

    @classmethod
    async def declare_queue(cls, queue_name):
        try:
            if not cls.channel:
                await cls.connect()
            return await cls.channel.declare_queue(queue=queue_name, durable=True)
        except Exception as e:
            logging.error(f"[RabbitMQClient.declare_queue] Exception: {e}")
            raise MessageQueueError

    @classmethod
    async def send_message(cls, queue_name, message: dict):
        if not cls.channel:
            await cls.connect()
            
        try:
            message_json = json.dumps(message)
            logging.info(f"✅ Sending message to {queue_name}: {message_json}")
            
            await cls.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_json.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=queue_name
            )
        except Exception as e:
            logging.error(f"[RabbitMQClient.send_message] Exception: {e}")
            raise MessageQueueError

    @classmethod
    async def consume_message(cls, queue_name, callback):
        if not cls.channel:
            await cls.connect()
            
        try:
            queue = await cls.declare_queue(queue_name)
            logging.info(f"✅ Starting to consume messages from {queue_name}")
            
            async def internal_callback(message):
                async with message.process():
                    try:
                        # 메시지 바디를 디코딩하고 JSON으로 파싱
                        body = message.body.decode()
                        data = json.loads(body)
                        # 사용자 제공 콜백 함수 호출
                        await callback(data)
                    except json.JSONDecodeError:
                        logging.error("🔴 JSON parsing error")
                    except Exception as e:
                        logging.error(f"🔴 Callback processing error: {e}")
            
            await queue.consume(internal_callback)
            
        except Exception as e:
            logging.error(f"[RabbitMQClient.consume_message] Exception: {e}")
            raise MessageQueueError
    
    # 예시 콜백 함수
    @staticmethod
    async def callback(data):
        try:
            logging.info(f"✅ Received message: {data}")
            # 여기에 메시지 처리 로직 추가
        except Exception as e:
            logging.error(f"[RabbitMQClient.callback] Exception: {e}")
            raise MessageQueueError