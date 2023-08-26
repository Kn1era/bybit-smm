import numpy as np
from numba import njit


@njit(nogil=True, fastmath=True)  # Enable fastmath for potential speed-up
def ema(arr_in: np.ndarray, window: int) -> np.ndarray:
    """
    Hyper-fast EWMA implementation
    """
    n = arr_in.shape[0]
    ewma = np.empty(n, dtype=np.float64)
    alpha = 2 / float(window + 1)

    ewma[0] = arr_in[0]

    for i in range(1, n):
        ewma[i] = alpha * arr_in[i] + (1 - alpha) * ewma[i - 1]

    return ewma
