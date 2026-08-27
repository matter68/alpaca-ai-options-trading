#!/usr/bin/env python3
"""
🔍 FLASH TEST SUITE — Alpaca AI Options Trading Agent
======================================================
Tests every chunk of code before hackathon launch (Aug 28).
Run this to verify everything works BEFORE the real market day.

Chunks tested:
1. Imports & Dependencies
2. Risk Manager Logic
3. Options Engine Logic  
4. Market Scanner Logic
5. Agent Integration (mock data)
6. Deploy Script Syntax
7. Report Generator Syntax
"""

import sys
import os
from pathlib import Path

# Add repo to path
REPO_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(REPO_DIR))

# Results tracking
results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test(name, func):
    """Run a test and record result."""
    try:
        func()
        results['passed'].append(name)
        print(f"  ✅ PASS: {name}")
        return True
    except AssertionError as e:
        results['failed'].append((name, str(e)))
        print(f"  ❌ FAIL: {name} — {e}")
        return False
    except Exception as e:
        results['failed'].append((name, f"{type(e).__name__}: {e}"))
        print(f"  ❌ ERROR: {name} — {type(e).__name__}: {e}")
        return False

def warn(name, msg):
    """Record a warning."""
    results['warnings'].append((name, msg))
    print(f"  ⚠️  WARN: {name} — {msg}")


# ============================================================
# CHUNK 1: Imports & Dependencies
# ============================================================
print("\n" + "="*60)
print("CHUNK 1: IMPORTS & DEPENDENCIES")
print("="*60)

def test_import_risk_manager():
    from risk_manager import RiskManager
    assert RiskManager is not None, "RiskManager class not found"

test("Import risk_manager.py", test_import_risk_manager)

def test_import_options_engine():
    from options_engine import OptionsEngine
    assert OptionsEngine is not None, "OptionsEngine class not found"

test("Import options_engine.py", test_import_options_engine)

def test_import_market_scanner():
    from market_scanner import MarketScanner
    assert MarketScanner is not None, "MarketScanner class not found"

test("Import market_scanner.py", test_import_market_scanner)

def test_import_agent():
    from agent import TradingAgent
    assert TradingAgent is not None, "TradingAgent class not found"

test("Import agent.py", test_import_agent)

def test_env_file_exists():
    env_path = REPO_DIR / ".env"
    assert env_path.exists(), f".env file missing at {env_path}"

test(".env file exists", test_env_file_exists)

def test_api_keys_loaded():
    from dotenv import load_dotenv
    load_dotenv(REPO_DIR / ".env")
    api_key = os.getenv('ALPACA_API_KEY', '')
    secret_key = os.getenv('ALPACA_SECRET_KEY', '')
    assert len(api_key) > 10, "ALPACA_API_KEY too short or empty"
    assert len(secret_key) > 10, "ALPACA_SECRET_KEY too short or empty"

test("API keys loaded from .env", test_api_keys_loaded)


# ============================================================
# CHUNK 2: Risk Manager Logic
# ============================================================
print("\n" + "="*60)
print("CHUNK 2: RISK MANAGER LOGIC")
print("="*60)

def test_risk_manager_init():
    from risk_manager import RiskManager
    rm = RiskManager(initial_capital=100000)
    assert rm.initial_capital == 100000, f"Expected 100000, got {rm.initial_capital}"
    assert rm.MAX_POSITIONS == 6, f"Expected MAX_POSITIONS=6, got {rm.MAX_POSITIONS}"
    assert rm.MAX_CAPITAL_PER_POSITION_PCT == 0.25, "Position cap should be 25%"

test("RiskManager initialization", test_risk_manager_init)

def test_position_limit():
    from risk_manager import RiskManager
    rm = RiskManager(100000)
    
    # Should allow adding positions when under limit
    assert rm.check_position_limit([]), "Should allow first position"
    assert rm.check_position_limit([{'asset_class': 'us_equity'}] * 5), "Should allow up to 6 positions"
    assert not rm.check_position_limit([{'asset_class': 'us_equity'}] * 6), "Should block 7th position"

test("Position limit enforcement", test_position_limit)

def test_capital_limit():
    from risk_manager import RiskManager
    rm = RiskManager(100000)
    
    # $25K position on $100K portfolio = exactly at limit (25%)
    assert rm.check_capital_limit(25000, 100000), "Should allow exactly 25% position"
    # $26K = over limit
    assert not rm.check_capital_limit(26000, 100000), "Should block >25% position"

test("Capital per position limit", test_capital_limit)

