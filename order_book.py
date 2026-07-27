"""
order_book.py
Holds every live order in plain Python lists (no database of any kind)
and exposes helpers for sorted views, lookups and cleanup.

Buy side  -> sorted by price DESCENDING, then by arrival time ascending
             (highest price wins, ties broken by who arrived first).
Sell side -> sorted by price ASCENDING, then by arrival time ascending
             (lowest price wins, ties broken by who arrived first).
"""


class OrderBook:
    def __init__(self):
        # Plain in-memory Python lists - no external storage of any kind.
        self.buy_orders = []
        self.sell_orders = []
        # Every order ever created, keyed by order_id, kept for history/lookup
        # even after it is fully filled or cancelled.
        self.all_orders = {}

    # ------------------------------------------------------------------ #
    # Insertion / removal
    # ------------------------------------------------------------------ #
    def add_order(self, order):
        self.all_orders[order.order_id] = order
        if order.side == "BUY":
            self.buy_orders.append(order)
        else:
            self.sell_orders.append(order)

    def purge_inactive(self):
        """Remove fully filled / rejected orders from the active book."""
        self.buy_orders = [o for o in self.buy_orders if o.is_active()]
        self.sell_orders = [o for o in self.sell_orders if o.is_active()]

    def order_exists(self, order_id):
        return order_id in self.all_orders

    # ------------------------------------------------------------------ #
    # Sorted views (price-time priority)
    # ------------------------------------------------------------------ #
    def sorted_buy_orders(self):
        """Highest price first; ties broken by earliest arrival (FIFO)."""
        return sorted(
            [o for o in self.buy_orders if o.is_active()],
            key=lambda o: (-o.price, o.sequence),
        )

    def sorted_sell_orders(self):
        """Lowest price first; ties broken by earliest arrival (FIFO)."""
        return sorted(
            [o for o in self.sell_orders if o.is_active()],
            key=lambda o: (o.price, o.sequence),
        )

    # ------------------------------------------------------------------ #
    # Market data helpers
    # ------------------------------------------------------------------ #
    def best_bid(self):
        book = self.sorted_buy_orders()
        return book[0].price if book else None

    def best_ask(self):
        book = self.sorted_sell_orders()
        return book[0].price if book else None

    def spread(self):
        bid = self.best_bid()
        ask = self.best_ask()
        if bid is None or ask is None:
            return None
        return round(ask - bid, 4)

    def total_buy_orders(self):
        return len([o for o in self.buy_orders if o.is_active()])

    def total_sell_orders(self):
        return len([o for o in self.sell_orders if o.is_active()])
