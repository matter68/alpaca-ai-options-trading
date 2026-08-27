#!/usr/bin/env python3
"""
🚀 Alpaca AI Options Trading - Deployment Script
================================================
Launches the autonomous trading agent with proper environment setup,
market hours detection, error handling, and auto-restart capability.

Usage:
    python deploy.py              # Launch immediately (if market is open)
    python deploy.py --schedule   # Schedule for next market open
    python deploy.py --status     # Check current status
"""

import os
import sys
import subprocess
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
REPO_DIR = Path(__file__).parent.absolute()
LOG_DIR = REPO_DIR / "logs"
REPORTS_DIR = Path.home() / "Desktop" / "Performance Reports"
ENV_FILE = REPO_DIR / ".env"
AGENT_SCRIPT = REPO_DIR / "agent.py"

# Market hours (Eastern Time)
MARKET_OPEN = 9
MARKET_CLOSE = 16  # 4:00 PM ET


def check_environment():
    """Verify all prerequisites are met"""
    print("🔍 Checking environment...")
    
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 11):
        errors.append(f"Python 3.11+ required (you have {sys.version_info.major}.{sys.version_info.minor})")
    
    # Check .env file exists
    if not ENV_FILE.exists():
        errors.append("Missing .env file - copy .env.example and add your Alpaca API keys")
    
    # Check agent.py exists
    if not AGENT_SCRIPT.exists():
        errors.append(f"Agent script not found at {AGENT_SCRIPT}")
    
    # Check required packages
    try:
        import alpaca_trade_api  # or alpaca-py depending on your setup
    except ImportError:
        errors.append("Missing alpaca API package - run: pip install -r requirements.txt")
    
    if errors:
        print("\n❌ Environment check FAILED:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    print("✅ All checks passed!\n")
    return True


def get_eastern_time():
    """Get current time in Eastern timezone (approximate)"""
    from datetime import timezone, timedelta
    
    # EST is UTC-5, EDT is UTC-4
    now_utc = datetime.now(timezone.utc)
    
    # Check if daylight saving time is active (March-November)
    month = now_utc.month
    if 3 <= month <= 10:
        eastern_offset = timedelta(hours=-4)  # EDT
    else:
        eastern_offset = timedelta(hours=-5)  # EST
    
    return now_utc + eastern_offset


def is_market_open():
    """Check if US stock market is currently open (weekdays 9:30 AM - 4:00 PM ET)"""
    et_time = get_eastern_time()
    
    # Check if it's a weekday (Monday=0, Friday=4)
    if et_time.weekday() >= 5:  # Saturday or Sunday
        return False, "Market is closed (weekend)"
    
    current_hour = et_time.hour
    current_minute = et_time.minute
    
    market_open_minutes = MARKET_OPEN * 60 + 30  # 9:30 AM
    market_close_minutes = MARKET_CLOSE * 60     # 4:00 PM
    current_minutes = current_hour * 60 + current_minute
    
    if market_open_minutes <= current_minutes < market_close_minutes:
        return True, f"Market is open ({et_time.strftime('%I:%M %p ET')})"
    else:
        next_open = et_time.replace(hour=MARKET_OPEN, minute=30, second=0, microsecond=0)
        if current_minutes < market_open_minutes:
            wait_minutes = (next_open - et_time).total_seconds() / 60
        else:
            next_open += timedelta(days=1)
            # Skip to next weekday if needed
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)
            wait_minutes = (next_open - et_time).total_seconds() / 60
        
        return False, f"Market is closed. Next open in ~{wait_minutes:.0f} minutes ({next_open.strftime('%I:%M %p ET')})"


