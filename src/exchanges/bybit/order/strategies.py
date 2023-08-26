import asyncio
from src.exchanges.bybit.order.core import Order
from src.sharedstate import SharedState


class OrderStrategies:
    def __init__(self, sharedstate: SharedState):
        self.ss = sharedstate
        self.symbol = self.ss.bybit_symbol

    async def limit_chase(self, side: str, qty):
        assert side in ["Buy", "Sell"], "Invalid side provided"

        curr_orderId = None
        best_price_index = 0 if side == "Buy" else 1
        comparison_operator = (lambda old, new: old < new) if side == "Buy" else (lambda old, new: old > new)

        try:
            best_price = self.ss.bybit_bba[best_price_index][0]
            init_order_tuple = (side, best_price, qty)
            init_order = await Order(self.ss).submit_limit(init_order_tuple)
            curr_orderId = init_order["orderId"]

            while True:
                await asyncio.sleep(0.1)
                new_best_price = self.ss.bybit_bba[best_price_index][0]

                if comparison_operator(best_price, new_best_price):
                    best_price = new_best_price
                    amend_order_tuple = (curr_orderId, best_price, qty)
                    await Order(self.ss).amend(amend_order_tuple)

                if self.ss.futures_execution_feed:
                    latest_fill = self.ss.futures_execution_feed[-1]
                    if latest_fill["orderId"] == curr_orderId:
                        return latest_fill

        except asyncio.CancelledError:
            if curr_orderId is not None:
                await Order(self.ss).cancel(curr_orderId)
                print(f"Chase cancelled, {curr_orderId} cancelled")
            raise

        except Exception as e:
            print(e)
            raise
