import numpy as np

from src.sharedstate import SharedState
from src.strategy.features.mark_spread import mark_price_spread
from src.strategy.features.momentum import trend_feature
from src.utils.jit_funcs import linspace, nsqrt
from src.utils.rounding import round_step_size


class CalculateFeatures:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate
        self.depths = np.array([10, 25, 50, 100, 200])

    def momentum_klines(self):
        return trend_feature(self.ss.bybit_klines[:, 4], self.depths)

    def bybit_mark_spread(self):
        return mark_price_spread(self.ss.bybit_mark_price, self.ss.bybit_weighted_mid_price)

    def generate_skew(self):
        momentum_weight = 0.5
        mark_spread_weight = 0.5
        momentum = self.momentum_klines() * momentum_weight
        mark_spread = self.bybit_mark_spread() * mark_spread_weight
        return momentum + mark_spread


class MarketMaker:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate
        self.calculate_features = CalculateFeatures(sharedstate)
        self.max_orders = self.ss.num_orders
        self.tick_size = self.ss.bybit_tick_size
        self.lot_size = self.ss.bybit_lot_size

    def skew(self) -> float:
        skew = self.calculate_features.generate_skew()
        inventory_delta = self.ss.inventory_delta
        inventory_extreme = self.ss.inventory_extreme

        bid_skew = np.where(skew >= 0, np.clip(skew, 0, 1), 0)
        ask_skew = np.where(skew < 0, np.clip(skew, -1, 0), 0)

        bid_skew[inventory_delta < 0] += inventory_delta
        ask_skew[inventory_delta > 0] -= inventory_delta

        bid_skew[inventory_delta < -inventory_extreme] = 1
        ask_skew[inventory_delta > inventory_extreme] = 1

        self.bid_skew = nabs(float(bid_skew))
        self.ask_skew = nabs(float(ask_skew))
        return bid_skew, ask_skew

    def quotes_price_range(self) -> tuple[np.ndarray, np.ndarray]:
        best_bid_price = self.ss.bybit_bba[0][0]
        best_ask_price = self.ss.bybit_bba[1][0]
        base_range = self.ss.volatility_value / 2

        if self.bid_skew >= 1 or self.ask_skew >= 1:
            self.num_bids = self.max_orders if self.bid_skew >= 1 else None
            self.num_asks = self.max_orders if self.ask_skew >= 1 else None
            bid_prices = (
                linspace(best_bid_price, best_bid_price - (self.ss.bybit_tick_size * self.num_bids), self.num_bids)
                if self.bid_skew >= 1
                else None
            )
            ask_prices = (
                linspace(best_ask_price, best_ask_price + (self.ss.bybit_tick_size * self.num_asks), self.num_asks)
                if self.ask_skew >= 1
                else None
            )
            return bid_prices, ask_prices

        # Shared calculations
        self.num_bids = int((self.max_orders / 2) * (1 + max(self.bid_skew, self.ask_skew)))
        self.num_asks = self.max_orders - self.num_bids
        bid_lower = best_bid_price - (base_range * (1 - self.bid_skew))
        ask_upper = best_ask_price + (base_range * (1 - self.ask_skew))

        if self.bid_skew >= self.ask_skew:
            best_bid_price = best_ask_price - self.ss.bybit_tick_size
            best_ask_price += self.ss.target_spread
        else:
            best_ask_price = best_bid_price + self.ss.bybit_tick_size
            best_bid_price -= self.ss.target_spread

        bid_prices = linspace(best_bid_price, bid_lower, self.num_bids)
        ask_prices = linspace(best_ask_price, ask_upper, self.num_asks)

        return bid_prices, ask_prices

    def quotes_size_range(self) -> tuple[np.ndarray, np.ndarray]:
        if self.bid_skew >= 1:
            bid_quantities = np.full(
                self.num_bids, np.median([self.ss.minimum_order_size, self.ss.maximum_order_size / 2])
            )
            return bid_quantities, None
        elif self.ask_skew >= 1:
            ask_quantities = np.full(
                self.num_asks, np.median([self.ss.minimum_order_size, self.ss.maximum_order_size / 2])
            )
            return None, ask_quantities

        bid_min = self.ss.minimum_order_size * (1 + nsqrt(self.bid_skew, 1))
        ask_min = self.ss.minimum_order_size * (1 + nsqrt(self.ask_skew, 1))

        bid_upper = self.ss.maximum_order_size * (1 - self.bid_skew)
        ask_upper = self.ss.maximum_order_size * (1 - self.ask_skew)

        bid_quantities = linspace(
            bid_min if self.bid_skew >= self.ask_skew else self.ss.minimum_order_size, bid_upper, self.num_bids
        )
        ask_quantities = linspace(
            ask_min if self.ask_skew > self.bid_skew else self.ss.minimum_order_size, ask_upper, self.num_asks
        )

        return bid_quantities, ask_quantities

    def generate_orders(self) -> list[tuple[str, str, str]]:
        self.skew()
        bid_prices, ask_prices = self.quotes_price_range()
        bid_quantities, ask_quantities = self.quotes_size_range()

        orders = []

        if self.num_bids is not None:
            for i in range(self.num_bids):
                bid_p = round_step_size(bid_prices[i], self.ss.bybit_tick_size)
                bid_q = round_step_size(bid_quantities[i], self.ss.bybit_lot_size)
                orders.append(["Buy", bid_p, bid_q])

        if self.num_asks is not None:
            for i in range(self.num_asks):
                ask_p = round_step_size(ask_prices[i], self.ss.bybit_tick_size)
                ask_q = round_step_size(ask_quantities[i], self.ss.bybit_lot_size)
                orders.append(["Sell", ask_p, ask_q])

        return orders
