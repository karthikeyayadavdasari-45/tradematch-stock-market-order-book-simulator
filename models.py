"""
models.py
Core data models for the Stock Market Order Book Simulator.

Contains:
    - Order   : represents a single buy/sell limit order
    - Trade   : represents a single executed trade between two orders
"""

import itertools
import time


# Monotonically increasing counters used to guarantee a strict, unique
# time-priority ordering even when two orders arrive within the same
# millisecond (FIFO / price-time priority requirement).
_order_sequence = itertools.count(1)
_trade_sequence = itertools.count(1)


class Order:
    """
    Represents a single limit order sitting in (or having passed through)
    the order book.

    Attributes:
        order_id (str):      user supplied identifier for the order.
        side (str):          "BUY" or "SELL".
        price (float):       limit price of the order.
        quantity (int):      original quantity requested.
        remaining_quantity (int): quantity still unmatched.
        status (str):        "OPEN", "PARTIAL", "FILLED", or "REJECTED".
        timestamp (float):   time.time() when the order was received - used
                              for FIFO ordering at the same price level.
        sequence (int):      strict monotonic tie-breaker for FIFO ordering.
    """

    def __init__(self, order_id, side, price, quantity):
        self.order_id = order_id
        self.side = side.upper()
        self.price = float(price)
        self.quantity = int(quantity)
        self.remaining_quantity = int(quantity)
        self.status = "OPEN"
        self.timestamp = time.time()
        self.sequence = next(_order_sequence)

    def is_active(self):
        """An order can still be matched against."""
        return self.status in ("OPEN", "PARTIAL") and self.remaining_quantity > 0

    def register_fill(self, fill_quantity):
        """Reduce remaining quantity after a (partial) execution."""
        self.remaining_quantity -= fill_quantity
        if self.remaining_quantity <= 0:
            self.remaining_quantity = 0
            self.status = "FILLED"
        else:
            self.status = "PARTIAL"

    def formatted_time(self):
        return time.strftime("%H:%M:%S", time.localtime(self.timestamp))

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "side": self.side,
            "price": self.price,
            "quantity": self.quantity,
            "remaining_quantity": self.remaining_quantity,
            "status": self.status,
            "time": self.formatted_time(),
        }


class Trade:
    """
    Represents a single executed trade produced by the matching engine.

    Attributes:
        trade_id (int):     auto incrementing unique trade identifier.
        buyer_id (str):     order_id of the resting/incoming buy order.
        seller_id (str):    order_id of the resting/incoming sell order.
        price (float):      execution price (price of the resting order).
        quantity (int):     quantity executed in this trade.
        timestamp (float):  time.time() of execution.
    """

    def __init__(self, buyer_id, seller_id, price, quantity):
        self.trade_id = next(_trade_sequence)
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.price = float(price)
        self.quantity = int(quantity)
        self.timestamp = time.time()

    def formatted_time(self):
        return time.strftime("%H:%M:%S", time.localtime(self.timestamp))

    def to_dict(self):
        return {
            "trade_id": self.trade_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "price": self.price,
            "quantity": self.quantity,
            "time": self.formatted_time(),
        }
