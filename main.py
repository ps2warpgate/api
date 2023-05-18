import os
import redis
import uvicorn
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from config.utils import is_docker
from config.db import pool, get_mongo
from consumer import Consumer

if is_docker() is False:  # Use .env file for secrets
    load_dotenv()

BASE_URL = os.getenv('BASE_URL') or None
LOG_LEVEL = os.getenv('LOG_LEVEL') or 'INFO'
VERSION = os.getenv('VERSION') or '1.0.0'
RABBITMQ_URL = os.getenv('RABBITMQ_URL') or None
MONGODB_DB = os.getenv('MONGODB_DB', 'warpgate')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'alerts')

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
    title="Warpgate API",
    version=VERSION,
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html"
    },
    root_path=BASE_URL
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

consumer = Consumer()


@app.on_event("startup")
async def startup_event():
    if not consumer.is_ready:
        await consumer.setup(
            rabbitmq_url=RABBITMQ_URL,
            queue_name='warpgate'
        )


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/worlds/")
def read_world(id: int, cache=Depends(get_redis)):
    for i in WORLD_IDS:
        if WORLD_IDS[i] == id:
            world_data = cache.json().get(i)
            return world_data


@app.get("/alerts/")
async def get_alerts(id: int = None, client: AsyncIOMotorClient = Depends(get_mongo)):
    db = client[MONGODB_DB]
    alert_collection = db[MONGODB_COLLECTION]
    if id:
        cursor = alert_collection.find({'world_id': id})
    else:
        cursor = alert_collection.find()
    response = []
    for i in await cursor.to_list(length=30):
        response.append(i)
    return response


@app.get("/health")
def healthcheck():
    return {"status": "UP"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await consumer.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        consumer.remove(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
