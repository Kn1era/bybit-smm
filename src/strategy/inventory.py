from src.sharedstate import SharedState


class Inventory:
    def __init__(self, sharedstate: SharedState) -> None:
        self.ss = sharedstate

    def calculate_delta(self, data) -> None:
        """
        Calculates the current position delta relative to account size
        """

        acc_size = self.ss.account_size
        val = 0

        for position_data in data:
            side = position_data["side"]

            if not side:
                continue

            value = float(position_data["positionValue"])

            if side == "Buy":
                val += value
            elif side == "Sell":
                val -= value

        self.ss.inventory_delta += val / acc_size
