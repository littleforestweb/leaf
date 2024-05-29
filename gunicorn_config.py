import multiprocessing

"""
Configures Gunicorn server settings with default values and returns them as a dictionary.

"""
# Determine the number of worker processes to run, based on CPU count
workers = multiprocessing.cpu_count() * 2 + 1

# The maximum number of seconds to wait for a worker to handle a request
timeout = 50000  # Increase this to a higher value if needed

# The number of seconds to wait for a graceful worker restart
graceful_timeout = 50000

# Set the socket to bind the server to
bind = "unix:leaf.sock"

# Set the umask to use when creating new files, to ensure proper permissions
umask = 0o007

# Enable automatic code reloading when files are changed
reload = True

# Set the file paths for logging access and error messages
accesslog = "log_gunicorn_access.txt"
errorlog = "log_gunicorn_error.txt"
