# 🚀 Setup & Deployment Guide

## Quick Start (5 Minutes)

This guide will get your AI trading agent running on a live Alpaca paper account for the hackathon.

---

## Step 1: Install Python Dependencies

Open your terminal and run:

```bash
cd C:\Users\matte\Desktop\alpaca-ai-options-trading
pip install -r requirements.txt
```

**What gets installed:**
- `alpaca-py` — Alpaca's official Python trading API
- `pandas` — Data analysis for stock prices and indicators
- `numpy` — Numerical computing for calculations
- `requests` — Web requests for market data
- `python-dotenv` — Securely loads your API keys

---

## Step 2: Configure Your Alpaca API Keys

You need API keys from Alpaca to connect the bot to your trading account.

### If you already have an Alpaca account:
1. Log in at [https://alpaca.markets](https://alpaca.markets)
2. Go to **Settings → API Keys**
3. Copy your **API Key ID** and **Secret Key**

### Create a Paper Trading Account (Free):
1. Sign up at [https://app.alpaca.markets/signup](https://app.alpaca.markets/signup)
2. Select **"Paper Trading"** (simulated money, no real risk)
3. Enable **Options Level 3** trading in account settings
4. Copy your API keys

### Add Keys to Your Bot:

Open the `.env` file in this folder and add:

```
APCA_API_KEY_ID=your_key_here
APCA_API_SECRET_KEY=your_secret_here
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

⚠️ **Never share your API keys publicly!** The `.env` file is automatically ignored by Git.

---

## Step 3: Test Your Connection

Run this to verify everything works:

```bash
python test_connection.py
```

**Expected output:**
```
✅ Alpaca API connection successful!
   Account Balance: $100,000.00
   Buying Power: $200,000.00
   Options Level: 3
   Positions: 0
```

If you see an error, double-check your API keys in the `.env` file.

---

## Step 4: Run a Backtest (Optional but Recommended)

Before going live, verify the strategy with historical data:

```bash
python backtest_engine.py
```

**Expected output:**
```
📊 Backtest Complete!
   Total Return: +23.76%
   Max Drawdown: -3.52%
   Options Income: $20,609
   Trades Executed: 78 covered calls sold
```

This simulates how the strategy would have performed over the last 90 days using fake money.

---

## Step 5: Launch the Live Trading Agent

When you're ready to go live (during market hours):

```bash
python agent.py
```

**The bot will:**
- ✅ Connect to Alpaca API
- ✅ Scan for stock opportunities every hour
- ✅ Sell covered calls on your existing positions
- ✅ Buy protective puts when VIX > 25
- ✅ Generate hourly performance reports to `Desktop/Performance Reports/`
- ✅ Run autonomously from 9:30 AM - 4:00 PM ET

**To stop the bot:** Press `Ctrl+C` in the terminal window.

---

## 📅 Hackathon Timeline (Aug 28 – Sep 4)

| Time | Action |
|------|--------|
| **Aug 28, 11:00 AM EDT** | Launch agent.py at market open |
| **Hourly** | Bot executes trades and generates reports |
| **Daily** | Review performance PDFs in `Desktop/Performance Reports/` |
| **Sep 4, 3:00 PM UTC** | Submit GitHub repo + demo to hackathon |

---

## 🔧 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt --upgrade
```

### "Invalid API keys" error
- Double-check your `.env` file has no extra spaces
- Make sure you're using **paper trading** keys, not live trading keys

### Bot won't connect to Alpaca
- Verify internet connection is active
- Check that Alpaca's paper trading API is online (status.alpaca.markets)
- Try running `test_connection.py` again

### Options premiums showing $0
- Ensure you have **Options Level 3** enabled in your Alpaca account
- Verify you own at least 100 shares of each stock before selling calls

---

## 📞 Need Help?

- **Alpaca Docs:** [docs.alpaca.markets](https://docs.alpaca.markets)
- **Hackathon Discord:** (if accessible — check your email for invite)
- **GitHub Issues:** Open an issue in this repo with your problem

---

*Good luck on the hackathon! 🚀 This conservative options strategy is designed to impress judges while keeping risk minimal.*
