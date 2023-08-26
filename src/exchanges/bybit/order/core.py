import asyncio
import json

import aiohttp

from src.exchanges.bybit.order.client import Client
from src.exchanges.bybit.order.endpoints import OrderEndpoints
from src.exchanges.bybit.order.types import OrderTypesFutures
from src.sharedstate import SharedState


class Order:
    # {order}: Tuple of struct (side: string, price: float, qty: float)

    def __init__(self, sharedstate: SharedState):
        self.ss = sharedstate
        self.order_market = OrderTypesFutures(self.ss.bybit_symbol)
        self.api_key = self.ss.api_key
        self.api_secret = self.ss.api_secret
        self.client = Client(self.api_key, self.api_secret)
        self.session = aiohttp.ClientSession()
        self.endpoints = OrderEndpoints

    def _extract_order(self, order):
        return tuple(map(str, order))

    async def _submit_order(self, payload):
        async with self.session:
            return await self.client.order(self.session, payload)

    async def submit_market(self, order: tuple) -> dict | None:
        side, _, qty = self._extract_order(order)
        payload = self.order_market.market(side, qty)
        return await self._submit_order(payload)

    async def submit_limit(self, order: tuple) -> dict | None:
        side, price, qty = self._extract_order(order)
        payload = self.order_market.limit(side, price, qty)
        return await self._submit_order(payload)

    async def submit_batch(self, orders: list) -> dict:
        single_endpoint = self.endpoints.CREATE_ORDER
        batch_endpoint = self.endpoints.CREATE_BATCH

        async def submit_sessionless_limit(order):
            payload = self.order_market.limit(order)
            return await self.client.submit(self.session, single_endpoint, payload)

        tasks = [submit_sessionless_limit(order) for order in orders[:4]]

        # Split the remaining orders into chunks of 10
        for i in range(4, len(orders), 10):
            batch = [self.order_market.limit(order) for order in orders[i : i + 10]]
            batch_payload = {"category": "linear", "request": batch}
            task = self.client.submit(self.session, batch_endpoint, batch_payload)
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def amend(self, order: tuple) -> dict | None:
        async with self.session:
            payload = self.order_market.amend(order)
            return await self.client.submit(self.session, self.endpoints.AMEND_ORDER, payload)

    async def amend_batch(self, orders: list) -> json:
        batch_endpoint = self.endpoints.AMEND_BATCH
        batch = [self.order_market.amend(order) for order in orders]
        batch_payload = {"category": "linear", "request": batch}
        await self.client.submit(self.session, batch_endpoint, batch_payload)

    async def cancel(self, orderId: str) -> dict | None:
        async with self.session:
            payload = self.order_market.cancel(orderId)
            return await self.client.submit(self.session, self.endpoints.CANCEL_SINGLE, payload)

    async def cancel_batch(self, orderIds: list):
        batch_endpoint = self.endpoints.CANCEL_BATCH
        batch = [self.order_market.cancel(order_id) for order_id in orderIds]
        batch_payload = {"category": "linear", "request": batch}
        await self.client.submit(self.session, batch_endpoint, batch_payload)

    async def cancel_all(self) -> dict | None:
        async with self.session:
            payload = self.order_market.cancel_all()
            return await self.client.submit(self.session, self.endpoints.CANCEL_ALL, payload)
