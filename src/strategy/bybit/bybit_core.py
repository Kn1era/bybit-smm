import asyncio

from src.sharedstate import SharedState
from src.strategy.bybit.bybit_mm import MarketMaker
from src.strategy.diff import Diff
from src.strategy.ws_feeds.bybitmarketdata import BybitMarketData
from src.strategy.ws_feeds.bybitprivatedata import BybitPrivateData
from src.utils.jit_funcs import nabs


class DataFeeds:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate
        self.bybit_market_data = BybitMarketData(self.ss)
        self.bybit_private_data = BybitPrivateData(self.ss)

    async def start_feeds(self) -> None:
        # Start all ws feeds as tasks, updating the sharedstate in the background
        await asyncio.gather(
            asyncio.create_task(self.bybit_market_data.start_feed(), name="BybitMarketData"),
            asyncio.create_task(self.bybit_private_data.start_feed(), name="BybitPrivateData"),
        )


class Strategy:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate
        self.market_maker = MarketMaker(self.ss)
        self.diff = Diff(self.ss)

    async def logic(self):
        # Delay to let data feeds warm up
        print("Warming up data feeds...")
        await asyncio.sleep(10)

        print("Starting strategy...")

        while True:
            # Pause for 5ms to let data feeds update
            await asyncio.sleep(0.005)

            # Generate new orders
            new_orders = self.market_maker.generate_orders()

            # Diff function will manage new order placements, if any
            await self.diff.diff(new_orders)

    async def run(self):
        await asyncio.gather(DataFeeds(self.ss).start_feeds(), self.logic())
