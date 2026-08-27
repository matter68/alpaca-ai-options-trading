"""
Options Engine — Handles covered calls and protective puts logic.
Built for conservative, income-first options trading.

Strategy 1: Covered Calls (Income Generator)
- Sell call options on stocks you already own
- Collect premium upfront = immediate income
- Strike price 2-5% above current (out-of-the-money)
- Expiration 7-30 days out

Strategy 2: Protective Puts (Crash Insurance)  
- Buy put options on stocks you own when market looks shaky
- Pay small premium = insurance against a crash
- Strike price 3-8% below current (your "floor")
- Expiration 30-60 days out
"""

import json
from datetime import datetime, timedelta


class OptionsEngine:
    """Manages covered calls and protective puts for conservative trading."""

    def __init__(self):
        self.trade_journal = []
        self.daily_summary = {}

    def analyze_covered_call_opportunity(self, position_data, market_conditions):
        """
        Evaluate whether to sell a covered call on an owned stock.
        
        Args:
            position_data: dict with 'symbol', 'qty', 'avg_entry_price', 
                          'current_price', 'market_cap'
            market_conditions: dict with 'vix', 'trend', 'volatility'
        
        Returns:
            dict with decision details or None if not a good opportunity
        """
        current = position_data.get('current_price', 0)
        vix = market_conditions.get('vix', 25)
        trend = market_conditions.get('trend', 'neutral')

        # Only sell covered calls when:
        # - VIX is moderate (not too high, not too low)
        # - Stock is NOT in a steep uptrend (we don't want to miss gains)
        if vix < 15 or trend == 'strong_uptrend':
            return None

        # Calculate strike price: 2-5% above current (out-of-the-money)
        strike_multiplier = 0.03  # Start with 3% OTM
        strike_price = round(current * (1 + strike_multiplier), 2)

        # Expiration: 7-30 days out (weekly contracts preferred for income)
        expiration_days = min(14, max(7, int(vix)))  # Higher VIX = shorter duration
        
        # Calculate optimal number of contracts based on position size
        shares_owned = position_data.get('qty', 0)
        max_contracts = shares_owned // 100  # Each contract = 100 shares
        
        # For $100K portfolio, cap at reasonable number to avoid over-concentration
        # Don't put more than 2 contracts on any single stock (conservative)
        optimal_contracts = min(max_contracts, 2)

        return {
            'action': 'sell_covered_call',
            'symbol': position_data['symbol'],
            'shares_owned': shares_owned,
            'contracts_to_sell': optimal_contracts,
            'strike_price': strike_price,
            'expiration_days': expiration_days,
            'estimated_premium_per_contract': round(current * 0.02, 2),  # ~2% premium estimate per share
            'total_estimated_income': round(current * 0.02 * optimal_contracts * 100, 2),  # Total income
            'reasoning': f"VIX at {vix}, trend is {trend}. "
                        f"Selling {optimal_contracts} OTM call contracts on {shares_owned} shares "
                        f"(strike {strike_multiplier:.0%} above current price)."
        }

    def analyze_protective_put_opportunity(self, position_data, market_conditions):
        """
        Evaluate whether to buy a protective put on an owned stock.
        
        Args:
            position_data: dict with 'symbol', 'qty', 'avg_entry_price', 
                          'current_price', 'market_cap'
            market_conditions: dict with 'vix', 'trend', 'volatility'
        
        Returns:
            dict with decision details or None if not needed
        """
        current = position_data.get('current_price', 0)
        entry = position_data.get('avg_entry_price', 0)
        vix = market_conditions.get('vix', 25)
        trend = market_conditions.get('trend', 'neutral')

        # Only buy protective puts when:
        # - VIX is rising or high (market stress)
        # - Stock is near support level or declining
        # - Position has gained significantly (lock in gains with insurance)
        
        pct_gain = (current - entry) / entry if entry > 0 else 0
        
        should_insure = False
        reason = ""

        if vix > 25:
            should_insure = True
            reason = "VIX elevated — market stress detected"
        elif trend == 'declining':
            should_insure = True
            reason = "Stock in declining trend — insurance recommended"
        elif pct_gain > 0.15:  # Up 15%+? Lock it in with insurance
            should_insure = True
            reason = f"Position up {pct_gain:.0%} — protect gains"

        if not should_insure:
            return None

        # Strike price: 3-8% below current (your "floor")
        strike_multiplier = -0.05  # Start with 5% OTM put
        strike_price = round(current * (1 + strike_multiplier), 2)

        # Expiration: 30-60 days out for meaningful protection window
        expiration_days = 45
        
        # Calculate optimal number of contracts based on position size
        shares_owned = position_data.get('qty', 0)
        max_contracts = shares_owned // 100
        
        # For $100K portfolio, cap at reasonable number to avoid over-concentration
        optimal_contracts = min(max_contracts, 2)

        return {
            'action': 'buy_protective_put',
            'symbol': position_data['symbol'],
            'shares_owned': shares_owned,
            'contracts_to_buy': optimal_contracts,
            'strike_price': strike_price,
            'expiration_days': expiration_days,
            'estimated_premium_per_contract': round(current * 0.015, 2),  # ~1.5% put premium per share
            'total_estimated_cost': round(current * 0.015 * optimal_contracts * 100, 2),  # Total cost
            'reasoning': f"{reason}. Buying {optimal_contracts} put contracts "
                        f"({abs(strike_multiplier):.0%} below current price)."
        }

    def log_trade(self, trade_details, outcome=None):
        """Log a trade decision with full reasoning to the journal."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            **trade_details,
            'outcome': outcome,
            'pnl': None  # Will be filled when position closes
        }
        self.trade_journal.append(entry)

    def generate_daily_summary(self, portfolio_value, daily_trades):
        """Generate end-of-day summary of all options activity."""
        covered_calls = [t for t in daily_trades if t.get('action') == 'sell_covered_call']
        protective_puts = [t for t in daily_trades if t.get('action') == 'buy_protective_put']

        total_premium_collected = sum(t.get('estimated_premium', 0) * t.get('contracts_to_sell', 1) 
                                     for t in covered_calls)
        total_insurance_cost = sum(t.get('estimated_premium', 0) * t.get('contracts_to_buy', 1) 
                                  for t in protective_puts)

        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_trades': len(daily_trades),
            'covered_calls_sold': len(covered_calls),
            'protective_puts_bought': len(protective_puts),
            'premium_collected': round(total_premium_collected, 2),
            'insurance_spent': round(total_insurance_cost, 2),
            'net_options_income': round(total_premium_collected - total_insurance_cost, 2),
            'portfolio_value': round(portfolio_value, 2)
        }

        self.daily_summary = summary
        return summary

    def get_journal(self):
        """Return the complete trade journal."""
        return self.trade_journal
