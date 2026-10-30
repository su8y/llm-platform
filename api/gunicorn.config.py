import multiprocessing

# Project-specific settings
project = "llm-platform-api"

base = "/home/app"
virtualenv = f"{base}/.virtualenv/llm-platform-python311"
chdir = f"{base}"
module = "main:app"

# Socket and log settings
bind = "0.0.0.0:8888"
logfile = f"{base}/llm-platform-gunicorn.log"
access_log_format = '%(h)s|%(l)s|%(u)s|%(r)s|%(s)s|%(b)s'
errorlog = logfile
capture_output = True

# Server settings
workers = 2
threads = 4
worker_class = "uvicorn.workers.UvicornWorker"
preload_app = False
chdir = chdir
umask = 0o000  # Matches `chmod-socket = 666`

# timeout
timeout = 300
keepalive = 180
graceful_timeout = 180

# Limit request for memory
max_requests = 300
max_requests_jitter = 100