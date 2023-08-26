import asyncio
from datetime import datetime

import orjson
import websockets

from src.exchanges.bybit.get.private import BybitPrivateClient
from src.exchanges.bybit.websockets.endpoints import WsStreamLinks
from src.exchanges.bybit.websockets.handlers.execution import BybitExecutionHandler
from src.exchanges.bybit.websockets.handlers.order import BybitOrderHandler
from src.exchanges.bybit.websockets.handlers.position import BybitPositionHandler
from src.exchanges.bybit.websockets.private import PrivateWs
from src.sharedstate import SharedState


class BybitPrivateData:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate
        self.api_key = self.ss.api_key
        self.api_secret = self.ss.api_secret
        self.symbol = self.ss.bybit_symbol
        self.private_ws = PrivateWs(self.api_key, self.api_secret)

        # Create a dictionary to map topics to handlers
        self.topic_handler_map = {
            "Position": BybitPositionHandler,
            "Execution": BybitExecutionHandler,
            "Order": BybitOrderHandler,
        }

    async def open_orders_sync(self):
        while True:
            recv = await BybitPrivateClient(self.ss).open_orders()
            data = recv["result"]["list"]
            self.ss.current_orders = {
                o["orderId"]: {"price": float(o["price"]), "qty": float(o["qty"]), "side": o["side"]} for o in data
            }
            await asyncio.sleep(0.5)

    async def current_position_sync(self):
        while True:
            recv = await BybitPrivateClient(self.ss).current_position()
            data = recv["result"]["list"]
            BybitPositionHandler(self.ss, data).process()
            await asyncio.sleep(0.5)

    async def privatefeed(self):
        req, topics = self.private_ws.multi_stream_request(["Position", "Execution", "Order"])
        print(f"{datetime.now().strftime('%H:%S.%f')[:12]}: Subscribed to BYBIT {topics} feeds...")

        async for websocket in websockets.connect(WsStreamLinks.COMBINED_PRIVATE_STREAM):
            try:
                await websocket.send(self.private_ws.auth())
                await websocket.send(req)

                while True:
                    recv = orjson.loads(await websocket.recv())
                    if "success" in recv:
                        continue

                    data = recv["data"]
                    handler_cls = self.topic_handler_map.get(recv["topic"])
                    if handler_cls:
                        handler_cls(self.ss, data).process()

            except websockets.ConnectionClosed:
                continue
            except Exception as e:
                print(e)
                raise

    async def start_feed(self):
        tasks = [self.open_orders_sync(), self.current_position_sync(), self.privatefeed()]
        await asyncio.gather(*tasks)
