<<<<<<< HEAD
# Automated EMA 120 Trading Bot – Delta Exchange

A production-grade, highly reliable automated trading platform designed specifically for **Delta Exchange** (supporting **Delta Exchange India**, **Delta Exchange Global**, and **Testnet** environments).

Built with a modern **React (Vite + TypeScript + Tailwind CSS)** dashboard and an independent, resilient **Python (FastAPI + AsyncIO + PyMongo Async API + Pandas)** backend trading engine with strict financial risk controls.

---

## Key Features & Safety Mechanisms

### 1. EMA 120 Strategy Engine
- **Timeframe:** 1 Hour (60m).
- **Indicator:** EMA 120 calculated over historical closed candles.
- **Strict Candle Closure:** Trades are **never** executed on open or unfinished candles. Candle completion timestamps are strictly verified.
- **Deduplication:** Prevents duplicate signals or re-entries on the same closed candle.
- **Signal Conditions:**
  - **BUY (LONG):** Previous closed candle closed $\le \text{EMA 120}$, and the latest closed candle closed $> \text{EMA 120}$.
  - **SELL (SHORT):** Previous closed candle closed $\ge \text{EMA 120}$, and the latest closed candle closed $< \text{EMA 120}$.

### 2. Mandatory Risk Controls
- **Strict One Open Position Rule:** The bot will **NEVER** open multiple simultaneous positions. Before executing an entry, it validates:
  1. Active position on Delta Exchange
  2. Pending entry/protective orders
  3. MongoDB atomic position lock
- **Maximum 2 Trades Per Day:** Enforced atomically via MongoDB `$inc` and day check. Once 2 positions have been opened in the configured trading day (default timezone: `Asia/Kolkata`), all new entries are locked until the next day's 00:00:00 reset.
- **Automated Take Profit & Stop Loss:**
  - **BUY:** Target = Filled Entry $+ 1500$ points, Stop Loss = Filled Entry $- 100$ points.
  - **SELL:** Target = Filled Entry $- 1500$ points, Stop Loss = Filled Entry $+ 100$ points.
  - Placed via exchange-native bracket orders or immediate reduce-only conditional exit orders.
- **Position Sizing:** Default 100% of available margin balance with 25x leverage, rounded down to valid lot step sizes and tested against minimum order sizes.
- **Instant Emergency Stop:** Immediately disables automated trading, cancels all open and bracket orders, and flattens any open position via market order.

### 3. Separation of Concerns
- The backend trading engine runs completely independently of the frontend. Closing or refreshing the browser does **not** stop the bot or interrupt position management.
- State is persistently maintained in MongoDB. Server restarts recover active positions and daily trade counters seamlessly.

### 4. Paper Trading by Default
- Paper trading mode is active by default. It calculates real EMA signals from market candles, simulates order fills, tracks tick-by-tick P&L, records completed trades in MongoDB, and enforces all position limits without risking real capital.
- Switching to **LIVE** trading requires explicit confirmation acknowledgment of futures risk and capital allocation.

---

## Architecture & Project Structure

