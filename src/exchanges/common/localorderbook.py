import numpy as np


class BaseOrderBook:
    def __init__(self):
        self.asks = np.empty((0, 2), float)
        self.bids = np.empty((0, 2), float)

    def update_book(self, book, data):
        indices = np.searchsorted(book[:, 0], data[:, 0])
        mask = indices < len(book)
        book = np.delete(book, indices[mask], axis=0)

        positive_data = data[data[:, 1] > 0]
        book = np.insert(book, np.searchsorted(book[:, 0], positive_data[:, 0]), positive_data, axis=0)

        return book

    def process_data(self, recv):
        raise NotImplementedError("Derived classes should implement this method")
