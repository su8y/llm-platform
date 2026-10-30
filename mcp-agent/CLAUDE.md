# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server project that implements a RAG (Retrieval-Augmented Generation) system using Pinecone vector database. The project provides tools for vector-based knowledge search and AI-powered answer generation.

## Key Architecture

- **Main Server**: `server.py` - FastMCP-based server with basic tools (add function, greeting resource)
- **Dependencies**: Uses MCP framework with Pinecone and OpenAI integrations
- **Project Structure**: Simple MCP server with tool and resource decorators

## Development Commands

- **Install dependencies**: `uv sync` (uses uv.lock and pyproject.toml)
- **Run server**: `python server.py`
- **Development mode**: The server includes a basic add tool and greeting resource for testing

## Configuration

- Python 3.10+ required (as specified in pyproject.toml)
- MCP CLI dependency with version >=1.6.0
- Uses FastMCP framework for simplified MCP server creation

## MCP Server Pattern

The codebase follows the FastMCP pattern:
- Use `@mcp.tool()` decorator for tool functions
- Use `@mcp.resource()` decorator for dynamic resources
- Server runs with `mcp.run()` in main block