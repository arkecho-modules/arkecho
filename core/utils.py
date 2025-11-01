# core/utils.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
import os
import time
import logging
import hashlib

def timer(fn, *args, **kwargs):
    """
    Measure execution time of function fn.
    Returns (result, elapsed_seconds).
    """
    start = time.time()
    result = fn(*args, **kwargs)
    end = time.time()
    return result, end - start

def get_logger(name=None):
    """
    Get a logger with timestamped messages.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_dir(path):
    """
    Ensure that a directory exists.
    """
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass

def sha256_hex(data: bytes) -> str:
    """
    Return SHA-256 hash of data as hex string.
    """
    return hashlib.sha256(data).hexdigest()
