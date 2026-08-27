"""
Market Scanner — Scans for stock opportunities using momentum criteria.
Mirrors the same screening logic as your existing autotrader v5.
Filters for quality stocks suitable for options trading.
"""


class MarketScanner:
    """Scans market for stocks meeting momentum and quality criteria."""

    def __init__(self, watchlist=None):
        # Default watchlist of liquid, options-enabled stocks
        self.watchlist = watchlist or [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD',
            'DIS', 'BAC', 'XOM', 'CVX', 'PFE'
        ]

    def scan_market(self, market_data):
        """
        Scan watchlist and return ranked opportunities.
        
        Args:
            market_data: dict mapping symbol -> {price, volume, vix, trend, ...}
        
        Returns:
            list of dicts sorted by score (highest first)
        """
        candidates = []

        for symbol in self.watchlist:
            data = market_data.get(symbol)
            if not data:
                continue

            score = self._calculate_score(data)
            
            # Only include stocks that meet minimum criteria
            if score >= 40 and data.get('market_cap', 0) / 1e9 >= 10:
                candidates.append({
                    'symbol': symbol,
                    'score': score,
                    'current_price': data.get('price', 0),
                    'volume': data.get('volume', 0),
                    'vix': data.get('vix', 25),
                    'trend': data.get('trend', 'neutral'),
                    'market_cap': data.get('market_cap', 0)
                })

        # Sort by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:10]  # Return top 10 opportunities

    def _calculate_score(self, data):
        """
        Calculate a momentum/quality score (0-100).
        
        Scoring criteria mirrors autotrader v5 approach:
        - Price relative to moving averages
        - Volume confirmation
        - Trend direction
        - Volatility context
        """
        price = data.get('price', 0)
        ma_20 = data.get('ma_20', price)
        ma_50 = data.get('ma_50', price)
        volume = data.get('volume', 0)
        avg_volume = data.get('avg_volume', volume)
        vix = data.get('vix', 25)

        score = 50  # Start at neutral baseline

        # Price above moving averages (bullish signal)
        if price > ma_20:
            score += 10
        if price > ma_50:
            score += 10

        # Volume confirmation (above average = interest)
        if avg_volume > 0 and volume / avg_volume > 1.2:
            score += 5

        # Trend context
        trend = data.get('trend', 'neutral')
        if trend == 'strong_uptrend':
            score += 10
        elif trend == 'uptrend':
            score += 5
        elif trend == 'declining':
            score -= 10

        # VIX context (lower = better for covered calls)
        if vix < 20:
            score += 5
        elif vix > 30:
            score -= 5

        return max(0, min(100, score))

    def get_market_conditions(self, market_data):
        """Extract overall market conditions from data."""
        if not market_data:
            return {'vix': 25, 'trend': 'neutral', 'volatility': 'moderate'}

        # Get VIX from first available source or default
        vix = None
        for symbol, data in market_data.items():
            if 'vix' in data:
                vix = data['vix']
                break
        
        if vix is None:
            vix = 25  # Default moderate VIX

        # Determine overall trend from watchlist
        uptrends = sum(1 for d in market_data.values() 
                      if d.get('trend') in ['strong_uptrend', 'uptrend'])
        downtrends = sum(1 for d in market_data.values() 
                        if d.get('trend') == 'declining')
        
        total = len(market_data)
        if uptrends > total * 0.6:
            trend = 'strong_uptrend'
        elif uptrends > total * 0.4:
            trend = 'uptrend'
        elif downtrends > total * 0.5:
            trend = 'declining'
        else:
            trend = 'neutral'

        # Volatility assessment
        if vix < 15:
            volatility = 'low'
        elif vix < 25:
            volatility = 'moderate'
        elif vix < 35:
            volatility = 'high'
        else:
            volatility = 'very_high'

        return {
            'vix': vix,
            'trend': trend,
            'volatility': volatility
        }
