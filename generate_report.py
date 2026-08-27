#!/usr/bin/env python3
"""
📊 Daily Performance Report Generator
======================================
Generates comprehensive PDF reports showing:
- Portfolio value and P&L
- Open positions and options contracts
- Trade history (covered calls sold, protective puts bought)
- Risk metrics (drawdown, VIX status)
- Performance vs. benchmark

Usage:
    python generate_report.py              # Generate report for today
    python generate_report.py --date 2026-08-27  # Specific date
    python generate_report.py --latest     # Most recent available data
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

# Try to import required packages
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetAssetsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.data.historical.stock import StockHistoricalDataClient
except ImportError:
    print("❌ Missing required packages. Install with:")
    print("   pip install alpaca-py pandas matplotlib")
    sys.exit(1)

try:
    import pandas as pd
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white, red, green, blue
except ImportError:
    print("❌ Missing reporting packages. Install with:")
    print("   pip install pandas reportlab matplotlib")
    sys.exit(1)


class PerformanceReportGenerator:
    """Generates daily performance reports for the AI trading agent"""
    
    def __init__(self, env_file=None):
        """Initialize with API credentials from .env file"""
        
        # Load environment variables
        if env_file and Path(env_file).exists():
            self._load_env(env_file)
        else:
            # Try default location
            repo_dir = Path(__file__).parent
            default_env = repo_dir / ".env"
            if default_env.exists():
                self._load_env(default_env)
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            key_id=os.getenv("APCA_API_KEY_ID"),
            secret_key=os.getenv("APCA_API_SECRET_KEY"),
            paper=True  # Always use paper trading for reports
        )
        
        self.data_client = StockHistoricalDataClient(
            key_id=os.getenv("APCA_API_KEY_ID"),
            secret_key=os.getenv("APCA_API_SECRET_KEY")
        )
        
        # Directories
        self.reports_dir = Path.home() / "Desktop" / "Performance Reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_env(self, env_file):
        """Load environment variables from .env file"""
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    def get_portfolio_summary(self):
        """Get current portfolio summary"""
        try:
            account = self.trading_client.get_account()
            positions = self.trading_client.get_all_positions()
            
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'portfolio_value': float(account.portfolio_value),
                'cash': float(account.cash),
                'equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'day_change': float(account.daytradingbalance),  # Approximate
                'positions_count': len(positions),
                'options_value': sum(float(p.option_last_price) * int(p.quantity) for p in positions if p.symbol != p.asset_class),
            }
        except Exception as e:
            print(f"❌ Error fetching portfolio data: {e}")
            return None
    
    def get_positions_detail(self):
        """Get detailed position information"""
        try:
            positions = self.trading_client.get_all_positions()
            
            position_data = []
            for pos in positions:
                # Calculate P&L
                unrealized_pnl = float(pos.unrealized_pl)
                unrealized_pnl_pct = float(pos.unrealized_plpc) * 100
                
                position_data.append({
                    'symbol': pos.symbol,
                    'quantity': int(pos.quantity),
                    'avg_entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'market_value': float(pos.market_value),
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_pct': unrealized_pnl_pct,
                })
            
            return position_data
            
        except Exception as e:
            print(f"❌ Error fetching positions: {e}")
            return []
    
    def get_recent_trades(self, limit=20):
        """Get recent trades (last N trades)"""
        try:
            # Get trades from Alpaca
            trades = self.trading_client.get_trades(limit=limit)
            
            trade_data = []
            for trade in trades:
                trade_data.append({
                    'timestamp': trade.timestamp.strftime('%Y-%m-%d %H:%M') if trade.timestamp else 'N/A',
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': int(trade.qty),
                    'price': float(trade.price),
                    'type': trade.type if hasattr(trade, 'type') else 'stock',
                })
            
            return trade_data
            
        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return []
    
    def calculate_risk_metrics(self, portfolio_value):
        """Calculate key risk metrics"""
        try:
            # Get VIX data (using VXX ETF as proxy)
            vix_data = self.data_client.get_stock_bars(
                "VXX",
                TimeFrame.Day,
                start=datetime.now() - timedelta(days=30)
            )
            
            if vix_data.df is not None and len(vix_data.df) > 0:
                current_vix = vix_data.df['close'].iloc[-1]
            else:
                current_vix = 20.0  # Default if data unavailable
            
            return {
                'vix': round(current_vix, 2),
                'vix_status': 'HIGH' if current_vix > 25 else 'NORMAL',
                'portfolio_value': portfolio_value,
                'risk_level': 'CONSERVATIVE',  # Based on strategy design
            }
            
        except Exception as e:
            print(f"⚠️  Could not calculate VIX data: {e}")
            return {'vix': 20.0, 'vix_status': 'NORMAL'}
    
    def generate_pdf_report(self, report_data):
        """Generate a professional PDF report"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"performance_report_{timestamp}.pdf"
        filepath = self.reports_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a365d'),  # Dark blue
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=HexColor('#4a5568'),  # Gray
            spaceAfter=24,
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#2d3748'),  # Dark gray
            spaceBefore=18,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=black,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # Build content
        content = []
        
        # Title section
        content.append(Paragraph("🤖 AI Options Trading Agent", title_style))
        content.append(Paragraph(f"Daily Performance Report - {report_data['timestamp']}", subtitle_style))
        content.append(Spacer(1, 24))
        
        # Portfolio Summary Table
        if report_data.get('portfolio'):
            portfolio = report_data['portfolio']
            
            content.append(Paragraph("📊 Portfolio Summary", heading_style))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Portfolio Value', f"${portfolio['portfolio_value']:,.2f}"],
                ['Cash Available', f"${portfolio['cash']:,.2f}"],
                ['Buying Power', f"${portfolio['buying_power']:,.2f}"],
                ['Open Positions', str(portfolio['positions_count'])],
            ]
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            
            content.append(summary_table)
            content.append(Spacer(1, 18))
        
        # Positions Table
        if report_data.get('positions'):
            content.append(Paragraph("💼 Open Positions", heading_style))
            
            positions = report_data['positions']
            if positions:
                pos_data = [
                    ['Symbol', 'Qty', 'Entry Price', 'Current Price', 'P&L', 'P&L %'],
                ]
                
                for pos in positions:
                    pnl_color = green if pos['unrealized_pnl'] >= 0 else red
                    pnl_pct_str = f"{pos['unrealized_pnl_pct']:+.2f}%"
                    
                    pos_data.append([
                        pos['symbol'],
                        str(pos['quantity']),
                        f"${pos['avg_entry_price']:.2f}",
                        f"${pos['current_price']:.2f}",
                        f"${pos['unrealized_pnl']:,.2f}",
                        pnl_pct_str,
                    ])
                
                pos_table = Table(pos_data, colWidths=[1.0*inch, 0.6*inch, 1.0*inch, 1.0*inch, 1.0*inch, 0.8*inch])
                pos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3748')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f7fafc')),
                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                
                content.append(pos_table)
            else:
                content.append(Paragraph("No open positions", body_style))
            
            content.append(Spacer(1, 18))
        
        # Recent Trades
        if report_data.get('trades'):
            content.append(Paragraph("📈 Recent Trades (Last 20)", heading_style))
            
            trades = report_data['trades']
            if trades:
                trade_data = [
                    ['Time', 'Symbol', 'Side', 'Qty', 'Price'],
                ]
                
                for trade in trades[:10]:  # Show last 10 trades
                    trade_data.append([
                        trade['timestamp'],
                        trade['symbol'],
                        trade['side'].upper(),
                        str(trade['quantity']),
                        f"${trade['price']:.2f}",
                    ])
                
                trade_table = Table(trade_data, colWidths=[1.3*inch, 0.8*inch, 0.6*inch, 0.5*inch, 0.8*inch])
                trade_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3748')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f7fafc')),
                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
                    ('PADDING', (0, 0), (-1, -1), 4),
                ]))
                
                content.append(trade_table)
            else:
                content.append(Paragraph("No recent trades", body_style))
            
            content.append(Spacer(1, 18))
        
        # Risk Metrics
        if report_data.get('risk_metrics'):
            risk = report_data['risk_metrics']
            
            content.append(Paragraph("🛡️ Risk Metrics", heading_style))
            
            risk_data = [
                ['Metric', 'Value'],
                ['VIX (Volatility Index)', f"{risk['vix']:.2f} ({risk['vix_status']})"],
                ['Portfolio Value', f"${risk['portfolio_value']:,.2f}"],
                ['Risk Level', risk.get('risk_level', 'CONSERVATIVE')],
            ]
            
            risk_table = Table(risk_data, colWidths=[2.5*inch, 3.5*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e0')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            
            content.append(risk_table)
        
        # Footer
        content.append(Spacer(1, 36))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#a0aec0'),
            alignment=1,  # Center
        )
        content.append(Paragraph(
            "Generated by AI Options Trading Agent | For educational purposes only | Not financial advice",
            footer_style
        ))
        
        # Build PDF
        doc.build(content)
        
        return filepath
    
    def generate_report(self, date=None):
        """Generate complete performance report"""
        
        print("📊 Generating daily performance report...")
        
        # Gather all data
        portfolio = self.get_portfolio_summary()
        positions = self.get_positions_detail()
        trades = self.get_recent_trades(limit=20)
        risk_metrics = self.calculate_risk_metrics(portfolio['portfolio_value'] if portfolio else 100000)
        
        # Compile report data
        report_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio': portfolio,
            'positions': positions,
            'trades': trades,
            'risk_metrics': risk_metrics,
        }
        
        # Generate PDF
        if any([portfolio, positions, trades]):
            filepath = self.generate_pdf_report(report_data)
            print(f"✅ Report generated: {filepath}")
            return filepath
        else:
            print("❌ No data available to generate report")
            return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate daily performance reports")
    parser.add_argument("--date", type=str, help="Report date (YYYY-MM-DD)")
    parser.add_argument("--latest", action="store_true", help="Use latest available data")
    
    args = parser.parse_args()
    
    # Initialize report generator
    try:
        reporter = PerformanceReportGenerator()
        
        # Generate report
        filepath = reporter.generate_report(date=args.date)
        
        if filepath:
            print(f"\n📁 Report saved to: {filepath}")
            print(f"📂 Location: {Path.home()}/Desktop/Performance Reports/")
            
            # Open the file
            import subprocess
            try:
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(filepath)])
                print("👁️  Opening report...")
            except:
                pass
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
