import os
from motor import motor_asyncio
from dotenv import load_dotenv

from config.utils import is_docker


if is_docker() is False:  # Use .env file for secrets
    load_dotenv()


LOG_LEVEL = os.getenv('LOG_LEVEL') or 'INFO'
MONGODB_URL = os.getenv('MONGODB_URL', None)


async def get_mongo():
    return motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
