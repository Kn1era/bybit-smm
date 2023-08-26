from src.sharedstate import SharedState


class BybitOrderHandler:
    def __init__(self, sharedstate: SharedState, data) -> None:
        self.ss = sharedstate
        self.data = data

    def process(self):
        current_orders = self.ss.current_orders

        new_orders = {
            order["orderId"]: {"price": order["price"], "qty": order["qty"], "side": order["side"]}
            for order in self.data
            if order.get("orderStatus") == "New"
        }

        filled_orders = set(order["orderId"] for order in self.data if order.get("orderStatus") == "Filled")

        # Update the orders
        current_orders.update(new_orders)

        # Remove filled orders
        for order_id in filled_orders:
            current_orders.pop(order_id, None)
