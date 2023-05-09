from typing import List
from starlette.websockets import WebSocket

import asyncio
from aio_pika import connect, Message, IncomingMessage, ExchangeType


class Consumer:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.is_ready = False

    async def setup(self, rabbitmq_url: str, queue_name: str):
        self.rmq_conn = await connect(
            url=rabbitmq_url,
            loop=asyncio.get_running_loop()
        )
        self.channel = await self.rmq_conn.channel()
        exchange = await self.channel.declare_exchange(
            name='events',
            type=ExchangeType.DIRECT,
        )
        self.queue_name = queue_name
        queue = await self.channel.declare_queue(self.queue_name)
        await queue.bind(exchange=exchange, routing_key='metagame')
        await queue.consume(self._send, no_ack=True)
        self.is_ready = True

    async def push(self, msg: str):
        await self.channel.default_exchange.publish(
            Message(msg.encode("ascii")),
            routing_key=self.queue_name,
        )

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def remove(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def _send(self, message: IncomingMessage):
        living_connections = []
        while len(self.connections) > 0:
            websocket = self.connections.pop()
            await websocket.send_text(f"{message.body}")
            await message.ack()
            living_connections.append(websocket)
        self.connections = living_connections