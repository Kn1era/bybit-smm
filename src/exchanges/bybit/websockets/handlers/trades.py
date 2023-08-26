import numpy as np
from src.sharedstate import SharedState


class BybitTradesInit:
    def __init__(self, sharedstate: SharedState, data) -> None:
        self.ss = sharedstate
        self.data = data["result"]["list"]

    def process(self):
        trades_list = []

        for row in self.data:
            side = 0 if row["side"] == "Buy" else 1
            trades_list.append([row["time"], side, row["price"], row["size"]])

        trades_array = np.array(trades_list, dtype=float)
        self.ss.bybit_trades.extend(trades_array)


class BybitTradesHandler:
    def __init__(self, sharedstate: SharedState, data) -> None:
        self.ss = sharedstate
        self.data = data[0]

    def process(self):
        side = 0 if self.data["S"] == "Buy" else 1
        new_trade = np.array([[self.data["T"], side, self.data["p"], self.data["v"]]], dtype=float)
        self.ss.bybit_trades.append(new_trade)
