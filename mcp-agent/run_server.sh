#!/bin/bash
# 환경변수(PINECONE_API_KEY, OPENAI_API_KEY, MYSQL_* 등)는 compose(env/mcp.yaml + env/secret.yaml) 또는
# pm2 ecosystem.config.js 의 env 로 주입한다. 이 파일에 값을 적지 않는다.
cd "$(dirname "$0")"
venv/bin/python server.py
