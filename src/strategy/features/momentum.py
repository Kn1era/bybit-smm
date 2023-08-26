import numpy as np
from numba import njit
from src.indicators.ema import ema


@njit
def trend_feature(closes, lengths):
    """
    Make sure lengths are fed in from longest to shortest
    """
    curr_price = closes[-1]
    n = len(lengths)
    vals = np.empty(n, dtype=np.float64)

    all_ema = ema(closes, max(lengths))

    for i in range(n):
        ema_val = all_ema[-lengths[i]]

        # Safety check
        if ema_val == 0:
            vals[i] = 0  # or any other value you'd like to default to
        else:
            vals[i] = np.log(curr_price / ema_val) * 100

    lambda_ = 1 - (2 / float(n + 1))
    weights = np.array([lambda_**i for i in range(n)])
    trend_val = np.sum(vals * weights) / np.sum(weights)

    return trend_val
