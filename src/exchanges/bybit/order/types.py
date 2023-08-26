from enum import Enum
from typing import Union


class OrderCategory(Enum):
    SPOT = "spot"
    LINEAR = "linear"


class OrderBase:
    def __init__(self, symbol: str, category: OrderCategory):
        self.symbol = symbol
        self.category = category.value

    def _base_payload(self) -> dict[str, str | int]:
        return {
            "category": self.category,
            "symbol": self.symbol,
        }

    def create_limit_payload(self, side: str, price: str, qty: str) -> dict:
        return {
            **self._base_payload(),
            "side": side,
            "orderType": "Limit",
            "price": price,
            "qty": qty,
            "timeInForce": "PostOnly",
        }

    def create_market_payload(self, side: str, qty: str) -> dict:
        return {
            **self._base_payload(),
            "side": side,
            "orderType": "Market",
            "qty": qty,
        }

    def cancel_payload(self, orderId: str) -> dict:
        return {**self._base_payload(), "orderId": orderId}


class OrderTypesSpot(OrderBase):
    def __init__(self, symbol: str, margin: bool):
        super().__init__(symbol, OrderCategory.SPOT)
        self.is_leverage = 1 if margin else 0

    def _base_payload(self) -> dict[str, Union[str, int]]:
        payload = super()._base_payload()
        payload["isLeverage"] = self.is_leverage
        return payload


class OrderTypesFutures(OrderBase):
    def __init__(self, symbol: str):
        super().__init__(symbol, OrderCategory.LINEAR)

    def amend_payload(self, order) -> dict:
        return {**self._base_payload(), "orderId": order[0], "qty": order[2], "price": order[1]}

    def cancel_all_payload(self) -> dict:
        return self._base_payload()
