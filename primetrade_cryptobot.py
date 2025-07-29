import tkinter as tk
from tkinter import messagebox
import requests
import time
import hashlib
import hmac
import json
import logging
import os
from collections import OrderedDict
from datetime import datetime, timezone, timedelta

BASE_URL = "https://cdn-ind.testnet.deltaex.org"
ORDER_ENDPOINT = "/v2/orders"

def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logger = logging.getLogger('delta_bot')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('logs/bot.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

class DeltaBot:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret.encode()  # Secret as bytes for HMAC
        self.logger = setup_logger()

    def _headers(self, method, path, data):
        timestamp = str(int(time.time()))  # UNIX seconds
        payload_str = json.dumps(data, separators=(', ', ': ')) if data else ''
        canonical = method + timestamp + path + '' + payload_str
        signature = hmac.new(self.api_secret, canonical.encode(), hashlib.sha256).hexdigest()
        headers = {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "User-Agent": "python-rest-client",
            "Content-Type": "application/json"
        }
        # You can uncomment for debugging the signature if needed.
        # print("Canonical string for signature:", canonical)
        # print("Generated signature:", signature)
        return headers

    def place_order(self, product_id, side, order_type, quantity, price=None, stop_price=None):
        url = BASE_URL + ORDER_ENDPOINT
        order_type_map = {
            "MARKET": "market_order",
            "LIMIT": "limit_order",
            "STOP_MARKET": "stop_order"
        }
        api_order_type = order_type_map.get(order_type.upper())
        if not api_order_type:
            return {"error": f"Unsupported order type: {order_type}"}

        payload = OrderedDict([
            ("product_id", int(product_id)),
            ("side", side.lower()),
            ("size", float(quantity)),
            ("order_type", api_order_type),
            ("post_only", False),
            ("reduce_only", False)
        ])
        if api_order_type == "limit_order":
            if price is None:
                return {"error": "Limit order requires price"}
            payload["limit_price"] = str(price)
        if api_order_type == "stop_order":
            if stop_price is None:
                return {"error": "Stop order requires stop_price"}
            payload["stop_price"] = str(stop_price)

        headers = self._headers("POST", ORDER_ENDPOINT, payload)

        try:
            resp = requests.post(url, headers=headers, json=payload)
            self.logger.info(f"Order API request: {payload}")
            if resp.status_code // 100 != 2:
                self.logger.error(f"Order API error: {resp.status_code} {resp.text}")
                return {"error": resp.text}
            return resp.json()
        except Exception as e:
            self.logger.error(f"Exception placing order: {str(e)}")
            return {"error": str(e)}

def format_order_message(order_response):
    # Print raw for debugging if needed
    # import pprint; pprint.pprint(order_response)
    
    def to_ist(utc_str):
        try:
            dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
            ist = dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
            return ist.strftime('%d %b %Y, %H:%M:%S IST')
        except Exception:
            return utc_str

    # Handle error
    if "error" in order_response:
        return f"❌ Error placing order:\n{order_response['error']}"

    # "result" sometimes present in wrapper; flatten if needed
    data = order_response.get("result", order_response)

    # Attempt to parse fields
    side = data.get("side") or "N/A"
    if side: side = side.capitalize()
    size = data.get("size") or data.get("order_size") or data.get("quantity") or "N/A"
    product_id = data.get("product_id", "N/A")
    # Try symbol, alt keys, fallback to ID
    product_symbol = None
    if "product" in data and "symbol" in data["product"]:
        product_symbol = data["product"]["symbol"]
    elif "symbol" in data:
        product_symbol = data["symbol"]
    elif "product" in data and "name" in data["product"]:
        product_symbol = data["product"]["name"]
    else:
        product_symbol = f"ID {product_id}"
    # Fill/entry price
    avg_fill_price = data.get("average_fill_price") or data.get("fill_price") or data.get("limit_price") or "N/A"
    stop_price = data.get("stop_price", None)
    # Execution or update time
    exec_time = data.get("updated_at") or data.get("created_at") or data.get("timestamp") or "N/A"
    exec_time_formatted = to_ist(exec_time) if exec_time != "N/A" else "N/A"
    order_id = data.get("id", "N/A")
    user_id = data.get("user_id", "N/A")
    ip = data.get("source_ip") or data.get("client_ip") or "N/A"
    success = data.get("success", order_response.get("success", False))
    # Build output
    msg_lines = [
        "✅ Order Confirmation & Details",
        f"- Action: {side}",
        f"- Order Size: {size}",
        f"- Product: {product_symbol} (ID: {product_id})",
        f"- Entry Price: {avg_fill_price}",
        f"- Stop Loss Price: {stop_price if stop_price else 'N/A'}",
        f"- Execution Time (IST): {exec_time_formatted}",
        f"- Order ID: {order_id}",
        f"- User ID: {user_id}",
        # f"- Source IP: {ip}",
        f"- Status: {'Success' if success else 'Failure'}"
    ]
    return "\n".join(msg_lines)

def start_gui():
    root = tk.Tk()
    root.title("Delta India Testnet Trading Bot")

    tk.Label(root, text="API Key:").grid(row=0, column=0, sticky="e")
    api_key_entry = tk.Entry(root, width=40)
    api_key_entry.grid(row=0, column=1)

    tk.Label(root, text="API Secret:").grid(row=1, column=0, sticky="e")
    api_secret_entry = tk.Entry(root, width=40, show="*")
    api_secret_entry.grid(row=1, column=1)

    tk.Label(root, text="Product ID:").grid(row=2, column=0, sticky="e")
    product_id_entry = tk.Entry(root, width=10)
    product_id_entry.grid(row=2, column=1)
    tk.Label(root, text="(Get product IDs from /v2/products API)").grid(row=2, column=2, sticky="w")

    tk.Label(root, text="Side:").grid(row=3, column=0, sticky="e")
    side_var = tk.StringVar(value="buy")
    tk.OptionMenu(root, side_var, "buy", "sell").grid(row=3, column=1, sticky="w")

    tk.Label(root, text="Order Type:").grid(row=4, column=0, sticky="e")
    order_type_var = tk.StringVar(value="MARKET")
    tk.OptionMenu(root, order_type_var, "MARKET", "LIMIT", "STOP_MARKET").grid(row=4, column=1, sticky="w")

    tk.Label(root, text="Quantity:").grid(row=5, column=0, sticky="e")
    quantity_entry = tk.Entry(root, width=10)
    quantity_entry.grid(row=5, column=1, sticky="w")

    tk.Label(root, text="Price (for LIMIT):").grid(row=6, column=0, sticky="e")
    price_entry = tk.Entry(root, width=10)
    price_entry.grid(row=6, column=1, sticky="w")

    tk.Label(root, text="Stop Price (for STOP_MARKET):").grid(row=7, column=0, sticky="e")
    stop_price_entry = tk.Entry(root, width=10)
    stop_price_entry.grid(row=7, column=1, sticky="w")

    def submit():
        api_key = api_key_entry.get().strip()
        api_secret = api_secret_entry.get().strip()
        product_id = product_id_entry.get().strip()
        side = side_var.get()
        order_type = order_type_var.get()
        quantity_s = quantity_entry.get().strip()
        price_s = price_entry.get().strip()
        stop_price_s = stop_price_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showerror("Input Error", "API Key and Secret are required.")
            return
        if not product_id.isdigit():
            messagebox.showerror("Input Error", "Product ID must be an integer.")
            return
        try:
            quantity = float(quantity_s)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a positive number.")
            return

        price = None
        stop_price = None

        if order_type == "LIMIT":
            if not price_s:
                messagebox.showerror("Input Error", "Price is required for LIMIT orders.")
                return
            try:
                price = float(price_s)
                if price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Price must be a positive number.")
                return

        if order_type == "STOP_MARKET":
            if not stop_price_s:
                messagebox.showerror("Input Error", "Stop Price is required for STOP_MARKET orders.")
                return
            try:
                stop_price = float(stop_price_s)
                if stop_price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Stop Price must be a positive number.")
                return

        bot = DeltaBot(api_key, api_secret)
        order_result = bot.place_order(product_id, side, order_type, quantity, price, stop_price)

        if "error" in order_result:
            messagebox.showerror("Order Error", f"Failed to place order:\n{order_result['error']}")
            return

        # Format and show detailed order confirmation
        message_text = format_order_message(order_result)
        messagebox.showinfo("Order Confirmation", message_text)

    tk.Button(root, text="Submit Order", command=submit).grid(row=8, column=0, columnspan=3, pady=10)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
