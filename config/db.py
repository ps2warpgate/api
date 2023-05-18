import os
import redis
from motor import motor_asyncio
from dotenv import load_dotenv

from config.utils import is_docker


if is_docker() is False:  # Use .env file for secrets
    load_dotenv()


LOG_LEVEL = os.getenv('LOG_LEVEL') or 'INFO'
REDIS_HOST = os.getenv('REDIS_HOST') or 'localhost'
REDIS_PORT = os.getenv('REDIS_PORT') or 6379
REDIS_DB = os.getenv('REDIS_DB') or 0
REDIS_PASS = os.getenv('REDIS_PASS') or None
MONGODB_URL = os.getenv('MONGODB_URL', None)


def create_redis():
    return redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASS,
        decode_responses=True
    )


pool = create_redis()


async def get_mongo():
    return motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
