import os
import socket

import redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry

host = os.getenv('REDIS_HOST')
password = os.getenv('REDIS_PASSWORD')
port = os.getenv('REDIS_PORT')

retry = Retry(ExponentialBackoff(), 6)

Broker = redis.StrictRedis(
    host=host,
    password=password,
    port=port,
    db=0,
    retry=retry,
    retry_on_error=[ConnectionError, TimeoutError, socket.timeout],
    decode_responses=True,
    health_check_interval=5,
)
