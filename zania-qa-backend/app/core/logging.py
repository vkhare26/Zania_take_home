import logging
from logging.handlers import RotatingFileHandler
import os, sys

def setup_logging():
    """
    Configure a rotating logger for the Zania backend.
    Logs go both to the console and a file (logs/zania_backend.log).
    """

    logger = logging.getLogger("zania")

    # Avoid re-adding handlers if setup_logging() is called multiple times
    if logger.handlers:
        return logger

    # Default to INFO level; can be overridden via env if needed
    logger.setLevel(logging.INFO)

    # Consistent timestamped log format
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    # Log to stdout for container visibility (Docker logs, etc.)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Ensure local log directory exists for file output
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Use a rotating file handler to prevent giant log files
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "zania_backend.log"),
        maxBytes=5_000_000,  # ~5 MB per file
        backupCount=3        # Keep up to 3 old logs
    )
    file_handler.setFormatter(formatter)

    # Attach both console and file outputs
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    for name in ["httpx", "urllib3", "faiss", "langchain", "openai"]:
        logging.getLogger(name).setLevel(logging.WARNING)

    return logger
