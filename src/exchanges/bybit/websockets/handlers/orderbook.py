import numpy as np

from src.exchanges.common.localorderbook import BaseOrderBook
from src.sharedstate import SharedState


class OrderBookBybit(BaseOrderBook):
    def process_snapshot(self, asks, bids):
        self.asks = np.array(asks, float)
        self.bids = np.array(bids, float)

    def process_data(self, recv):
        asks = np.array(recv["data"]["a"], dtype=float)
        bids = np.array(recv["data"]["b"], dtype=float)

        if recv["type"] == "snapshot":
            self.process_snapshot(asks, bids)
        elif recv["type"] == "delta":
            self.asks = self.update_book(self.asks, asks)
            self.bids = self.update_book(self.bids, bids)


class BybitBBAHandler:
    def __init__(self, sharedstate: SharedState, data: dict) -> None:
        self.ss = sharedstate
        self.data = data

    def process(self):
        best_bid = self.data["b"]
        best_ask = self.data["a"]

        if len(best_bid) != 0:
            # Directly assign to the existing array
            self.ss.bybit_bba[0, 0] = float(best_bid[0][0])
            self.ss.bybit_bba[0, 1] = float(best_bid[0][1])

        if len(best_ask) != 0:
            # Directly assign to the existing array
            self.ss.bybit_bba[1, 0] = float(best_ask[0][0])
            self.ss.bybit_bba[1, 1] = float(best_ask[0][1])