def test_stop_loss():
    from risk_manager import RiskManager
    rm = RiskManager(100000)
    
    # Entry $100, current $95 (-5%) — should be safe (>= -8%)
    assert rm.check_stop_loss(100, 95), "Should allow -5% loss"
    # Entry $100, current $91 (-9%) — should NOT be safe (< -8%)
    assert not rm.check_stop_loss(100, 91), "Should block -9% loss (stop hit)"

test("Stop loss check", test_stop_loss)

def test_premium_limit():
    from risk_manager import RiskManager
    rm = RiskManager(100000)
    
    # Daily limit = 2% of $100K = $2,000
    assert rm.check_premium_limit(500, 100000), "Should allow $500 premium"
    assert not rm.check_premium_limit(3000, 100000), "Should block $3K premium (over $2K limit)"

test("Premium daily limit", test_premium_limit)

def test_covered_call_validation():
    from risk_manager import RiskManager
    rm = RiskManager(100000)
    
    # Valid position: 200 shares, $10B+ market cap, above stop loss
    valid_position = {
        'symbol': 'AAPL',
        'qty': 200,
        'avg_entry_price': 190.0,
        'current_price': 195.0,
        'market_cap': 3e12,
        'strike_price': 200.0
    }
    is_valid, reason = rm.validate_covered_call(valid_position, 100000)
    assert is_valid, f"Should validate: {reason}"

test("Covered call validation (valid)", test_covered_call_validation)

def test_covered_call_rejects_insufficient_shares():
    from risk_manager import RiskManager
    rm = RiskManager(100000)
    
    # Invalid: only 50 shares (need 100 for 1 contract)
    invalid_position = {
        'symbol': 'AAPL',
        'qty': 50,
        'avg_entry_price': 190.0,
        'current_price': 195.0,
        'market_cap': 3e12,
        'strike_price': 200.0
    }
    is_valid, reason = rm.validate_covered_call(invalid_position, 100000)
    assert not is_valid, "Should reject <100 shares"

test("Covered call rejects <100 shares", test_covered_call_rejects_insufficient_shares)


# ============================================================
# CHUNK 3: Options Engine Logic
# ============================================================
print("\n" + "="*60)
print("CHUNK 3: OPTIONS ENGINE LOGIC")
print("="*60)

def test_options_engine_init():
    from options_engine import OptionsEngine
    oe = OptionsEngine()
    assert oe.trade_journal == [], "Trade journal should start empty"

test("OptionsEngine initialization", test_options_engine_init)

def test_covered_call_analysis_vix_filter():
    from options_engine import OptionsEngine
    oe = OptionsEngine()
    
    position = {
        'symbol': 'AAPL',
        'qty': 200,
        'avg_entry_price': 190.0,
        'current_price': 195.0,
        'market_cap': 3e12
    }
    
    # VIX too low (<15) — should NOT sell covered calls
    conditions_low_vix = {'vix': 12, 'trend': 'neutral'}
    result = oe.analyze_covered_call_opportunity(position, conditions_low_vix)
    assert result is None, "Should not sell calls when VIX < 15"
    
    # VIX moderate (15-25), neutral trend — SHOULD sell
    conditions_ok = {'vix': 20, 'trend': 'neutral'}
    result = oe.analyze_covered_call_opportunity(position, conditions_ok)
    assert result is not None, "Should sell calls when VIX=20, trend=neutral"
    assert result['contracts_to_sell'] == 2, f"Expected 2 contracts for 200 shares, got {result['contracts_to_sell']}"

test("Covered call VIX filter", test_covered_call_analysis_vix_filter)

def test_covered_call_strong_uptrend_reject():
    from options_engine import OptionsEngine
    oe = OptionsEngine()
    
    position = {
        'symbol': 'NVDA',
        'qty': 200,
        'avg_entry_price': 450.0,
        'current_price': 500.0,
        'market_cap': 2e12
    }
    
    # Strong uptrend — should NOT sell (don't want to miss gains)
    conditions = {'vix': 20, 'trend': 'strong_uptrend'}
    result = oe.analyze_covered_call_opportunity(position, conditions)
    assert result is None, "Should not sell calls in strong uptrend"

test("Covered call rejects strong uptrend", test_covered_call_strong_uptrend_reject)