```
delta-ema-120/
├── backend/
│   ├── app/
│   │   ├── api/                     # REST API routers & WebSocket
│   │   │   ├── account.py           # Balance & margin endpoints
│   │   │   ├── bot.py               # Bot start, stop, emergency-stop
│   │   │   ├── dashboard.py         # Consolidated dashboard overview
│   │   │   ├── exchange.py          # Delta Exchange credentials & tests
│   │   │   ├── logs.py              # Activity logs
│   │   │   ├── positions.py         # Active positions
│   │   │   ├── strategy.py          # Strategy settings
│   │   │   ├── trades.py            # Historical trades & today's trades
│   │   │   └── websocket.py         # Real-time WebSocket (/ws/live)
│   │   ├── models/                  # Pydantic & database schemas
│   │   ├── schemas/                 # Request & response validations
│   │   ├── services/
│   │   │   ├── delta_exchange.py    # Official Delta Exchange REST API client
│   │   │   ├── ema_strategy.py      # EMA 120 crossover calculation engine
│   │   │   ├── market_data.py       # OHLC candles & price feed
│   │   │   ├── order_manager.py     # Paper & Live order placement
│   │   │   ├── position_manager.py  # TP/SL evaluation & P&L calculation
│   │   │   ├── reconciliation.py    # Periodic exchange-database sync
│   │   │   ├── risk_manager.py      # One-position rule & daily trade limit
│   │   │   ├── trading_engine.py    # Master state machine loop
│   │   │   └── websocket_manager.py # Broadcast live ticker & logs
│   │   ├── utils/
│   │   │   ├── crypto.py            # AES-256 Fernet encryption for API keys
│   │   │   └── datetime_utils.py    # UTC & timezone daily boundary helpers
│   │   ├── workers/
│   │   │   └── trading_worker.py    # Autonomous background task runner
│   │   ├── tests/                   # 23 automated unit & integration tests
│   │   ├── config.py                # Environment configuration
│   │   ├── database.py              # PyMongo AsyncMongoClient connection manager
│   │   └── main.py                  # FastAPI application entrypoint
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AccountOverviewCards.tsx
│   │   │   ├── ActivityLogsCard.tsx
│   │   │   ├── ApiSettingsModal.tsx
│   │   │   ├── BotControlPanel.tsx
│   │   │   ├── LiveConfirmationModal.tsx
│   │   │   ├── LivePositionCard.tsx
│   │   │   ├── Navbar.tsx
│   │   │   ├── StrategySettingsCard.tsx
│   │   │   ├── TradeHistoryTable.tsx
│   │   │   └── TradingChart.tsx
│   │   ├── api.ts                   # Axios REST client
│   │   ├── App.tsx                  # Dashboard layout & WebSocket subscriber
│   │   ├── types.ts                 # TypeScript interfaces
│   │   └── index.css                # Dark theme & styling
│   ├── package.json
│   └── vite.config.ts
├── pytest.ini
└── README.md
```

---

## Installation & Setup

### Prerequisites
- **Python 3.12+**
- **Node.js 18+ & npm**
- **MongoDB** (Local instance or free MongoDB Atlas cluster)

---

### Step 1: Backend Setup

1. Open a terminal and navigate to the project directory:
   ```bash
   cd c:\Users\Lenovo\OneDrive\Desktop\delta-ema-120\backend
   ```

2. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file from `.env.example`:
   ```bash
   copy .env.example .env
   ```

5. Configure your `.env` variables:
   ```env
   # MongoDB Connection
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DATABASE=ema_trading_bot

   # Secret Key for AES-256 Encrypted Credentials
   ENCRYPTION_KEY=D3lt4Em4Tr4d1ngB0tS3cr3tK3y1234567890123456=

   # Delta Exchange Default Environment
   DELTA_ENVIRONMENT=india
   DELTA_API_KEY=
   DELTA_API_SECRET=
   ```

---

### Step 2: MongoDB Atlas Connection (Optional Cloud Setup)

