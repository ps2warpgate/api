import os
import redis
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from config.utils import is_docker
from config.db import pool


if is_docker() is False:  # Use .env file for secrets
    load_dotenv()


BASE_URL = os.getenv('BASE_URL') or None
LOG_LEVEL = os.getenv('LOG_LEVEL') or 'INFO'
VERSION = os.getenv('VERSION') or '1.0.0'

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


app = FastAPI(
    title = "Warpgate API",
    version = VERSION,
    license_info = {
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html"
    },
    root_path = BASE_URL
)

origins = [
    BASE_URL,
    '127.0.0.1'
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/worlds/")
def read_world(id: int, cache = Depends(get_redis)):
    for i in WORLD_IDS:
        if WORLD_IDS[i] == id:
            world_data = cache.json().get(i)
    return world_data


@app.get("/health")
def healthcheck():
    return {"status": "UP"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
