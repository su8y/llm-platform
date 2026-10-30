FROM python:3.14-slim

ENV TZ=Asia/Seoul

RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo "$TZ" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /home/app

COPY requirements.lock .

# Install dependencies with uv
RUN uv pip install --system --require-hashes -r requirements.lock

COPY . .

EXPOSE 8002

CMD ["python3", "server.py"]
