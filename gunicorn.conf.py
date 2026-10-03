import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("WEB_WORKERS", "2"))
threads = 4
worker_class = "gthread"
timeout = 30
graceful_timeout = 30
keepalive = 5
max_requests = 2000
max_requests_jitter = 200
accesslog = "-"
errorlog = "-"
# Rate limiting uses the peer address. No user-supplied proxy headers are trusted.
forwarded_allow_ips = ""
worker_tmp_dir = "/tmp"
control_socket_disable = True
