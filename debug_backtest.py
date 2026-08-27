"""Debug script — check why positions aren't being created."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from risk_manager import RiskManager
import yfinance as yf

rm = RiskManager()

# Test with AAPL
symbol = 'AAPL'
ticker = yf.Ticker(symbol)
df = ticker.history(start='2026-05-30', end='2026-08-26')

print(f"AAPL data: {len(df)} rows")
if df.empty:
    print("❌ No data!")
else:
    entry_price = df['Close'].iloc[0]
    print(f"Entry price: ${entry_price:.2f}")
    
    max_shares = int(rm.calculate_optimal_position_size(entry_price, 100_000))
    print(f"Max shares by capital calc: {max_shares}")
    
    # Round up to nearest 100
    shares_to_buy = ((max_shares + 99) // 100) * 100
    print(f"After rounding to 100s: {shares_to_buy} shares")
    
    max_affordable = int((100_000 * 0.20) / entry_price)
    print(f"Max affordable (20% cap): {max_affordable} shares")
    
    shares_to_buy = min(shares_to_buy, max_affordable)
    print(f"After applying cap: {shares_to_buy} shares")
    
    position_value = shares_to_buy * entry_price
    print(f"Position value: ${position_value:,.2f}")
    print(f"15% of portfolio: ${100_000 * 0.15:,.2f}")
    print(f"20% of portfolio: ${100_000 * 0.20:,.2f}")
    
    if shares_to_buy < 100:
        print("❌ Too few shares for options (need 100+)")
    else:
        can_add, reason = rm.check_position_limit({})
        print(f"Position limit check: {can_add} - {reason}")
