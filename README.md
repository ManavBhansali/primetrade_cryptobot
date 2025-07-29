Delta Exchange India Testnet Trading Bot

A Python-based simplified crypto futures trading bot for the Delta Exchange India testnet. This bot enables placing market, limit, and stop loss orders with secure API authentication and includes a user-friendly Tkinter GUI for easy interaction.

Features:- 

  1. Connects to Delta Exchange India Testnet API (https://cdn-ind.testnet.deltaex.org/v2) with authenticated REST calls.

  2. Supports market_order, limit_order, and stop_order types.

  3. Secure HMAC-SHA256 signature implementation following Delta’s v2 API specs.

  4. User inputs API credentials, product ID, order type, quantity, price, and stop loss via a GUI.

  5. Logs API requests and responses to assist with debugging and auditing (logs/bot.log).

  6. Displays detailed order execution confirmation, including prices, order ID, timestamps (converted to IST), and status.

Prerequisites:-

  1. Python 3.8 or above

  2. requests library (pip install requests)

  3. Access to Delta Exchange India testnet API key and secret (from your testnet account)

  4. Knowledge of valid product_ids via the testnet /v2/products endpoint

Installation and Usage:-

  Clone or download this repository.

Install dependencies:

bash
pip install requests

Run the bot:

  bash
  python bot.py

  Fill in your API Key, API Secret, Product ID, and order details in the GUI and submit to place orders on the testnet.

Notes:-

  1. Make sure your API keys have the necessary permissions and your IP address is whitelisted if applicable.

  2. The timestamp used for signing requires accurate system clock synchronization.

  3. Use the testnet endpoint only for testing; do not use live funds.

Project Structure:-

  1. bot.py — Main script including API interaction and GUI.

  2. logs/bot.log — Log file recording the bot’s activities.

  3. Other files as needed for modularization.
