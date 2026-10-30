#!/usr/bin/env python3
"""
LLM Proxy Server with MCP Tool Integration
Supports OpenAI GPT and Claude APIs with MCP server tool calling
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
from anthropic import Anthropic
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Proxy with MCP Tools", description="Chat with LLMs that can use MCP server tools")

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8002/mcp/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MCP_TOKEN = os.getenv("MCP_SERVER_TOKEN", "")
# Initialize clients
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "claude-4-sonnet"  # or "claude-4-sonnet"
    max_tokens: int = 2000
    temperature: float = 0.7


class ChatResponse(BaseModel):
    response: str
    model_used: str
    tools_called: List[str] = []


async def chat_with_openai(messages: List[Dict], tools_called: List[str]) -> str:
    """Chat with OpenAI GPT with tool calling support"""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        # Convert messages to OpenAI format
        message = "".join([msg["content"] for msg in messages])
        system_message = "당신은 LLM Platform 이라는 고객문의 관리 AI Assistant입니다. 제공한 mcp 도구를 가능한 활용해 고객 혹은 관리자가 필요한 내용을 찾아 답변해주세요. 번거롭거나 오래걸리더라도 필요하다면 반복해서 tool을 사용하고 내용이 너무 크다면 tool을 작은 단위로 반복해서 사용해도 좋습니다."
        response = openai_client.responses.create(
            model="gpt-5",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "llm_platform_agent_server",
                    "server_url": MCP_SERVER_URL,
                    "require_approval": "never",
                    "allowed_tools": ["get_current_time", "query_customer_emails", "get_email_statistics"],
                    "headers": {
                        "Authorization": f"Bearer {MCP_TOKEN}"
                    }
                },
            ],
            instructions=system_message,
            input=message,
        )

        return response.output_text

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")


async def chat_with_claude(messages: List[Dict], tools_called: List[str]):
    """Chat with Claude with tool calling support"""
    if not anthropic_client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    try:

        # Convert messages to Claude format (system message separate)
        claude_messages = []
        system_message = "당신은 LLM Platform 이라는 고객문의 관리 AI Assistant입니다. 제공한 mcp 도구를 가능한 활용해 고객 혹은 관리자가 필요한 내용을 찾아 답변해주세요. 번거롭거나 오래걸리더라도 필요하다면 반복해서 tool을 사용하고 내용이 너무 크다면 tool을 작은 단위로 반복해서 사용해도 좋습니다."

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({"role": msg["role"], "content": msg["content"]})

        # Initial request with tools
        response = anthropic_client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_message,
            messages=claude_messages,
            mcp_servers=[
                {
                    "type": "url",
                    "url": MCP_SERVER_URL,
                    "name": "llm_platform_agent_server",

                    "tool_configuration": {
                        "enabled": True,
                        "allowed_tools": ["get_current_time", "query_customer_emails", "get_email_statistics"]
                    },
                    "authorization_token": MCP_TOKEN
                }
            ],
            extra_headers={
                "anthropic-beta": "mcp-client-2025-04-04"
            }
        )
        # Handle tool use
        for block in response.content:
            if block.type == 'mcp_tool_use':
                claude_messages.append({
                    "role": "mcp_tool_use",
                    "content": {
                        "name": block.name,
                        "input": block.input,
                    }
                })
            elif block.type == 'mcp_tool_result':
                block_result = []
                for sub_block in block.content:
                    block_result.append(sub_block.text)
                claude_messages.append({
                    "role": "mcp_tool_result",
                    "content": block_result
                })
            else:
                claude_messages.append({
                    "role": "assistant",
                    "content": block.text
                })

        return claude_messages

    except Exception as e:
        logger.error(f"Claude API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint that supports both OpenAI and Claude with MCP tool integration"""
    tools_called = []

    try:
        # Convert Pydantic models to dict
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        if request.model.startswith("gpt") or request.model.startswith("openai"):
            response_text = await chat_with_openai(messages, tools_called)
            model_used = "openai-gpt-5"
        elif request.model.startswith("claude"):
            response_text = await chat_with_claude(messages, tools_called)
            model_used = "claude-4-sonnet"
        else:
            raise HTTPException(status_code=400, detail="Unsupported model. Use 'gpt-5' or 'claude-4-sonnet'")

        return JSONResponse(content=response_text)
        # return ChatResponse(
        #     response=response_text,
        #     model_used=model_used,
        #     tools_called=tools_called
        # )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Simple test page"""
    return {
        "message": "LLM Proxy Server with MCP Tools",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "tools": "/tools"
        },
        "supported_models": ["gpt-5","openai/gpt-oss-20b", "claude-4-sonnet"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mcp_server": MCP_SERVER_URL,
        "openai_configured": OPENAI_API_KEY is not None,
        "claude_configured": ANTHROPIC_API_KEY is not None
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
