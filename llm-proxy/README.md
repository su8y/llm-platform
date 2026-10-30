# LLM Proxy
- LLM Proxy Server
- Like Langchain, make easy to switch LLM Model, handle Error, etc.
- Build LLM API Client per Company such as OpenAI, Anthropic, Google, etc.


###  1. Language Version
- Python 3.14
- Gunicorn + Uvicorn


### 2. env setting
```text
JWT_SECRET_KEY=""
OPENAI_API_KEY=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_BASE_URL=""
AZURE_OPENAI_API_VERSION=""
```

### 3. make gunicorn config script
```python
import multiprocessing

project = "proxy-api"
base = 
virtualenv = 
chdir = f"{base}"
module = "main:app"

# Socket and log settings
# bind = f"unix:/tmp/{project}.sock"
bind = "0.0.0.0:9999"
logfile = f"{base}/llm-proxy-api-gunicorn.log"
access_log_format = '%(h)s|%(l)s|%(u)s|%(r)s|%(s)s|%(b)s'
errorlog = logfile
capture_output = True

# Server settings
workers = 
threads = 
worker_class = "uvicorn.workers.UvicornWorker"
preload_app = False
chdir = chdir
umask = 0o000

# timeout
timeout = 
keepalive = 
graceful_timeout = 


# Limit request for memory
max_requests = 
max_requests_jitter = 
```


### 3. How to Start

#### 1. Clone the repository
```bash
git clone <repository-url>
```

#### 2. Install the dependencies
```bash
pip install -r requirements.txt
```


### 4. Start the server
    
-  3-1. Start the server with Uvicorn
```bash
python main.py
```
- 3-2. Start the server with Gunicorn + Uvicorn
    - please check gunicorn.config.py if you want run with gunicorn
```bash
gunicorn -c gunicorn.config.py main:app
```


### 5. Process Flow
```text
Request: Client -> API -> **LLM Proxy** -> Vendor API
Response: Vendor API -> **LLM Proxy** -> API -> Client
```

- Issue: All Response is Streaming, and chunk data must be passed through Generator pipeline without delay.
- Issue Example:
    ```text
    if LLM model send "Hello" on Streaming, Process Flow is like this:
        1. Vendor API -> "H" -> LLM Proxy -> "H" -> API -> "H" -> Client -> "H" -> User
        2. Vendor API -> "e" -> LLM Proxy -> "e" -> API -> "e" -> Client -> "e" -> User
        3. Vendor API -> "l" -> LLM Proxy -> "l" -> API -> "l" -> Client -> "l" -> User
        4. Vendor API -> "l" -> LLM Proxy -> "l" -> API -> "l" -> Client -> "l" -> User
        5. Vendor API -> "o" -> LLM Proxy -> "o" -> API -> "o" -> Client -> "o" -> User
    ```