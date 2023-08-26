import numpy as np
from src.exchanges.common.localorderbook import BaseOrderBook
from src.sharedstate import SharedState


class OrderBookBinance(BaseOrderBook):
    def process_snapshot(self, snapshot):
        self.asks = np.array(snapshot["asks"], dtype=float)
        self.bids = np.array(snapshot["bids"], dtype=float)

    def process_data(self, recv):
        recv_data = recv["data"]

        asks = np.array(recv_data["a"], dtype=float)
        bids = np.array(recv_data["b"], dtype=float)

        self.asks = self.update_book(self.asks, asks)
        self.bids = self.update_book(self.bids, bids)


class BinanceBBAHandler:
    def __init__(self, sharedstate: SharedState, recv) -> None:
        self.ss = sharedstate
        self.data = recv["data"]

    def process(self):
        """
        Realtime BBA updates
        """

        self.ss.binance_bba = np.array(
            [[float(self.data["b"]), float(self.data["B"])], [float(self.data["a"]), float(self.data["A"])]],
            dtype=float,
        )
