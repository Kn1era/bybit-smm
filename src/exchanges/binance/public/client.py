from binance.client import AsyncClient


class PublicClient:
    def __init__(self, sharedstate) -> None:
        self.ss = sharedstate
        self.symbol = self.ss.binance_symbol
        self.client = AsyncClient()

    async def orderbook_snapshot(self, limit) -> dict:
        return await self.client.get_order_book(symbol=self.symbol, limit=limit)

    async def klines_snapshot(self, limit, interval):
        return await self.client.get_klines(symbol=self.symbol, interval=interval, limit=limit)

    async def trades_snapshot(self, limit):
        return await self.client.get_recent_trades(symbol=self.symbol, limit=limit)
