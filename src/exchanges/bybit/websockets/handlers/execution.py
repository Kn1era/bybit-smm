from src.sharedstate import SharedState


class BybitExecutionHandler:
    def __init__(self, sharedstate: SharedState, data) -> None:
        self.ss = sharedstate
        self.data = data

    def process(self):
        for execution in self.data:
            symbol = execution["symbol"]
            if symbol == self.ss.bybit_symbol:
                self.ss.execution_feed.appendleft(
                    {
                        execution["orderId"]: {
                            "side": execution["side"],
                            "price": float(execution["execPrice"]),
                            "qty": float(execution["execQty"]),
                        }
                    }
                )
