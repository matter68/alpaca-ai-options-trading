"""Quick test — connects to Alpaca and prints account info."""
import os, sys
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                os.environ[key] = val

from agent import TradingAgent

agent = TradingAgent()

print("=== Testing Alpaca Connection ===\n")

try:
    info = agent.get_account_info()
    print(f"Account Status: {info['status']}")
    print(f"Portfolio Value: ${info['portfolio_value']:,.2f}")
    print(f"Buying Power: ${info['buying_power']:,.2f}")
    print(f"Positions Count: {info.get('positions_count', 0)}")
    print("\n✅ API connection successful!")
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    sys.exit(1)
