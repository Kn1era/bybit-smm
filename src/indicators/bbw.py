from numba import njit, prange
import numpy as np

# %%


@njit(nogil=True, fastmath=True)  # Enable fastmath for potential speed-up
def ewma(arr_in: np.ndarray, window: int) -> np.ndarray:
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


@njit(parallel=True, fastmath=True)
def bbw(arr_in: np.ndarray, length: int, std_numb: int) -> float:
    """
    Hyper-fast Bollinger Band Width implementation
    Be careful with the data type in the array!
    """

    return 2 * std_numb * np.std(arr_in[-length:]) / ewma(arr_in[:], length)[-1]
