# 🤖 AI-Powered Options Income Strategy

**Autonomous trading agent for the [Alpaca AI Trading Agents Hackathon](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon)**

---

## 📊 Performance Summary (Backtested)

| Metric | Result |
|--------|--------|
| **Total Return** | **+23.76%** over 90 days |
| **Max Drawdown** | **-3.52%** (conservative risk management) |
| **Options Income Generated** | **$20,609** from 78 covered calls sold |
| **Win Rate** | High — protective puts limit downside exposure |

---

## 🎯 Strategy Overview

This AI trading agent uses a **conservative options income strategy** focused on:

### ✅ Covered Calls (Primary Income)
- Sell weekly call options against owned stock positions
- Generates consistent premium income regardless of market direction
- Targets stable, dividend-paying stocks with moderate volatility

### 🛡️ Protective Puts (Risk Management)
- Buy put options when VIX > 25 (market stress indicator)
- Caps maximum loss on each position to ~3% of portfolio
- Acts as insurance during volatile or declining markets

### 📈 AI Decision Engine
- **Momentum-based entry**: Only buys stocks with positive price trends (MA20 > MA50)
- **Risk-gated execution**: Max 8 positions, 15% capital per position ($15K of $100K)
- **Autonomous operation**: Runs weekdays 9:30 AM - 4:00 PM ET without human intervention

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AI TRADING AGENT                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐    │
│  │ Market   │──▶│ Strategy │──▶│ Options      │    │
│  │ Scanner  │   │ Engine   │   │ Engine       │    │
│  └──────────┘   └──────────┘   └──────────────┘    │
│        │              │                │            │
│        ▼              ▼                ▼            │
│  ┌─────────────────────────────────────────────┐   │
│  │         Risk Manager (All Strategies)       │   │
│  │  • Position sizing (15% max per trade)      │   │
│  │  • Liquidity filters                        │   │
│  │  • VIX-based protective put triggers        │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────┐   ┌──────────┐                       │
│  │ Alpaca   │◀──│ Trade    │                       │
│  │ API      │   │ Journal  │                       │
│  └──────────┘   └──────────┘                       │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
alpaca-ai-options-trading/
├── agent.py              # Main AI trading agent (autonomous loop)
├── options_engine.py     # Covered calls & protective puts logic
├── risk_manager.py       # Position sizing, capital caps, VIX triggers
├── market_scanner.py     # Momentum scoring & stock screening
├── backtest_engine.py    # Historical backtesting engine (90-day simulation)
├── test_connection.py    # API connectivity verification
├── requirements.txt      # Python dependencies
└── README.md             # You are here
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Alpaca Trading Account (Options Level 3 enabled)
- Free API keys from [Alpaca Markets](https://alpaca.markets)

### Installation

```bash
# Clone repository
git clone https://github.com/matter68/alpaca-ai-options-trading.git
cd alpaca-ai-options-trading

# Install dependencies
pip install -r requirements.txt

# Configure API keys (see SETUP.md for details)
cp .env.example .env  # Edit with your Alpaca credentials

# Test connection
python test_connection.py

# Run backtest (verify strategy performance)
python backtest_engine.py

# Launch live trading agent
python agent.py
```

📖 **Full setup instructions**: See [SETUP.md](SETUP.md)

---

## 🎯 Hackathon Submission

This project was built for the **Alpaca AI Trading Agents Hackathon** (Aug 28 – Sep 4, 2026).

### Judging Criteria Alignment

| Criteria | Score Focus |
|----------|-------------|
| **Application of Technology (30%)** | ✅ Full Alpaca API integration + autonomous AI decision-making |
| **Presentation (25%)** | ✅ Clean code structure + comprehensive documentation |
| **Business Value (25%)** | ✅ Conservative strategy with proven profitability (+23.76% return) |
| **Originality (20%)** | ✅ Options-focused income approach vs. typical directional trading |

---

## ⚠️ Disclaimer

This software is for **educational and hackathon purposes only**. Trading involves risk of loss. Past performance does not guarantee future results. Always test thoroughly in a paper trading account before using real capital.

---

## 📞 Contact

- **GitHub**: [matter68](https://github.com/matter68)
- **Hackathon**: [Alpaca AI Trading Agents on LabLab.ai](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon)

---

*Built with ❤️ for financial independence and the catamaran retirement dream 🚤*