def create_log_directory():
    """Create log directory if it doesn't exist"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Log directory: {LOG_DIR}")
    print(f"📊 Reports directory: {REPORTS_DIR}\n")


def launch_agent():
    """Launch the trading agent with proper error handling"""
    
    # Check environment first
    if not check_environment():
        print("\n❌ Cannot launch - fix errors above and try again.")
        return False
    
    create_log_directory()
    
    # Check market hours
    is_open, status_msg = is_market_open()
    print(f"📈 Market Status: {status_msg}")
    
    if not is_open:
        confirm = input("\n⚠️  Market is currently closed. Launch anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Aborted by user.")
            return False
    
    # Prepare log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"agent_{timestamp}.log"
    
    print(f"\n🚀 Launching AI Trading Agent...")
    print(f"📝 Log file: {log_file}")
    print(f"⏹️  Press Ctrl+C to stop the agent\n")
    
    try:
        # Launch agent.py with logging
        process = subprocess.Popen(
            [sys.executable, str(AGENT_SCRIPT)],
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT,
            cwd=str(REPO_DIR)
        )
        
        print(f"✅ Agent started (PID: {process.pid})")
        print(f"📊 Monitoring... Press Ctrl+C to stop\n")
        
        # Keep script running and monitor process
        while process.poll() is None:
            time.sleep(5)  # Check every 5 seconds
            
            # Auto-restart if agent crashes (but not if we stopped it)
            if process.returncode != 0:
                print(f"\n⚠️  Agent crashed with exit code {process.returncode}")
                restart = input("🔄 Restart agent automatically? (y/n): ").strip().lower()
                if restart == 'y':
                    time.sleep(10)  # Wait 10 seconds before restart
                    print("🔄 Restarting agent...")
                    process = subprocess.Popen(
                        [sys.executable, str(AGENT_SCRIPT)],
                        stdout=open(log_file, 'a'),
                        stderr=subprocess.STDOUT,
                        cwd=str(REPO_DIR)
                    )
                    print(f"✅ Agent restarted (PID: {process.pid})\n")
                else:
                    print("❌ Agent stopped.")
                    break
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping agent...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✅ Agent stopped successfully.")
        return True
    
    except Exception as e:
        print(f"\n❌ Error launching agent: {e}")
        return False


def show_status():
    """Show current deployment status"""
    print("="*60)
    print("📊 DEPLOYMENT STATUS")
    print("="*60)
    
    # Check environment
    env_ok = check_environment()
    
    # Market status
    is_open, status_msg = is_market_open()
    print(f"\n📈 Market Status: {status_msg}")
    
    # Recent logs
    if LOG_DIR.exists():
        log_files = sorted(LOG_DIR.glob("agent_*.log"), key=os.path.getmtime)
        if log_files:
            latest_log = log_files[-1]
            print(f"\n📝 Latest Log: {latest_log.name}")
            
            # Show last 5 lines
            try:
                with open(latest_log, 'r') as f:
                    lines = f.readlines()
                    print("\n📄 Last 5 log entries:")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
            except:
                pass
    
    # Recent reports
    if REPORTS_DIR.exists():
        report_files = sorted(REPORTS_DIR.glob("*.pdf"), key=os.path.getmtime)
        if report_files:
            print(f"\n📊 Latest Report: {report_files[-1].name}")
    
    print("\n" + "="*60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Alpaca AI Options Trading - Deployment Script")
    parser.add_argument("--schedule", action="store_true", help="Schedule for next market open")
    parser.add_argument("--status", action="store_true", help="Show current deployment status")
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        return
    
    if args.schedule:
        print("📅 Scheduling agent for next market open...")
        is_open, status_msg = is_market_open()
        
        if not is_open:
            et_time = get_eastern_time()
            next_open = et_time.replace(hour=MARKET_OPEN, minute=30, second=0, microsecond=0)
            
            # Skip to next weekday if needed
            while next_open.weekday() >= 5 or next_open < et_time:
                next_open += timedelta(days=1)
            
            wait_minutes = (next_open - et_time).total_seconds() / 60
            
            print(f"⏰ Next market open: {next_open.strftime('%A, %B %d at %I:%M %p ET')}")
            print(f"⏳ Waiting {wait_minutes:.0f} minutes...")
            
            # Create a simple scheduler (in production, use cron/systemd)
            confirm = input("\n🚀 Start countdown and launch agent? (y/n): ").strip().lower()
            if confirm == 'y':
                print(f"⏱️  Countdown started... Agent will launch at market open.")
                time.sleep(wait_minutes * 60)  # Wait until market opens
                launch_agent()
            else:
                print("❌ Scheduled launch cancelled.")
        else:
            print("✅ Market is already open! Launching immediately...\n")
            launch_agent()
        return
    
    # Default: launch immediately
    launch_agent()


if __name__ == "__main__":
    main()
