import asyncio
from src.utils.jit_funcs import nabs
from src.exchanges.bybit.order.core import Order
from src.sharedstate import SharedState


class Diff:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate

    def segregate_orders(self, orders: dict):
        """Segregate orders based on their side and sort them by price."""
        buys = []
        sells = []

        for orderId, details in orders.items():
            if details["side"] == "Buy":
                buys.append((orderId, [details["side"], details["price"], details["qty"]]))
            else:
                sells.append((orderId, [details["side"], details["price"], details["qty"]]))

        buys.sort(key=lambda x: x[1][1], reverse=True)
        sells.sort(key=lambda x: x[1][1])

        return buys, sells

    def current_close_to_bba(self):
        buys, sells = self.segregate_orders(self.ss.current_orders)
        return buys[:2], sells[:2]

    def current_far_from_bba(self, close_bids, close_asks):
        close_orders_ids = {order[0] for order in close_bids + close_asks}
        far_orders = {
            orderId: info for orderId, info in self.ss.current_orders.items() if orderId not in close_orders_ids
        }
        return self.segregate_orders(far_orders)

    def current_all(self):
        cb, ca = self.current_close_to_bba()
        fb, fa = self.current_far_from_bba(cb, ca)
        return cb + ca + fb + fa

    def new_close_to_bba(self, new_orders):
        return new_orders[:2], new_orders[2:4]

    async def amend_orders(self, old_orders, new_orders):
        tasks = [
            asyncio.create_task(Order(self.ss).amend((old[0], new[1], new[2])))
            for old, new in zip(old_orders, new_orders)
            if old[1][1] != new[1]
        ]
        await asyncio.gather(*tasks)

    async def diff(self, new_orders: list) -> bool:
        """
        This function checks new orders vs current orders

        Checks performed:

        - No current orders
            -> Send all orders as batch

        - Number of new orders and current are not same
            -> Cancel all and send all as batch

        - All are bids/asks and have changed (extreme scenario)
            -> Cancel all and send all as batch

        - 4 close to BBA orders have changed
            -> Amend changed orders to new price/qty

        - Number of bids/asks have changed for outer orders
            -> Cancel batch and send batch

        - Rest outer orders have changed more than buffer
            -> Cancel changed and send changed as batch
        """

        if not self.ss.current_orders:
            await Order(self.ss).submit_batch(new_orders)
            return

        # Sorting and segregating orders
        new_best_bids, new_best_asks = self.new_close_to_bba(new_orders)
        new_outer_bids, new_outer_asks = self.new_far_from_bba(new_orders)
        new_all_orders = new_best_bids + new_best_asks + new_outer_bids + new_outer_asks

        current_best_bids, current_best_asks = self.current_close_to_bba()
        current_outer_bids, current_outer_asks = self.current_far_from_bba(current_best_bids, current_best_asks)
        current_all_orders = current_best_bids + current_best_asks + current_outer_bids + current_outer_asks
        current_outer_orders = current_outer_bids + current_outer_asks

        # Perform checks
        # Second check (reordered for optimization purposes)
        if len(self.ss.current_orders) < len(new_orders):
            await Order(self.ss).cancel_all()
            await Order(self.ss).submit_batch(new_orders)
            return

        # Third check
        if len(current_outer_bids) == len(current_outer_orders) or len(current_outer_asks) == len(
            current_outer_orders
        ):
            if new_all_orders != current_all_orders:
                await Order(self.ss).cancel_all()
                await Order(self.ss).submit_batch(new_orders)
            return

        # Fourth check
        if new_best_bids and new_best_asks:
            await self.amend_orders(current_best_bids, new_best_bids)
            await self.amend_orders(current_best_asks, new_best_asks)

        # Fifth check
        if len(current_outer_bids) != len(new_outer_bids) or len(current_outer_asks) != len(new_outer_asks):
            current_outer_orders_ids = [order[0] for order in current_outer_orders]
            await Order(self.ss).cancel_batch(current_outer_orders_ids)
            await Order(self.ss).submit_batch(new_outer_bids + new_outer_asks)
            return

        # Sixth check
        amend_batches = []

        for current, new in zip(current_outer_bids + current_outer_asks, new_outer_bids + new_outer_asks):
            if nabs(current[1][1] - new[1][1]) > self.ss.buffer:
                amend_batches.append((current[0], new[1][1], new[1][2]))

        if amend_batches:
            await Order(self.ss).amend_batch(amend_batches)

        return
