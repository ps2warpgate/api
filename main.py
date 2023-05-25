import os
import uvicorn
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from enum import IntEnum
from pydantic.dataclasses import dataclass

from constants.models import MetagameEvent, WorldZones
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


class WorldId(IntEnum):
    connery = 1
    miller = 10
    cobalt = 13
    emerald = 17
    jaeger = 19
    soltech = 40


@dataclass
class Zones:
    amerish: int
    esamir: int
    hossin: int
    indar: int
    oshur: int


@dataclass
class World:
    id: WorldId
    total: int
    zones: Zones


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
async def get_zone_status(
        world_id: WorldId = None,
        client: AsyncIOMotorClient = Depends(get_mongo)) -> WorldZones | list[WorldZones]:
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
async def get_population(world_id: WorldId = None, client: AsyncIOMotorClient = Depends(get_mongo)):
    db = client[MONGODB_DB]
    now = datetime.utcnow()
    delta = timedelta(seconds=1200)
    if world_id:
        query_filter = {'metadata.world_id': world_id, 'timestamp': {'$gt': now - delta}}
    else:
        query_filter = {'timestamp': {'$gt': now - delta}}
    players = []
    zones = {2: 0, 4: 0, 6: 0, 8: 0, 344: 0}
    async for event in db.realtime.find(query_filter, {'_id': False}):
        zone_id = event['metadata']['zone_id']
        print(zone_id)
        if event['attacker_id'] not in players:
            players.append(event['attacker_id'])
            if zone_id in zones:
                zones[zone_id] += 1
        if event['victim_id'] not in players:
            players.append(event['victim_id'])
            if zone_id in zones:
                zones[zone_id] += 1

    response = {
        'total': len(players),
    }
    if world_id:
        response.update({'zones': zones})

    return response


@app.get("/alerts/")
async def get_alerts(
        world_id: WorldId = None,
        client: AsyncIOMotorClient = Depends(get_mongo)) -> list[MetagameEvent]:
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
