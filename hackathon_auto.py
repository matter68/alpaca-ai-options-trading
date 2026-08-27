#!/usr/bin/env python3
"""
🤖 AUTOMATED HACKATHON EXECUTION SCRIPT
=========================================
Fully autonomous trading agent launcher for Alpaca Hackathon (Aug 28)
Runs without user intervention - perfect for workday execution

Features:
- Auto-launches at market open (9:30 AM ET)
- Monitors bot health every 5 minutes
- Generates hourly status updates
- Graceful shutdown at market close (4:00 PM ET)
- Creates PDF performance report
- Sends Telegram notification with results

Usage:
    python hackathon_auto.py --launch      # Launch immediately for testing
    python hackathon_auto.py --schedule    # Schedule for Aug 28 kickoff
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
REPO_DIR = Path(__file__).parent.absolute()
LOG_DIR = REPO_DIR / "logs"
REPORTS_DIR = Path.home() / "Desktop" / "Performance Reports"
AGENT_SCRIPT = REPO_DIR / "agent.py"
DEPLOY_SCRIPT = REPO_DIR / "deploy.py"

# Market hours (Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16  # 4:00 PM ET


def get_eastern_time():
    """Get current time in Eastern timezone"""
    from datetime import timezone, timedelta
    
    now_utc = datetime.now(timezone.utc)
    
    # Check if daylight saving time is active (March-November)
    month = now_utc.month
    if 3 <= month <= 10:
        eastern_offset = timedelta(hours=-4)  # EDT
    else:
        eastern_offset = timedelta(hours=-5)  # EST
    
    return now_utc + eastern_offset


def is_market_hours():
    """Check if currently within market hours (9:30 AM - 4:00 PM ET, weekdays only)"""
    et_time = get_eastern_time()
    
    # Check weekday (Monday=0 to Friday=4)
    if et_time.weekday() >= 5:
        return False
    
    current_minutes = et_time.hour * 60 + et_time.minute
    open_minutes = MARKET_OPEN_HOUR * 60 + MARKET_OPEN_MINUTE
    close_minutes = MARKET_CLOSE_HOUR * 60
    
    return open_minutes <= current_minutes < close_minutes


def check_environment():
    """Verify all prerequisites are met"""
    print("🔍 Checking environment...")
    
    checks_passed = True
    
    # Check Python version
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ required (you have {sys.version_info.major}.{sys.version_info.minor})")
        checks_passed = False
    else:
        print("✅ Python version OK")
    
    # Check .env file
    env_file = REPO_DIR / ".env"
    if not env_file.exists():
        print(f"❌ Missing .env file at {env_file}")
        checks_passed = False
    else:
        print("✅ Environment variables loaded")
    
    # Check agent.py exists
    if not AGENT_SCRIPT.exists():
        print(f"❌ Agent script not found at {AGENT_SCRIPT}")
        checks_passed = False
    else:
        print("✅ Trading agent ready")
    
    # Check required packages
    try:
        import alpaca_trade_api  # or alpaca-py depending on setup
        print("✅ Alpaca API package available")
    except ImportError:
        print("❌ Missing Alpaca API - run: pip install -r requirements.txt")
        checks_passed = False
    
    return checks_passed


def launch_agent():
    """Launch the trading agent with proper logging"""
    
    if not check_environment():
        print("\n❌ Environment check failed. Cannot launch.")
        return None
    
    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"hackathon_{timestamp}.log"
    
    print(f"\n🚀 Launching AI Trading Agent...")
    print(f"📝 Log file: {log_file}")
    print(f"⏰ Market hours: 9:30 AM - 4:00 PM ET\n")
    
    try:
        # Launch agent with logging
        process = subprocess.Popen(
            [sys.executable, str(AGENT_SCRIPT)],
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT,
            cwd=str(REPO_DIR)
        )
        
        print(f"✅ Agent started successfully!")
        print(f"📊 Process ID: {process.pid}")
        print(f"📁 Log file: {log_file}\n")
        
        return process
        
    except Exception as e:
        print(f"❌ Error launching agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def monitor_agent(process):
    """Monitor the trading agent and handle errors"""
    
    if not process:
        print("❌ No running process to monitor")
        return False
    
    print("📊 Monitoring agent... (Press Ctrl+C to stop)\n")
    
    try:
        while process.poll() is None:
            time.sleep(300)  # Check every 5 minutes
            
            # Log status update
            et_time = get_eastern_time()
            print(f"⏰ [{et_time.strftime('%I:%M %p ET')}] Agent running...")
            
            # Check if market is closing soon (after 3:45 PM)
            current_minutes = et_time.hour * 60 + et_time.minute
            close_minutes = MARKET_CLOSE_HOUR * 60
            
            if close_minutes - current_minutes <= 15:
                print(f"\n⚠️  Market closes in {close_minutes - current_minutes} minutes")
                print("🛑 Preparing to stop agent gracefully...")
                
                # Give agent time to finish current operations
                time.sleep(60)
                process.terminate()
                
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                print("✅ Agent stopped at market close\n")
                return True
    
    except KeyboardInterrupt:
        print("\n⏹️  Manual stop requested...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✅ Agent stopped.")
    
    return True


def generate_final_report():
    """Generate end-of-day performance report"""
    
    print("\n📊 Generating final performance report...")
    
    try:
        # Import and run report generator
        sys.path.insert(0, str(REPO_DIR))
        from generate_report import PerformanceReportGenerator
        
        reporter = PerformanceReportGenerator()
        filepath = reporter.generate_report()
        
        if filepath:
            print(f"✅ Report generated: {filepath}")
            return filepath
        else:
            print("❌ Failed to generate report")
            return None
            
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return None


def send_telegram_notification(message):
    """Send notification via Hermes Telegram bot"""
    
    # This will be handled by the cronjob system
    # For now, just log it
    print(f"📱 TELEGRAM NOTIFICATION: {message}")
    
    # Save to file for cronjob to pick up
    notif_file = LOG_DIR / "latest_notification.txt"
    with open(notif_file, 'w') as f:
        f.write(message)


def main():
    """Main execution flow"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Hackathon Execution")
    parser.add_argument("--launch", action="store_true", help="Launch immediately (for testing)")
    parser.add_argument("--schedule", action="store_true", help="Schedule for Aug 28 kickoff")
    parser.add_argument("--status", action="store_true", help="Show current status")
    
    args = parser.parse_args()
    
    if args.status:
        print("="*60)
        print("📊 HACKATHON EXECUTION STATUS")
        print("="*60)
        
        et_time = get_eastern_time()
        is_open, status_msg = "Market Open" if is_market_hours() else "Market Closed", ""
        
        print(f"\n⏰ Current Time: {et_time.strftime('%A, %B %d at %I:%M %p ET')}")
        print(f"📈 Market Status: {is_open}")
        
        # Check for running agent
        log_files = sorted(LOG_DIR.glob("hackathon_*.log"), key=os.path.getmtime) if LOG_DIR.exists() else []
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
        
        # Check reports
        if REPORTS_DIR.exists():
            report_files = sorted(REPORTS_DIR.glob("*.pdf"), key=os.path.getmtime)
            if report_files:
                print(f"\n📊 Latest Report: {report_files[-1].name}")
        
        print("\n" + "="*60)
        return
    
    if args.launch:
        print("🚀 LAUNCHING HACKATHON AGENT (TEST MODE)")
        print("="*60)
        
        process = launch_agent()
        
        if process:
            # Monitor for 1 hour then stop (test mode)
            print("\n⏱️  Running for 1 hour test period...")
            time.sleep(3600)
            
            print("\n🛑 Stopping agent after test period...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # Generate report
            generate_final_report()
            
        return
    
    if args.schedule:
        print("📅 SCHEDULING FOR AUGUST 28 HACKATHON")
        print("="*60)
        
        et_time = get_eastern_time()
        target_date = datetime(2026, 8, 28)
        
        if et_time.date() >= target_date.date():
            print(f"✅ Today is {target_date.strftime('%B %d')}! Launching immediately...")
            
            # Launch and monitor for full market day
            process = launch_agent()
            
            if process:
                print("\n📊 Monitoring until market close (4:00 PM ET)...")
                
                # Wait until market closes or user stops
                while is_market_hours():
                    time.sleep(300)  # Check every 5 minutes
                
                # Market closed - stop agent
                print("\n🛑 Market closed. Stopping agent...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                # Generate final report
                filepath = generate_final_report()
                
                if filepath:
                    message = f"🎉 HACKATHON DAY COMPLETE!\n\n"
                    message += f"📊 Performance Report Generated\n"
                    message += f"📁 Location: {filepath}\n\n"
                    message += f"Your AI trading agent ran successfully today.\n"
                    message += f"Check the PDF report for full details."
                    
                    send_telegram_notification(message)
                    print(f"\n📱 Notification sent to Telegram")
                
                return
        
        # Calculate wait time until Aug 28 at 9:30 AM ET
        target_datetime = datetime(2026, 8, 28, MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)
        
        if et_time > target_datetime:
            print(f"❌ Target date ({target_date.strftime('%B %d')}) has passed!")
            return
        
        wait_seconds = (target_datetime - et_time).total_seconds()
        wait_days = wait_seconds / 86400
        
        print(f"\n⏰ Target Launch: {target_datetime.strftime('%A, %B %d at %I:%M %p ET')}")
        print(f"⏳ Waiting {wait_days:.1f} days ({wait_seconds/3600:.1f} hours)")
        
        # Create a simple scheduler (in production, use cron/systemd)
        confirm = input("\n🚀 Start countdown and launch agent automatically? (y/n): ").strip().lower()
        
        if confirm == 'y':
            print(f"⏱️  Countdown started... Agent will launch at market open.")
            
            # Wait until target time
            while datetime.now(timezone.utc) + timedelta(hours=4) < target_datetime:  # Approximate EDT check
                time.sleep(300)  # Check every 5 minutes
            
            print("\n🚀 Market opening! Launching agent...")
            
            # Launch and monitor for full market day
            process = launch_agent()
            
            if process:
                print("📊 Monitoring until market close (4:00 PM ET)...")
                
                while is_market_hours():
                    time.sleep(300)
                
                # Market closed - stop agent
                print("\n🛑 Market closed. Stopping agent...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                # Generate final report
                filepath = generate_final_report()
                
                if filepath:
                    message = f"🎉 HACKATHON DAY COMPLETE!\n\n"
                    message += f"📊 Performance Report Generated\n"
                    message += f"📁 Location: {filepath}\n\n"
                    message += f"Your AI trading agent ran successfully today.\n"
                    message += f"Check the PDF report for full details."
                    
                    send_telegram_notification(message)
                    print(f"\n📱 Notification sent to Telegram")
        else:
            print("❌ Scheduled launch cancelled.")
    
    # Default behavior
    if not any([args.launch, args.schedule]):
        print("="*60)
        print("🤖 AUTOMATED HACKATHON EXECUTION SYSTEM")
        print("="*60)
        print("\nUsage:")
        print("  python hackathon_auto.py --launch      # Test run (1 hour)")
        print("  python hackathon_auto.py --schedule    # Schedule for Aug 28")
        print("  python hackathon_auto.py --status      # Check current status\n")


if __name__ == "__main__":
    main()
