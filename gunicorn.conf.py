import multiprocessing
import os

# Bind to the port provided by environment or default 5000
bind = f"0.0.0.0:{int(os.getenv('PORT', '5000'))}"

# Workers: 2-4 x CPU cores is a common rule of thumb; start conservative
workers = int(os.getenv("WEB_CONCURRENCY", max(2, multiprocessing.cpu_count())))
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "sync")

# Timeouts
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))

# Logging to stdout/stderr for Docker
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")

# Proxy handling (if running behind a reverse proxy)
forwarded_allow_ips = "*"
proxy_protocol = False
