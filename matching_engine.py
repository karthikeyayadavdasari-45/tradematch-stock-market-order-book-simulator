"""
matching_engine.py
Implements the price-time priority matching algorithm.

Rules implemented:
    1. A buy order matches a sell order whenever buy.price >= sell.price.
    2. Among competing orders, price priority wins first (best price trades
       first), and time priority (FIFO, via Order.sequence) breaks ties at
       the same price.
    3. Execution price is the price of the order that was already resting
       in the book (the order with the earlier sequence number) - the
       incoming/aggressive order receives price improvement, exactly like
       a real exchange.
    4. Partial fills are fully supported: whichever order has the smaller
       remaining quantity is completely filled, and the other order's
       remaining_quantity is simply reduced and stays in the book.
    5. Fully filled orders are removed from the active book automatically
       (OrderBook.purge_inactive).
"""

from models import Trade


class MatchingEngine:
    def __init__(self):
        # Full execution history, most recent trade last.
        self.trade_history = []

    def run_matching(self, order_book):
        """
        Continuously cross the book until no more trades are possible.
        Returns the list of Trade objects generated during this call.
        """
        new_trades = []

        while True:
            buys = order_book.sorted_buy_orders()
            sells = order_book.sorted_sell_orders()

            if not buys or not sells:
                break

            best_buy = buys[0]
            best_sell = sells[0]

            # Core matching rule: highest bid must be >= lowest ask.
            if best_buy.price < best_sell.price:
                break

            # Time priority: whichever order arrived first sets the
            # execution price (price-time priority / price improvement).
            if best_buy.sequence < best_sell.sequence:
                execution_price = best_buy.price
            else:
                execution_price = best_sell.price

            fill_quantity = min(best_buy.remaining_quantity,
                                 best_sell.remaining_quantity)

            trade = Trade(
                buyer_id=best_buy.order_id,
                seller_id=best_sell.order_id,
                price=execution_price,
                quantity=fill_quantity,
            )

            best_buy.register_fill(fill_quantity)
            best_sell.register_fill(fill_quantity)

            self.trade_history.append(trade)
            new_trades.append(trade)

            # Drop any order(s) that are now fully filled.
            order_book.purge_inactive()

        return new_trades

    def last_traded_price(self):
        if not self.trade_history:
            return None
        return self.trade_history[-1].price

    def total_trades(self):
        return len(self.trade_history)

    def sorted_history(self):
        """Most recent trade first, for display purposes."""
        return list(reversed(self.trade_history))