def test_protective_put_vix_trigger():
    from options_engine import OptionsEngine
    oe = OptionsEngine()
    
    position = {
        'symbol': 'AAPL',
        'qty': 200,
        'avg_entry_price': 190.0,
        'current_price': 195.0,
        'market_cap': 3e12
    }
    
    # VIX > 25 — should buy protective puts
    conditions = {'vix': 30, 'trend': 'neutral'}
    result = oe.analyze_protective_put_opportunity(position, conditions)
    assert result is not None, "Should buy puts when VIX > 25"

test("Protective put triggered by high VIX", test_protective_put_vix_trigger)

def test_protective_put_gain_lock():
    from options_engine import OptionsEngine
    oe = OptionsEngine()
    
    position = {
        'symbol': 'MSFT',
        'qty': 100,
        'avg_entry_price': 400.0,
        'current_price': 500.0,  # Up 25%
        'market_cap': 3e12
    }
    
    # Position up 25% — should buy puts to lock gains (even with moderate VIX)
    conditions = {'vix': 20, 'trend': 'neutral'}
    result = oe.analyze_protective_put_opportunity(position, conditions)
    assert result is not None, "Should buy puts when position up >15%"

test("Protective put locks in gains", test_protective_put_gain_lock)

def test_trade_journal_logging():
    from options_engine import OptionsEngine
    oe = OptionsEngine()
    
    trade = {
        'action': 'sell_covered_call',
        'symbol': 'AAPL',
        'strike_price': 200.0,
        'premium': 1.50
    }
    oe.log_trade(trade)
    
    assert len(oe.trade_journal) == 1, "Should have 1 trade in journal"
    assert oe.trade_journal[0]['symbol'] == 'AAPL', "Journal should record symbol"

test("Trade journal logging", test_trade_journal_logging)


# ============================================================
# CHUNK 4: Market Scanner Logic
# ============================================================
print("\n" + "="*60)
print("CHUNK 4: MARKET SCANNER LOGIC")
print("="*60)

def test_scanner_init():
    from market_scanner import MarketScanner
    ms = MarketScanner()
    assert len(ms.watchlist) > 0, "Watchlist should not be empty"
    assert 'AAPL' in ms.watchlist, "AAPL should be in watchlist"

test("MarketScanner initialization", test_scanner_init)

def test_market_conditions_extraction():
    from market_scanner import MarketScanner
    ms = MarketScanner()
    
    data = {
        'AAPL': {'vix': 18, 'trend': 'uptrend'},
        'MSFT': {'vix': 18, 'trend': 'strong_uptrend'}
    }
    conditions = ms.get_market_conditions(data)
    
    assert conditions['vix'] == 18, f"Expected VIX=18, got {conditions['vix']}"
    assert conditions['trend'] in ['uptrend', 'strong_uptrend'], \
        f"Trend should be bullish, got {conditions['trend']}"

test("Market conditions extraction", test_market_conditions_extraction)

def test_scoring_logic():
    from market_scanner import MarketScanner
    ms = MarketScanner()
    
    # Bullish stock: price above MAs, high volume, uptrend
    bullish_data = {
        'price': 200, 'ma_20': 195, 'ma_50': 190,
        'volume': 60e6, 'avg_volume': 50e6,
        'vix': 18, 'trend': 'uptrend'
    }
    score = ms._calculate_score(bullish_data)
    assert score >= 70, f"Bullish stock should score high, got {score}"
    
    # Bearish stock: price below MAs, declining trend
    bearish_data = {
        'price': 180, 'ma_20': 195, 'ma_50': 190,
        'volume': 30e6, 'avg_volume': 50e6,
        'vix': 35, 'trend': 'declining'
    }
    score = ms._calculate_score(bearish_data)
    assert score < 40, f"Bearish stock should score low, got {score}"

test("Stock scoring logic", test_scoring_logic)


# ============================================================
# CHUNK 5: Agent Integration (Mock Data)
# ============================================================
print("\n" + "="*60)
print("CHUNK 5: AGENT INTEGRATION")
print("="*60)

def test_agent_instantiation():
    from agent import TradingAgent
    agent = TradingAgent()
    
    assert agent.risk_manager is not None, "RiskManager should be initialized"
    assert agent.options_engine is not None, "OptionsEngine should be initialized"
    assert agent.scanner is not None, "MarketScanner should be initialized"

test("TradingAgent instantiation", test_agent_instantiation)

def test_get_account_info():
    from agent import TradingAgent
    agent = TradingAgent()
    
    info = agent.get_account_info()
    assert 'portfolio_value' in info, "Account info missing portfolio_value"
    assert info['status'] == 'ACTIVE', f"Expected ACTIVE status, got {info['status']}"

test("get_account_info returns valid data", test_get_account_info)

