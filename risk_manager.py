"""
Risk Manager — Hard-coded safety gates for the hackathon agent.
These limits CANNOT be overridden by AI decisions.
Built to match conservative trading philosophy: protect capital first.
"""

import json
from datetime import datetime, timedelta


class RiskManager:
    """Enforces hard risk limits on all trading decisions."""

    # === CONFIGURATION (Scaled for $100K portfolio) ===
    MAX_POSITIONS = 6              # Max stocks with options at any time — more concentrated
    MAX_CAPITAL_PER_POSITION_PCT = 0.25  # 25% of portfolio per position (deploy more capital)
    STOP_LOSS_PERCENT = -0.08      # -8% stop loss — cut losses fast before they become catastrophic
    TAKE_PROFIT_PERCENT = 0.10     # +10% take profit — lock gains quickly for consistent wins
    OPTIONS_PREMIUM_DAILY_LIMIT = 0.02  # Max 2% of portfolio in premiums/day
    PUT_SPENDING_DAILY_LIMIT = 0.01     # Max 1% of portfolio in put insurance/day
    MIN_MARKET_CAP_BILLIONS = 10      # Only stocks above $10B market cap
    
    # Scaling factors for larger portfolios
    POSITION_SIZE_MULTIPLIER = 1.0   # Base multiplier (adjust based on liquidity)
    MAX_CONTRACTS_PER_TRADE = 50     # Max contracts per single trade

    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.daily_premium_collected = 0.0
        self.daily_put_spending = 0.0
        self.trade_date = datetime.now().date()

    def get_max_position_value(self, portfolio_value=None):
        """Calculate max position value based on current portfolio size."""
        if portfolio_value is None:
            portfolio_value = self.initial_capital
        return int(portfolio_value * self.MAX_CAPITAL_PER_POSITION_PCT)

    def reset_daily_counters(self, current_date):
        """Reset daily counters if it's a new trading day."""
        if current_date != self.trade_date:
            self.daily_premium_collected = 0.0
            self.daily_put_spending = 0.0
            self.trade_date = current_date

    def check_position_limit(self, portfolio_positions):
        """Check if adding another position would exceed max positions."""
        # Count only equity positions (not options contracts)
        equity_count = sum(1 for p in portfolio_positions 
                          if not p.get('asset_class') == 'us_option')
        return equity_count < self.MAX_POSITIONS

    def check_capital_limit(self, position_value, portfolio_value):
        """Check if a single position exceeds max percentage of portfolio."""
        pct_of_portfolio = position_value / portfolio_value if portfolio_value > 0 else 1.0
        return pct_of_portfolio <= self.MAX_CAPITAL_PER_POSITION_PCT

    def calculate_optimal_position_size(self, stock_price, portfolio_value):
        """Calculate optimal number of shares based on portfolio size and liquidity."""
        max_dollar = self.get_max_position_value(portfolio_value)
        
        # For $100K: 15% = $15K per position (same as before, but now dynamic)
        # Check stock liquidity — don't put more than 5% of daily volume in one trade
        # This prevents slippage on larger positions
        
        max_shares_by_capital = int(max_dollar / stock_price) if stock_price > 0 else 0
        
        # Cap at reasonable number based on average daily volume
        # Assume we won't put more than 2% of avg daily volume in one trade
        # This is a placeholder — real implementation would fetch actual volume data
        max_shares_by_liquidity = min(max_shares_by_capital, 5000)  # Conservative cap
        
        return max_shares_by_liquidity

    def check_liquidity_suitability(self, symbol, position_size_shares):
        """Check if stock is liquid enough for our position size."""
        # For $100K portfolio, we need stocks with:
        # - Average daily volume > 500K shares (for easy entry/exit)
        # - Bid-ask spread < $0.10 (to minimize slippage on larger orders)
        
        # Placeholder — real implementation would check Alpaca market data
        liquid_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD',
            'DIS', 'BAC', 'XOM', 'CVX', 'PFE'
        ]
        
        # For larger positions, we need more liquid stocks
        if position_size_shares > 100:
            return symbol in liquid_stocks
        
        return True  # Smaller positions can use less liquid stocks

    def check_stop_loss(self, entry_price, current_price):
        """Check if current price has hit stop loss threshold."""
        pct_change = (current_price - entry_price) / entry_price
        return pct_change >= self.STOP_LOSS_PERCENT  # Returns True if SAFE

    def check_premium_limit(self, premium_amount, portfolio_value):
        """Check if adding this premium would exceed daily limit."""
        max_daily_premium = portfolio_value * self.OPTIONS_PREMIUM_DAILY_LIMIT
        return (self.daily_premium_collected + premium_amount) <= max_daily_premium

    def check_put_spending_limit(self, put_cost, portfolio_value):
        """Check if buying this put would exceed daily insurance budget."""
        max_daily_puts = portfolio_value * self.PUT_SPENDING_DAILY_LIMIT
        return (self.daily_put_spending + put_cost) <= max_daily_puts

    def check_market_cap(self, market_cap_billions):
        """Check if stock meets minimum market cap requirement."""
        return market_cap_billions >= self.MIN_MARKET_CAP_BILLIONS

    def validate_covered_call(self, position_data, portfolio_value):
        """
        Validate a covered call trade against all risk gates.
        
        Args:
            position_data: dict with keys like 'symbol', 'qty', 'avg_entry_price', 
                          'current_price', 'market_cap'
            portfolio_value: current total account value
        
        Returns:
            tuple: (is_valid, reason)
        """
        # Check 1: Own at least 100 shares (1 contract = 100 shares)
        if position_data.get('qty', 0) < 100:
            return False, "Insufficient shares for covered call (need 100+)"

        # Check 2: Market cap requirement
        market_cap = position_data.get('market_cap', 0) / 1e9  # Convert to billions
        if not self.check_market_cap(market_cap):
            return False, f"Market cap too small ({market_cap:.1f}B < {self.MIN_MARKET_CAP_BILLIONS}B)"

        # Check 3: Stop loss check — don't sell calls on positions about to hit stop
        entry = position_data.get('avg_entry_price', 0)
        current = position_data.get('current_price', 0)
        if not self.check_stop_loss(entry, current):
            return False, f"Position near stop loss ({(current-entry)/entry:.1%} change)"

        # Check 4: Premium limit
        strike = position_data.get('strike_price', 0)
        estimated_premium = (strike - current) * 0.3 + 1.0  # Rough estimate
        if not self.check_premium_limit(estimated_premium, portfolio_value):
            return False, "Daily premium limit reached"

        return True, "All risk gates passed"

    def validate_protective_put(self, position_data, portfolio_value):
        """
        Validate a protective put trade against all risk gates.
        
        Args:
            position_data: dict with keys like 'symbol', 'qty', 'avg_entry_price', 
                          'current_price', 'market_cap'
            portfolio_value: current total account value
        
        Returns:
            tuple: (is_valid, reason)
        """
        # Check 1: Own at least 100 shares
        if position_data.get('qty', 0) < 100:
            return False, "Insufficient shares for protective put (need 100+)"

        # Check 2: Market cap requirement
        market_cap = position_data.get('market_cap', 0) / 1e9
        if not self.check_market_cap(market_cap):
            return False, f"Market cap too small ({market_cap:.1f}B < {self.MIN_MARKET_CAP_BILLIONS}B)"

        # Check 3: Put spending limit
        estimated_put_cost = position_data.get('current_price', 0) * 0.02  # Rough estimate
        if not self.check_put_spending_limit(estimated_put_cost, portfolio_value):
            return False, "Daily put insurance budget reached"

        return True, "All risk gates passed"

    def get_risk_summary(self, portfolio_value):
        """Get a summary of current risk status."""
        return {
            "daily_premium_collected": round(self.daily_premium_collected, 2),
            "daily_premium_limit": round(portfolio_value * self.OPTIONS_PREMIUM_DAILY_LIMIT, 2),
            "daily_put_spending": round(self.daily_put_spending, 2),
            "daily_put_limit": round(portfolio_value * self.PUT_SPENDING_DAILY_LIMIT, 2),
            "trade_date": str(self.trade_date)
        }
