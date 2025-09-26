# Gunicorn Configuration for Quiz Partner
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5001')}"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "quiz_partner"

# Server mechanics
daemon = False
pidfile = "/tmp/quiz_partner.pid"
tmp_upload_dir = None

# SSL (uncomment for HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Application preloading
preload_app = True

# Worker timeout for graceful shutdown
graceful_timeout = 30

def when_ready(server):
    server.log.info("🎯 Quiz Partner server is ready. Listening on %s", server.address)

def worker_int(worker):
    worker.log.info("🔄 Worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("👷 Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("✅ Worker ready (pid: %s)", worker.pid)