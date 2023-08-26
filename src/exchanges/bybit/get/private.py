import json
import time
import hashlib
import hmac
import aiohttp

from src.sharedstate import SharedState
from src.exchanges.bybit.order.endpoints import BaseEndpoints

OPEN_ORDERS = "/v5/order/realtime"
CURRENT_POSITION = "/v5/position/list"


class BybitPrivateClient:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate
        self.base_endpoint = BaseEndpoints.MAINNET1
        self.api_key = self.ss.api_key
        self.api_secret = self.ss.api_secret
        self.recvWindow = "5000"
        self.session = aiohttp.ClientSession()

        # Compute headers only once
        self.static_headers = {"X-BAPI-API-KEY": self.api_key, "X-BAPI-SIGN-TYPE": "2"}

    def _sign(self, params: str) -> dict:
        timestamp = str(int(time.time() * 1000))

        headers = self.static_headers.copy()
        headers["X-BAPI-TIMESTAMP"] = timestamp
        headers["X-BAPI-RECV-WINDOW"] = self.recvWindow

        param_str = f"{timestamp}{self.api_key}{self.recvWindow}{params}"
        hash = hmac.new(self.api_secret.encode("utf-8"), param_str.encode("utf-8"), hashlib.sha256)
        headers["X-BAPI-SIGN"] = hash.hexdigest()

        return headers

    async def open_orders(self):
        symbol = self.ss.bybit_symbol
        params = f"category=linear&symbol={symbol}&limit=50"
        endpoint = f"{self.base_endpoint}{OPEN_ORDERS}?{params}"

        try:
            # Submit request to the session
            req = await self.session.request(method="GET", url=endpoint, headers=self._sign(params))

            response = json.loads(await req.text())
            return response

        except Exception as e:
            print(e)

    async def current_position(self):
        symbol = self.ss.bybit_symbol
        params = f"category=linear&symbol={symbol}"
        endpoint = f"{self.base_endpoint}{CURRENT_POSITION}?{params}"

        try:
            # Submit request to the session
            req = await self.session.request(method="GET", url=endpoint, headers=self._sign(params))

            response = json.loads(await req.text())
            return response

        except Exception as e:
            print(e)

    async def close(self):
        await self.session.close()
