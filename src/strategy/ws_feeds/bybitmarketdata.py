from datetime import datetime

import orjson
import websockets

from src.exchanges.bybit.get.public import BybitPublicClient
from src.exchanges.bybit.websockets.endpoints import WsStreamLinks
from src.exchanges.bybit.websockets.handlers.kline import BybitKlineProcessor
from src.exchanges.bybit.websockets.handlers.orderbook import BybitBBAHandler
from src.exchanges.bybit.websockets.handlers.ticker import BybitTickerHandler
from src.exchanges.bybit.websockets.handlers.trades import BybitTradesHandler, BybitTradesInit
from src.exchanges.bybit.websockets.public import PublicWs
from src.sharedstate import SharedState


class BybitMarketData:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate

        # Dictionary to map topics to their respective handlers.
        self.topic_handler_map = {
            "Orderbook": self.ss.bybit_book.process_data,
            "BBA": BybitBBAHandler(self.ss).process,
            "Trades": BybitTradesHandler(self.ss).process,
            "Ticker": BybitTickerHandler(self.ss).process,
            "Kline": BybitKlineProcessor(self.ss).process,
        }

    async def initialize_data(self):
        init_kline_data = await BybitPublicClient(self.ss).klines(1)
        BybitKlineProcessor(self.ss, init_kline_data).process()

        init_trades = await BybitPublicClient(self.ss).trades(1000)
        BybitTradesInit(self.ss, init_trades).process()

    async def bybit_data_feed(self):
        await self.initialize_data()

        streams = ["Orderbook", "BBA", "Trades", "Ticker", "Kline"]
        req, topics = PublicWs(self.ss).multi_stream_request(streams, depth=500, interval=1)

        async for websocket in websockets.connect(WsStreamLinks.FUTURES_PUBLIC_STREAM):
            print(f"{datetime.now().strftime('%H:%S.%f')[:12]}: Subscribed to BYBIT {topics} feed...")

            try:
                await websocket.send(req)

                while True:
                    recv = orjson.loads(await websocket.recv())

                    if "success" in recv:
                        continue

                    handler = self.topic_handler_map.get(recv["topic"])
                    if handler:
                        handler(recv["data"])

            except websockets.ConnectionClosed:
                continue
            except Exception as e:
                print(e)
                raise

    async def start_feed(self):
        await self.bybit_data_feed()
