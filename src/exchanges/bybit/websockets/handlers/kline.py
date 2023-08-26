from collections import deque

import numpy as np
import pandas as pd

from src.indicators.bbw import bbw
from src.sharedstate import SharedState


class BybitKlineProcessor:
    def __init__(self, sharedstate: SharedState, recv_data=None) -> None:
        self.ss = sharedstate

        if recv_data:
            self.data = recv_data["result"]["list"]
            self.initialize_klines()
        else:
            self.data = None

    def initialize_klines(self):
        """
        Used to attain close values and calculate volatility
        """
        # Clear existing deque (if needed)
        self.ss.bybit_klines.clear()

        for candle in reversed(self.data):
            self.ss.bybit_klines.append(candle)

        self.update_volatility()

    def process(self, new_data):
        """
        Used to attain close values and calculate volatility
        """
        self.data = new_data

        for candle in self.data:
            new = (
                candle["start"],
                candle["open"],
                candle["high"],
                candle["low"],
                candle["close"],
                candle["volume"],
                candle["turnover"],
            )

            if candle["confirm"]:
                self.ss.bybit_klines.append(new)
            else:
                self.ss.bybit_klines[-1] = new

            self.update_volatility()

    def update_volatility(self):
        closes = [kline[4] for kline in self.ss.bybit_klines]
        self.ss.volatility_value = bbw(
            arr_in=np.array(closes, dtype=np.float64), length=self.ss.bb_length, std_numb=self.ss.bb_std
        )
        self.ss.volatility_value += self.ss.volatility_offset
