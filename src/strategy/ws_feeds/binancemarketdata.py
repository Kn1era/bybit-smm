from datetime import datetime

import orjson
import websockets

from src.exchanges.binance.public.client import PublicClient
from src.exchanges.binance.websockets.handlers.orderbook import BinanceBBAHandler
from src.exchanges.binance.websockets.handlers.trades import BinanceTradesHandler, BinanceTradesInit
from src.exchanges.binance.websockets.public import PublicWs
from src.sharedstate import SharedState


class BinanceMarketData:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate

        # Dictionary to map streams to their respective handlers.
        self.stream_handler_map = {
            "Orderbook": self.ss.binance_book.process_data,
            "BBA": BinanceBBAHandler(self.ss).process,
            "Trades": BinanceTradesHandler(self.ss).process,
        }

    async def initialize_data(self):
        init_ob = await PublicClient(self.ss).orderbook_snapshot(500)
        self.ss.binance_book.process_snapshot(init_ob)

        init_trades = await PublicClient(self.ss).trades_snapshot(1000)
        BinanceTradesInit(self.ss, init_trades).process()

    async def binance_data_feed(self):
        await self.initialize_data()

        streams = ["Orderbook", "BBA", "Trades"]
        url, topics = PublicWs(self.ss).multi_stream_request(streams)

        async for websocket in websockets.connect(url):
            print(f"{datetime.now().strftime('%H:%S.%f')[:12]}: Subscribed to BINANCE {topics} feeds...")

            try:
                while True:
                    recv = orjson.loads(await websocket.recv())

                    if "success" not in recv:
                        handler = self.stream_handler_map.get(recv["stream"])
                        if handler:
                            handler(recv)

            except websockets.ConnectionClosed:
                continue
            except Exception as e:
                print(e)
                raise

    async def start_feed(self):
        await self.binance_data_feed()