def test_full_cycle_with_mock_data():
    """Test a complete agent cycle using mock positions."""
    from agent import TradingAgent
    
    agent = TradingAgent()
    
    # Mock get_positions to return test data
    original_get_positions = agent.get_positions
    agent.get_positions = lambda: [
        {
            'symbol': 'AAPL',
            'qty': 200,
            'avg_entry_price': 190.0,
            'current_price': 195.0,
            'market_cap': 3e12
        }
    ]
    
    # Mock get_account_info
    agent.get_account_info = lambda: {
        'portfolio_value': 100000.0,
        'buying_power': 200000.0,
        'status': 'ACTIVE'
    }
    
    # Run one cycle — should not crash
    try:
        agent.run_cycle()
    except Exception as e:
        raise AssertionError(f"Agent cycle crashed: {e}")

test("Full agent cycle with mock data", test_full_cycle_with_mock_data)


# ============================================================
# CHUNK 6: Deploy Script Syntax
# ============================================================
print("\n" + "="*60)
print("CHUNK 6: DEPLOY SCRIPT")
print("="*60)

def test_deploy_syntax():
    import py_compile
    deploy_path = REPO_DIR / "deploy.py"
    assert deploy_path.exists(), f"deploy.py not found at {deploy_path}"
    py_compile.compile(str(deploy_path), doraise=True)

test("deploy.py compiles without syntax errors", test_deploy_syntax)


# ============================================================
# CHUNK 7: Report Generator Syntax
# ============================================================
print("\n" + "="*60)
print("CHUNK 7: REPORT GENERATOR")
print("="*60)

def test_report_syntax():
    import py_compile
    report_path = REPO_DIR / "generate_report.py"
    assert report_path.exists(), f"generate_report.py not found at {report_path}"
    py_compile.compile(str(report_path), doraise=True)

test("generate_report.py compiles without syntax errors", test_report_syntax)


# ============================================================
# CHUNK 8: Auto Script Syntax
# ============================================================
print("\n" + "="*60)
print("CHUNK 8: AUTO EXECUTION SCRIPT")
print("="*60)

def test_auto_script_syntax():
    import py_compile
    auto_path = REPO_DIR / "hackathon_auto.py"
    assert auto_path.exists(), f"hackathon_auto.py not found at {auto_path}"
    py_compile.compile(str(auto_path), doraise=True)

test("hackathon_auto.py compiles without syntax errors", test_auto_script_syntax)


# ============================================================
# CHUNK 9: Backtest Engine (Sanity Check)
# ============================================================
print("\n" + "="*60)
print("CHUNK 9: BACKTEST ENGINE")
print("="*60)

def test_backtest_imports():
    import py_compile
    bt_path = REPO_DIR / "backtest_engine.py"
    assert bt_path.exists(), f"backtest_engine.py not found at {bt_path}"
    py_compile.compile(str(bt_path), doraise=True)

test("backtest_engine.py compiles without syntax errors", test_backtest_imports)


# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "="*60)
print("📊 FLASH TEST RESULTS")
print("="*60)

total = len(results['passed']) + len(results['failed'])
pass_rate = (len(results['passed']) / total * 100) if total > 0 else 0

print(f"\n✅ Passed: {len(results['passed'])}/{total}")
print(f"❌ Failed: {len(results['failed'])}/{total}")
print(f"⚠️  Warnings: {len(results['warnings'])}")
print(f"📈 Pass Rate: {pass_rate:.0f}%")

if results['failed']:
    print("\n--- FAILURES ---")
    for name, reason in results['failed']:
        print(f"  ❌ {name}: {reason}")

if results['warnings']:
    print("\n--- WARNINGS ---")
    for name, msg in results['warnings']:
        print(f"  ⚠️  {name}: {msg}")

print()

# Save results to file for cronjob to read
results_path = REPO_DIR / "flash_test_results.json"
with open(results_path, 'w') as f:
    import json
    json.dump({
        'passed': len(results['passed']),
        'failed': len(results['failed']),
        'warnings': len(results['warnings']),
        'pass_rate': pass_rate,
        'failures': results['failed'],
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }, f, indent=2)

print(f"📁 Results saved to: {results_path}")

# Exit with error code if any failures
if results['failed']:
    print("\n⚠️  FLASH TESTS FAILED — DO NOT LAUNCH ON AUG 28 UNTIL FIXED!")
    sys.exit(1)
else:
    print("\n🎉 ALL FLASH TESTS PASSED — READY FOR HACKATHON LAUNCH!")
    sys.exit(0)
