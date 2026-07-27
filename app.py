"""
app.py
Flask entry point for the Stock Market Order Book Simulator.

Everything lives in process memory - two plain Python lists inside an
OrderBook instance, plus a list inside the MatchingEngine. There is no
database, no external API, and no JavaScript anywhere in this project.

Run with:
    python app.py
"""

from flask import Flask, render_template, request, redirect, url_for, flash

from models import Order
from order_book import OrderBook
from matching_engine import MatchingEngine

app = Flask(__name__)
app.secret_key = "order-book-simulator-secret-key"  # required for flash messages

# ---------------------------------------------------------------------- #
# Global, in-memory application state (plain Python objects only)
# ---------------------------------------------------------------------- #
book = OrderBook()
engine = MatchingEngine()


# ---------------------------------------------------------------------- #
# Validation helpers
# ---------------------------------------------------------------------- #
def validate_order_id(order_id):
    if not order_id or not order_id.strip():
        return "Order ID is required."
    if book.order_exists(order_id.strip()):
        return f"Order ID '{order_id.strip()}' already exists. Choose a unique ID."
    return None


def validate_side(side):
    if side not in ("BUY", "SELL"):
        return "Side must be either BUY or SELL."
    return None


def validate_price(price_raw):
    try:
        price = float(price_raw)
    except (TypeError, ValueError):
        return None, "Price must be a valid number."
    if price <= 0:
        return None, "Price must be greater than zero."
    return round(price, 2), None


def validate_quantity(quantity_raw):
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        return None, "Quantity must be a whole number."
    if quantity <= 0:
        return None, "Quantity must be greater than zero."
    return quantity, None


def validate_new_order(order_id, side, price_raw, quantity_raw):
    """Runs every validation rule; returns a list of error strings (empty = valid)."""
    errors = []

    id_error = validate_order_id(order_id)
    if id_error:
        errors.append(id_error)

    side_error = validate_side(side)
    if side_error:
        errors.append(side_error)

    price, price_error = validate_price(price_raw)
    if price_error:
        errors.append(price_error)

    quantity, quantity_error = validate_quantity(quantity_raw)
    if quantity_error:
        errors.append(quantity_error)

    return errors, price, quantity


# ---------------------------------------------------------------------- #
# Analytics helper (shared by home preview + analytics page)
# ---------------------------------------------------------------------- #
def build_analytics():
    best_bid = book.best_bid()
    best_ask = book.best_ask()
    spread = book.spread()
    last_price = engine.last_traded_price()

    return {
        "total_buy_orders": book.total_buy_orders(),
        "total_sell_orders": book.total_sell_orders(),
        "total_trades": engine.total_trades(),
        "best_bid": f"{best_bid:.2f}" if best_bid is not None else "--",
        "best_ask": f"{best_ask:.2f}" if best_ask is not None else "--",
        "spread": f"{spread:.2f}" if spread is not None else "--",
        "last_price": f"{last_price:.2f}" if last_price is not None else "--",
    }


# ---------------------------------------------------------------------- #
# Routes
# ---------------------------------------------------------------------- #
def _with_depth_percent(orders):
    """Attach a 0-100 relative width (vs. the largest order shown) for the
    pure-CSS depth bars on the home page preview."""
    orders = list(orders)
    max_qty = max((o.remaining_quantity for o in orders), default=0)
    rows = []
    for o in orders:
        percent = int((o.remaining_quantity / max_qty) * 100) if max_qty else 0
        rows.append({"order": o, "percent": max(percent, 6)})
    return rows


@app.route("/")
def home():
    preview_buys = _with_depth_percent(book.sorted_buy_orders()[:4])
    preview_sells = _with_depth_percent(book.sorted_sell_orders()[:4])
    return render_template(
        "index.html",
        active_page="home",
        preview_buys=preview_buys,
        preview_sells=preview_sells,
        analytics=build_analytics(),
    )


@app.route("/orderbook")
def orderbook():
    return render_template(
        "orderbook.html",
        active_page="orderbook",
        buy_orders=book.sorted_buy_orders(),
        sell_orders=book.sorted_sell_orders(),
    )


@app.route("/place-order", methods=["GET", "POST"])
def place_order():
    errors = []
    form_values = {"order_id": "", "side": "BUY", "price": "", "quantity": ""}

    if request.method == "POST":
        order_id = request.form.get("order_id", "")
        side = request.form.get("side", "").upper()
        price_raw = request.form.get("price", "")
        quantity_raw = request.form.get("quantity", "")

        form_values = {
            "order_id": order_id,
            "side": side or "BUY",
            "price": price_raw,
            "quantity": quantity_raw,
        }

        errors, price, quantity = validate_new_order(
            order_id, side, price_raw, quantity_raw
        )

        if not errors:
            new_order = Order(order_id.strip(), side, price, quantity)
            book.add_order(new_order)

            trades = engine.run_matching(book)

            if trades:
                flash(
                    f"Order '{new_order.order_id}' accepted and matched "
                    f"into {len(trades)} trade(s).",
                    "success",
                )
            else:
                flash(
                    f"Order '{new_order.order_id}' accepted and resting in the book.",
                    "success",
                )
            return redirect(url_for("place_order"))

    return render_template(
        "place_order.html",
        active_page="place_order",
        errors=errors,
        form_values=form_values,
    )


@app.route("/trades")
def trades():
    return render_template(
        "trades.html",
        active_page="trades",
        trade_history=engine.sorted_history(),
    )


@app.route("/analytics")
def analytics():
    return render_template(
        "analytics.html",
        active_page="analytics",
        analytics=build_analytics(),
        recent_trades=engine.sorted_history()[:6],
    )


if __name__ == "__main__":
    app.run(debug=True)
