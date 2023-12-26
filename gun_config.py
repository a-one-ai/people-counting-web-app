# gunicorn_config.py

# Server socket
bind = '0.0.0.0:8000'  # Bind to a port
#backlog = 2048  # The maximum number of pending connections

# Worker processes
workers = 1  # Number of worker processes
worker_class = 'tornado'  # The type of workers to use
threads = 2
worker_connections = 10000  # For eventlet or gevent worker classes
#timeout = 120  # Workers silent for more than this many seconds are killed and restarted
keepalive = 2  # The number of seconds to wait for requests on a Keep-Alive connection

# Security
#limit_request_line = 4094  # The maximum size of HTTP request line in bytes
#limit_request_fields = 20  # Limit the number of HTTP headers fields in a request

# Server mechanics
preload_app = True  # Load application code before the worker processes are forked
#reload = True  # Restart workers when code changes (useful during development)
daemon = False  # If True, Gunicorn will run in the background

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'  # Log to stderr
loglevel = 'info'  # The granularity of error log outputs

# Process naming
proc_name = 'app.py'
