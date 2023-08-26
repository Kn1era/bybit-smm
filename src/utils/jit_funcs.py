import numpy as np
from numba import njit, prange, float64, int32


@njit(float64(float64, int32))
def nsqrt(value: float, n: int) -> float:
    """
    Return the n'th root of a value
    """
    if n == 1:
        return value**0.5  # using ** for power is often faster with Numba

    else:
        for _ in range(n):
            value = value**0.5

        return value


@njit(float64(float64, int32))
def npower(value: float, n: int) -> float:
    """
    Return the n'th square of a value
    """
    return value**n  # using ** for power is often faster with Numba


@njit(float64[:](float64, float64, int32))  # return type is a 1D array of float64
def linspace(start: float, end: float, n: int) -> np.ndarray:
    step = (end - start) / (n - 1)
    result = np.empty(n, dtype=np.float64)

    for i in prange(n):  # parallelized loop
        result[i] = start + step * i

    return result
