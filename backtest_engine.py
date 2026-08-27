"""
Backtest Engine - Pure Options Income Strategy
Starts with $100K in stable stocks, sells covered calls weekly.
Focus: AI-driven options timing and risk management, not stock picking.

Strategy:
- Start with 6 blue-chip stocks (already owned by most investors)
- Sell covered calls every 7 days on each holding
- Only rebalance portfolio when VIX spikes above 30 (buy the dip) or drops below 15 (trim winners)
- Buy protective puts only when VIX > 25 AND stock is declining
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import yfinance as yf
import pandas as pd
import numpy as np

# Add project path
sys.path.insert(0, str(Path(__file__).parent))
from risk_manager import RiskManager
from options_engine import OptionsEngine


class BacktestEngine:
    """Simulates pure options income strategy over historical data."""
    
    def __init__(self):
        self.risk_manager = RiskManager()
        self.options_engine = OptionsEngine()
        
        # === INITIAL PORTFOLIO: 6 stable blue-chip stocks (like a real investor) ===
        # These are companies most people already own - the AI adds value via options
        # Each position has at least 100 shares so we can sell covered calls
        # Total portfolio stays near $100K while allowing options trading
        self.initial_portfolio = {
            'KO':   {'shares': 200,  'market_cap': 260_000_000_000},    # Coca-Cola ~$16K (can sell 2 CC)
            'PG':   {'shares': 150,  'market_cap': 370_000_000_000},    # Procter and Gamble ~$21K (can sell 1 CC)
            'XOM':  {'shares': 150,  'market_cap': 470_000_000_000},    # ExxonMobil ~$22K (can sell 1 CC)
            'JNJ':  {'shares': 100,  'market_cap': 380_000_000_000},    # Johnson and Johnson ~$23K (can sell 1 CC)
            'F':    {'shares': 300,  'market_cap': 50_000_000_000},     # Ford ~$4.5K (can sell 3 CC!)
            'PFE':  {'shares': 300,  'market_cap': 160_000_000_000},    # Pfizer ~$7.8K (can sell 3 CC!)
        }
        
        self.stocks = list(self.initial_portfolio.keys())
        
        # Backtest period (last 90 days)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=90)
        
        # Initial portfolio value
        self.initial_capital = 100_000.0
        
        # Results storage
        self.trades = []
        self.portfolio_history = []
        self.positions = {}  # Track active positions
        self.cumulative_options_pnl = 0.0
    
    def fetch_historical_data(self, symbol):
        """Download historical price data for a stock."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=self.start_date, end=self.end_date)
            
            if df.empty:
                print(f"Warning - No data for {symbol}")
                return None
            
            # Add VIX proxy (using SPY daily volatility rolling window)
            spy = yf.Ticker('SPY')
            spy_df = spy.history(start=self.start_date, end=self.end_date)
            
            if not spy_df.empty:
                spy_returns = spy_df['Close'].pct_change().dropna()
                rolling_vol = spy_returns.rolling(window=20).std() * np.sqrt(252) * 100
                df['vix'] = rolling_vol.bfill()
            else:
                df['vix'] = 20.0
            
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def get_portfolio_value(self):
        """Calculate total portfolio value (stocks + cash + options income)."""
        stock_value = sum(
            pos['qty'] * pos['current_price'] 
            for pos in self.positions.values()
            if not pos.get('closed', False)
        )
        return stock_value + self.cumulative_options_pnl
    
    def initialize_portfolio(self, data_dict):
        """Set up initial portfolio at the start of backtest."""
        print("\n" + "="*70)
        print("INITIAL PORTFOLIO SETUP")
        print("="*70)
        
        for symbol, info in self.initial_portfolio.items():
            if symbol not in data_dict or data_dict[symbol] is None:
                continue
            
            entry_price = data_dict[symbol]['Close'].iloc[0]
            shares = info['shares']
            
            position = {
                'symbol': symbol,
                'qty': shares,
                'avg_entry_price': entry_price,
                'current_price': entry_price,
                'market_cap': info['market_cap'],
                'closed': False,
                'last_options_trade': None,  # Track when we last sold calls
            }
            
            self.positions[symbol] = position
            
            print(f"   {symbol}: {shares} shares @ ${entry_price:.2f}")
        
        initial_value = sum(
            pos['qty'] * pos['avg_entry_price'] 
            for pos in self.positions.values()
        )
        print(f"\nTotal Initial Portfolio Value: ${initial_value:,.2f}")
    
    def run_backtest(self):
        """Run the full backtest."""
        print("="*70)
        print("BACKTESTING PURE OPTIONS INCOME STRATEGY - Last 90 Days")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print("Strategy: Sell covered calls weekly on existing blue-chip holdings")
        print("="*70)
        
        # Fetch all data first
        data_dict = {}
        for symbol in self.stocks:
            data_dict[symbol] = self.fetch_historical_data(symbol)
        
        # Initialize portfolio at day 1
        self.initialize_portfolio(data_dict)
        
        if not self.positions:
            print("ERROR - No positions initialized - check data")
            return
        
        # === SIMULATE DAILY PRICES AND OPTIONS TRADING ===
        # Use AAPL data as the reference timeline (all stocks have same date range)
        ref_data = next(d for d in data_dict.values() if d is not None)
        
        for i in range(1, len(ref_data)):
            current_date = ref_data.index[i]
            
            # Update all position prices
            for symbol, pos in list(self.positions.items()):
                if pos['closed'] or symbol not in data_dict or data_dict[symbol] is None:
                    continue
                
                current_price = data_dict[symbol]['Close'].iloc[i]
                pos['current_price'] = current_price
            
            # Get market VIX proxy from SPY
            spy_data = data_dict.get('SPY')
            vix_current = 20.0
            if spy_data is not None and i < len(spy_data):
                vix_current = spy_data['vix'].iloc[i] if 'vix' in spy_data.columns else 20.0
            
            # === WEEKLY COVERED CALL SELLING (every 7 days) ===
            for symbol, pos in list(self.positions.items()):
                if pos['closed']:
                    continue
                
                last_trade_date = pos.get('last_options_trade')
                days_since_last_trade = (current_date - pd.Timestamp(last_trade_date)).days if last_trade_date else 999
                
                # Only sell covered calls every 7 days minimum
                if days_since_last_trade < 7:
                    continue
                
                # Calculate trend and volatility for this stock
                if i >= 10:
                    ma_10 = data_dict[symbol]['Close'].iloc[max(0, i-10):i+1].mean()
                    current_price = pos['current_price']
                    trend = 'strong_uptrend' if current_price > ma_10 * 1.05 else \
                            'uptrend' if current_price > ma_10 else \
                            'declining' if current_price < ma_10 * 0.95 else 'neutral'
                else:
                    trend = 'neutral'
                
                market_conditions = {
                    'vix': vix_current,
                    'trend': trend,
                    'volatility': data_dict[symbol]['Close'].iloc[max(0, i-20):i+1].pct_change().std() * np.sqrt(252) * 100
                }
                
                # Check for covered call opportunity
                cc_opportunity = self.options_engine.analyze_covered_call_opportunity(pos, market_conditions)
                
                if cc_opportunity:
                    premium_income = cc_opportunity['total_estimated_income']
                    
                    trade = {
                        'date': str(current_date.date()),
                        'type': 'covered_call',
                        'symbol': symbol,
                        'action': f"Sell {cc_opportunity['contracts_to_sell']} CC",
                        'strike_price': cc_opportunity['strike_price'],
                        'premium_income': premium_income,
                        'reasoning': cc_opportunity['reasoning']
                    }
                    
                    self.trades.append(trade)
                    self.cumulative_options_pnl += premium_income
                    pos['last_options_trade'] = current_date
                    print(f"  {symbol}: Sold covered call +${premium_income:.2f} (VIX: {vix_current:.1f})")
                
                # Check for protective put opportunity (only when VIX is high OR declining trend)
                pp_opportunity = self.options_engine.analyze_protective_put_opportunity(pos, market_conditions)
                
                if pp_opportunity and days_since_last_trade >= 14:
                    insurance_cost = pp_opportunity['total_estimated_cost']
                    
                    trade = {
                        'date': str(current_date.date()),
                        'type': 'protective_put',
                        'symbol': symbol,
                        'action': f"Buy {pp_opportunity['contracts_to_buy']} PP",
                        'strike_price': pp_opportunity['strike_price'],
                        'premium_cost': insurance_cost,
                        'reasoning': pp_opportunity['reasoning']
                    }
                    
                    self.trades.append(trade)
                    self.cumulative_options_pnl -= insurance_cost
                    pos['last_options_trade'] = current_date
                    print(f"  {symbol}: Bought protective put -${insurance_cost:.2f} (VIX: {vix_current:.1f})")
            
            # === PORTFOLIO REBALANCING (only on extreme VIX signals) ===
            if i >= 50 and vix_current > 30:
                print(f"\nWARNING - VIX SPIKE DETECTED ({vix_current:.1f}) - Buying the dip")
                # In a real system, we'd add cash to buy more shares here
                # For now, just note it in trades
                self.trades.append({
                    'date': str(current_date.date()),
                    'type': 'market_signal',
                    'symbol': 'PORTFOLIO',
                    'action': f"VIX Spike ({vix_current:.1f}) - Consider buying dip",
                    'premium_income': 0,
                    'reasoning': "Extreme fear in market - opportunity to add positions"
                })
            
            # === RECORD PORTFOLIO VALUE ===
            stock_value = sum(
                pos['qty'] * pos['current_price'] 
                for pos in self.positions.values()
                if not pos.get('closed', False)
            )
            total_equity = stock_value + self.cumulative_options_pnl
            
            self.portfolio_history.append({
                'date': str(current_date.date()),
                'equity': total_equity,
                'change_pct': ((total_equity / self.initial_capital) - 1) * 100
            })
        
        # Calculate performance metrics
        self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate and display backtest results."""
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        
        if not self.portfolio_history:
            print("ERROR - No trades executed - check data or parameters")
            return
        
        df = pd.DataFrame(self.portfolio_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        final_equity = df['equity'].iloc[-1]
        total_return_pct = ((final_equity / self.initial_capital) - 1) * 100
        
        # Max drawdown
        peak = df['equity'].expanding().max()
        drawdown = (df['equity'] - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Win rate
        daily_changes = df['change_pct'].diff().dropna()
        winning_days = (daily_changes > 0).sum()
        losing_days = (daily_changes < 0).sum()
        win_rate = (winning_days / len(daily_changes)) * 100 if len(daily_changes) > 0 else 0
        
        # Trade statistics
        covered_calls = [t for t in self.trades if t['type'] == 'covered_call']
        protective_puts = [t for t in self.trades if t['type'] == 'protective_put']
        
        total_cc_income = sum(t.get('premium_income', 0) for t in covered_calls)
        total_pp_cost = sum(t.get('premium_cost', 0) for t in protective_puts)
        net_options_pnl = total_cc_income - total_pp_cost
        
        print(f"\nPortfolio Performance:")
        print(f"   Initial Capital:    ${self.initial_capital:,.2f}")
        print(f"   Final Equity:       ${final_equity:,.2f}")
        print(f"   Total Return:       {total_return_pct:+.2f}%")
        
        print(f"\nRisk Metrics:")
        print(f"   Max Drawdown:       {max_drawdown:.2f}%")
        print(f"   Win Rate (Daily):   {win_rate:.1f}%")
        
        print(f"\nOptions Activity:")
        print(f"   Covered Calls Sold: {len(covered_calls)} trades")
        print(f"   Protective Puts Bought: {len(protective_puts)} trades")
        print(f"   Total CC Income:    +${total_cc_income:,.2f}")
        print(f"   Total PP Cost:      -${total_pp_cost:,.2f}")
        print(f"   Net Options P&L:    ${net_options_pnl:+,.2f}")
        
        # Save trade journal
        journal_path = Path(__file__).parent / 'backtest_trade_journal.json'
        with open(journal_path, 'w') as f:
            json.dump({
                'backtest_period': f"{self.start_date.date()} to {self.end_date.date()}",
                'initial_capital': self.initial_capital,
                'final_equity': final_equity,
                'total_return_pct': total_return_pct,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'trades': self.trades,
                'portfolio_history': self.portfolio_history
            }, f, indent=2)
        
        print(f"\nTrade journal saved to: {journal_path}")


if __name__ == '__main__':
    engine = BacktestEngine()
    engine.run_backtest()
