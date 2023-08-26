from pybit.unified_trading import HTTP
from src.sharedstate import SharedState


class BybitPublicClient:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate
        self.symbol = self.ss.bybit_symbol
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = HTTP(api_key=self.ss.api_key, api_secret=self.ss.api_secret)
        return self._session

    async def klines(self, interval: int):
        return self.session.get_kline(category="linear", symbol=self.symbol, interval=str(interval))

    async def trades(self, limit: int):
        return self.session.get_public_trade_history(category="linear", symbol=self.symbol, limit=str(limit))
