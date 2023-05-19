import os
import asyncio
import uvicorn
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi_health import health
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv

from config.utils import is_docker
from config.db import get_mongo
from consumer import Consumer

if is_docker() is False:  # Use .env file for secrets
    load_dotenv()

BASE_URL = os.getenv('BASE_URL') or None
LOG_LEVEL = os.getenv('LOG_LEVEL') or 'INFO'
VERSION = os.getenv('VERSION') or '1.0.0'
RABBITMQ_URL = os.getenv('RABBITMQ_URL') or None
MONGODB_DB = os.getenv('MONGODB_DB', 'warpgate')

WORLD_IDS = {
    'connery': 1,
    'miller': 10,
    'cobalt': 13,
    'emerald': 17,
    'jaeger': 19,
    'soltech': 40
}


async def is_mongo_alive(client: AsyncIOMotorClient = Depends(get_mongo)):
    try:
        await asyncio.wait_for(client.server_info(), timeout=30)
    except (ServerSelectionTimeoutError, TimeoutError):
        return False
    return True


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


@app.get("/zones/")
async def get_zone_status(world_id: int = None, client: AsyncIOMotorClient = Depends(get_mongo)):
    db = client[MONGODB_DB]
    if world_id:
        response = await db.continents.find_one({'world_id': world_id}, {'_id': False})
        return response
    else:
        cursor = db.continents.find({}, {'_id': False})
        response = []
        for i in await cursor.to_list(length=6):
            response.append(i)
        return response


@app.get("/population/")
async def get_population(world_id: int = None, client: AsyncIOMotorClient = Depends(get_mongo)):
    db = client[MONGODB_DB]
    if world_id:
        response = await db.population.find_one({'world_id': world_id}, {'_id': False})
        return response
    else:
        cursor = db.population.find({}, {'_id': False})
        response = []
        for i in await cursor.to_list(length=6):
            response.append(i)
        return response


@app.get("/alerts/")
async def get_alerts(world_id: int = None, client: AsyncIOMotorClient = Depends(get_mongo)):
    db = client[MONGODB_DB]
    alert_collection = db.alerts
    if world_id:
        cursor = alert_collection.find({'world_id': world_id}, {'_id': False})
    else:
        cursor = alert_collection.find({}, {'_id': False})
    response = []
    for i in await cursor.to_list(length=30):
        response.append(i)
    return response


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await consumer.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        consumer.remove(websocket)


app.add_api_route("/health", health([is_mongo_alive]))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