If you are using MongoDB Atlas instead of local MongoDB:
1. Log in to [MongoDB Atlas](https://cloud.mongodb.com/).
2. Create or select a cluster.
3. Under **Database Access**, create a user with read/write permissions.
4. Under **Network Access**, add your current IP address (or `0.0.0.0/0` for cloud deployment).
5. Click **Connect** > **Drivers** > **Python**, copy the connection string, and set it in your `.env`:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=ema_trading_bot
   ```
*Note: If MongoDB is offline, the backend's resilient async fallback store ensures you can still test, backtest, and inspect the dashboard locally without crashes.*

---

### Step 3: Frontend Setup

1. Open a new terminal in the `frontend` folder:
   ```bash
   cd c:\Users\Lenovo\OneDrive\Desktop\delta-ema-120\frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will be accessible at: `http://localhost:5173/`

---

### Step 4: Running the Backend

From the project root:
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/`
- WebSocket Live Feed: `ws://127.0.0.1:8000/ws/live`

---

## Delta Exchange API Setup

1. Log into your Delta Exchange account:
   - For India: [https://india.delta.exchange](https://india.delta.exchange)
   - For Global: [https://delta.exchange](https://delta.exchange)
   - For Testnet: [https://testnet.delta.exchange](https://testnet.delta.exchange)
2. Go to **Settings** > **API Keys** > **Create API Key**.
3. Grant **Read & Write** permissions for Orders and Positions.
4. In the trading dashboard:
   - Click the **API Keys** button on the top right.
   - Select your environment (`Delta Exchange India`, `Global`, or `Testnet`).
   - Enter your API Key and Secret.
   - Click **Test Connection** to verify balance and authentication.
   - Click **Save Credentials**.
   - Your API secret is encrypted using AES-256 Fernet before being stored in MongoDB and is **never** sent back to the browser.

---

## Paper Trading Testing Workflow

1. Start both backend and frontend.
2. Open `http://localhost:5173/` in your browser.
3. Keep the mode selector set to **Paper Trading** (default).
4. Verify your initial paper account balance is displayed ($10,000 USD/USDT).
5. Click **START BOT**. The status badge changes to `RUNNING`.
6. The engine will evaluate completed 1h candles:
   - When a bullish crossover occurs (prev candle $\le$ EMA, latest candle $>$ EMA), a **BUY** order fills at market price.
   - When a bearish crossover occurs (prev candle $\ge$ EMA, latest candle $<$ EMA), a **SELL** order fills at market price.
7. Observe the **Live Trading Position** card update in real time with entry price, TP (+1500), SL (-100), and live unrealized P&L.
8. When the market reaches +1500 or -100 points, the position manager automatically executes the exit, updates the trade status to `CLOSED`, records realized P&L, releases the position lock, and updates the daily trade count.
9. Try testing the **EMERGENCY STOP** button: any active position is flattened immediately and the bot halts all trading.

---

## Live Trading Deployment Guidelines

> [!IMPORTANT]
> **Safety First:** Always run paper trading for at least 72 hours to verify signal logic and exchange connectivity before enabling live trading.

When you are ready for Live Trading:
1. Ensure your Delta Exchange API credentials are authenticated and funded with sufficient margin.
2. In the dashboard, click **Live Trading** on the mode selector.
3. The **Live Confirmation Modal** will appear detailing your position sizing (default 100%), 25x leverage, and risk parameters.
4. Check both acknowledgment checkboxes and click **Confirm & Activate Live Mode**.
5. The bot badge will switch to `🔴 LIVE TRADING`.
6. All orders placed will now be transmitted directly to Delta Exchange with native protective stop-loss and take-profit orders.

---

## Automated Test Suite

A complete test suite of **23 automated tests** is included covering all critical functional and risk requirements.

To run the test suite:
```bash
python -m pytest backend/app/tests -v
```

### Test Coverage Highlights:
- `test_buy_crossover_detection`: Verifies BUY signal when previous $\le$ EMA and latest $>$ EMA.
- `test_sell_crossover_detection`: Verifies SELL signal when previous $\ge$ EMA and latest $<$ EMA.
- `test_insufficient_candles`: Ensures no trades trigger on unfinished or insufficient candle sets.
- `test_no_duplicate_signal_on_same_candle`: Verifies that evaluating the same closed candle twice yields HOLD.
- `test_one_open_position_rule`: Validates that no new position can be opened while a position exists.
- `test_max_two_trades_per_day`: Verifies that exactly 2 trades can open per trading day and the 3rd is blocked.
- `test_correct_buy_target_and_stop_loss`: Verifies +1500 TP and -100 SL on BUY.
- `test_correct_sell_target_and_stop_loss`: Verifies -1500 TP and +100 SL on SELL.
- `test_quantity_calculation`: Verifies proper balance, leverage, and lot step sizing.
- `test_emergency_stop_flattens_and_halts`: Verifies instant emergency market exit and halting.
- `test_paper_trading_order_fill_and_target_exit`: End-to-end simulated trade cycle and P&L accounting.
- `test_paper_trading_stop_loss_exit`: End-to-end stop-loss trigger and accounting.
- `test_restart_recovery_from_database`: Confirms that backend restart preserves open positions and daily trade counters.
- `test_api_credential_encryption`: Confirms AES-256 encryption and masking of credentials.
- `test_delta_signature_format`: Confirms HMAC-SHA256 signature algorithm against Delta Exchange specifications.
- `test_api_endpoints_end_to_end`: Tests all FastAPI REST endpoints.

---

## License & Disclaimer

This software is for educational and algorithmic trading purposes. Trading cryptocurrency derivatives involves substantial risk of loss. Past performance of any trading strategy is not indicative of future results. Never trade with capital you cannot afford to lose.

=======
# delta-120
>>>>>>> 5a2b010ca153a1e9d5417b987f88372e33d25bfc
