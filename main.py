import os
import redis
from fastapi import Depends, FastAPI
from dotenv import load_dotenv

from config.utils import is_docker, log
from config.db import pool


if is_docker() is False:  # Use .env file for secrets
    load_dotenv()


API_KEY = os.getenv('API_KEY') or 's:example'
LOG_LEVEL = os.getenv('LOG_LEVEL') or 'INFO'

WORLD_IDS = {
    'connery': 1,
    'miller': 10,
    'cobalt': 13,
    'emerald': 17,
    'jaeger': 19,
    'soltech': 40
}


def get_redis():
    return redis.Redis(connection_pool=pool)

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/worlds/{world_id}")
def read_world(world_id: int, cache = Depends(get_redis)):
    for i in WORLD_IDS:
        if WORLD_IDS[i] == world_id:
            world_data = cache.hgetall(i)
    return world_data