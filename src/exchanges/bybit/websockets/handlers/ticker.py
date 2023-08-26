from src.sharedstate import SharedState


class BybitTickerHandler:
    def __init__(self, sharedstate: SharedState, data) -> None:
        self.ss = sharedstate
        self.data = data

    def process(self):
        if "markPrice" in self.data:
            self.ss.bybit_mark_price = float(self.data["markPrice"])
