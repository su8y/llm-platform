import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from utils.constants import DOCKER, DEV
# infra side by server stage
if os.getenv("SERVER_STAGE", DEV) != DOCKER:
    from dotenv import load_dotenv
    # Load Environment Variables
    APP_ROOT = os.path.dirname(__file__)
    # if not os.getenv("DOCKER"):
    dotenv_path = os.path.join(APP_ROOT, '.env')
    load_dotenv(dotenv_path, override=True)
    # cloud infra side
    from client.aws import S3Client
    from client.pinecone import PineconeClientConnector
    from client.slack import SlackClient
else:
    # docker infra side
    from client.milvus import MilvusClientConnector

import logging

# common infra side
from client.groxy import LLMProxyClient
from client.mysql import MySQLClient
from client.redis import RedisClient
from client.rabbit import RabbitMQClient

# web framework
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

# cors - dynamic
from auth.middleware import DynamicCORSMiddleware

# route side
from api.admin import router as admin_router
from api.chatbot import router as chatbot_router
from api.company import router as company_router
from api.drive import router as drive_router
from api.monitoring import router as monitoring_router
from api.plan import router as plan_router
from api.playground import router as playground_router 
from api.prompt import router as prompt_router
from api.reference import router as reference_router
from api.user import router as user_router
from api.email import router as email_router
from api.emailrag import router as emailrag_router
from api.geo import router as geo_router

# inner side
from module.Language.detector import FastTextDetector
from module.MailReceiver.runner import MailReceiverRunner
from utils.error import handle_errors, token_exception_handler
from utils.response import Response200



# Logging Settings
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    from models import SessionLocal, engine, init_admin, init_db

    async with AsyncExitStack() as resources:
        resources.push_async_callback(engine.dispose)
        await init_db()
        if os.getenv("SERVER_STAGE", DEV) == DOCKER:
            async with SessionLocal() as db_session:
                await init_admin(db=db_session)

        clients = [
            (LLMProxyClient.connect, LLMProxyClient.disconnect),
            (MySQLClient.connect, MySQLClient.disconnect),
            (RedisClient.connect, RedisClient.disconnect),
            (RabbitMQClient.connect, RabbitMQClient.disconnect),
        ]
        if os.getenv("SERVER_STAGE", DEV) == DOCKER:
            clients.append((MilvusClientConnector.connect, MilvusClientConnector.disconnect))
        else:
            clients.extend([
                (S3Client.initialize, S3Client.close),
                (PineconeClientConnector.initialize, PineconeClientConnector.disconnect),
                (SlackClient.connect, SlackClient.disconnect),
            ])
        for connect, disconnect in clients:
            resources.push_async_callback(disconnect)
            await connect()
        await asyncio.to_thread(FastTextDetector.model_init)
        if os.getenv("SERVER_STAGE", DEV) == DOCKER and os.getenv("MAIL_RECEIVER_ENABLED", "true").lower() in ("1", "true", "yes", "on"):
            resources.push_async_callback(MailReceiverRunner.stop)
            await MailReceiverRunner.start()
        yield


# FastAPI App
app = FastAPI(
    lifespan=lifespan,
    title="LLM Platform API",
    version="1.0.0",
    description="LLM Platform API",
    root_path="/llm-platform-api",
    default_response_class=ORJSONResponse
)

app.add_middleware(DynamicCORSMiddleware)

# Register Router
app.include_router(admin_router)
app.include_router(chatbot_router)
app.include_router(company_router)
app.include_router(drive_router)
app.include_router(monitoring_router)
app.include_router(plan_router)
app.include_router(playground_router)
app.include_router(prompt_router)
app.include_router(reference_router)
app.include_router(user_router)
app.include_router(email_router)
app.include_router(emailrag_router)
app.include_router(geo_router)

token_exception_handler(app)

# Check Server Status
@app.get("/check")
@handle_errors()
async def check() -> dict:
    """Check Server Status"""
    return Response200(message=f"I AM LIVING. Server Stage is {os.getenv('SERVER_STAGE', DEV)}", data="").to_dict()

# Run API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", #app = app
        host="0.0.0.0",
        port=8888,
        timeout_keep_alive=180,
        limit_concurrency=1000,
        limit_max_requests=1000,
        loop="asyncio",
        http="h11",
        log_level="info",
        reload=True
    )
