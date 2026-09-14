"""
API Routes for Trading Analysis System
Exposes signals, indicators, and analysis via HTTP endpoints
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from app.services import DataFetcher, TechnicalAnalysis, SignalEngine, RiskEngine

# Create a Blueprint for analysis routes
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# Initialize services
fetcher = DataFetcher()
analyzer = TechnicalAnalysis()
engine = SignalEngine()
risk_engine = RiskEngine()

# ============================================================================
# HEALTH CHECK
# ============================================================================

@analysis_bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    Returns: status and timestamp
    """
    return jsonify({
        'status': 'ok',
        'message': 'Trading analysis system is running',
        'timestamp': datetime.now().isoformat()
    }), 200


# ============================================================================
# SIGNALS ENDPOINT
# ============================================================================

@analysis_bp.route('/signals/<string:pair>/<string:timeframe>', methods=['GET'])
def get_signal(pair, timeframe):
    """
    Get trading signal for a forex pair
    
    Args:
        pair: Forex pair (e.g., EURUSD, GBPUSD, USDJPY)
        timeframe: Timeframe (60min, 15min, etc)
    
    Returns:
        JSON with signal type, confidence, entry, stop loss, take profit
    
    Example:
        GET /api/signals/EURUSD/60min
        
    Response:
        {
            "pair": "EURUSD",
            "timeframe": "60min",
            "signal": "LONG",
            "confidence": 0.70,
            "entry": 1.16023,
            "stop_loss": 1.15697,
            "take_profit": 1.16675,
            "risk_reward_ratio": 2.00,
            "reasons": [...],
            "valid": true
        }
    """
    
    try:
        # Validate inputs
        pair = pair.upper()
        timeframe = timeframe.lower()
        
        # Convert timeframe format (user might send "60min" or "1h")
        if timeframe == "1h":
            timeframe = "60min"
        elif timeframe == "4h":
            timeframe = "240min"
        
        # Fetch data
        candles = fetcher.get_intraday_data(pair, timeframe)
        
        # Analyze indicators
        indicators = analyzer.analyze(candles)
        
        # Generate signal
        signal = engine.generate_signal(candles, indicators, pair, timeframe)
        
        # Calculate risk
        signal = risk_engine.calculate_risk(signal, candles, indicators.atr)
        
        # Check if trade is valid
        is_valid = risk_engine.validate_trade(signal)
        
        # Build response
        response = {
            'pair': pair,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'signal': signal.signal_type,
            'confidence': round(signal.confidence, 2),
            'entry': round(signal.entry_price, 6),
            'stop_loss': round(signal.stop_loss, 6),
            'take_profit': round(signal.take_profit, 6),
            'risk_pips': round((signal.entry_price - signal.stop_loss) * 10000, 1) if signal.signal_type == "LONG" else round((signal.stop_loss - signal.entry_price) * 10000, 1),
            'profit_pips': round((signal.take_profit - signal.entry_price) * 10000, 1) if signal.signal_type == "LONG" else round((signal.entry_price - signal.take_profit) * 10000, 1),
            'risk_reward_ratio': round(signal.risk_reward_ratio, 2),
            'position_size_micro_lots': round(risk_engine.get_position_size(signal), 2),
            'reasons': signal.reasons,
            'valid': is_valid,
            'message': 'Trade is VALID' if is_valid else 'Trade does not meet quality criteria'
        }
        
        return jsonify(response), 200
    
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'pair': pair,
            'timeframe': timeframe
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Error generating signal: {str(e)}',
            'pair': pair,
            'timeframe': timeframe
        }), 500


# ============================================================================
# INDICATORS ENDPOINT
# ============================================================================

@analysis_bp.route('/indicators/<string:pair>/<string:timeframe>', methods=['GET'])
def get_indicators(pair, timeframe):
    """
    Get all technical indicators for a forex pair
    
    Args:
        pair: Forex pair (e.g., EURUSD)
        timeframe: Timeframe (60min, 15min, etc)
    
    Returns:
        JSON with all indicator values
    
    Example:
        GET /api/indicators/EURUSD/60min
        
    Response:
        {
            "pair": "EURUSD",
            "timeframe": "60min",
            "rsi": 45.46,
            "macd": -0.000475,
            "macd_signal": -0.000508,
            "ema_9": 1.160271,
            "ema_21": 1.160657,
            "sma_50": 1.161933,
            "sma_200": 1.161761,
            "atr": 0.000884
        }
    """
    
    try:
        pair = pair.upper()
        timeframe = timeframe.lower()
        
        # Fetch data
        candles = fetcher.get_intraday_data(pair, timeframe)
        
        # Analyze indicators
        indicators = analyzer.analyze(candles)
        
        response = {
            'pair': pair,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'indicators': {
                'rsi': round(indicators.rsi, 2) if indicators.rsi else None,
                'macd': round(indicators.macd, 6) if indicators.macd else None,
                'macd_signal': round(indicators.macd_signal, 6) if indicators.macd_signal else None,
                'macd_histogram': round(indicators.macd_histogram, 6) if indicators.macd_histogram else None,
                'ema_9': round(indicators.ema_short, 6) if indicators.ema_short else None,
                'ema_21': round(indicators.ema_long, 6) if indicators.ema_long else None,
                'sma_50': round(indicators.sma_short, 6) if indicators.sma_short else None,
                'sma_200': round(indicators.sma_long, 6) if indicators.sma_long else None,
                'atr': round(indicators.atr, 6) if indicators.atr else None
            }
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error fetching indicators: {str(e)}',
            'pair': pair,
            'timeframe': timeframe
        }), 500


# ============================================================================
# ANALYSIS ENDPOINT (Everything combined)
# ============================================================================

@analysis_bp.route('/analysis/<string:pair>/<string:timeframe>', methods=['GET'])
def get_analysis(pair, timeframe):
    """
    Get complete analysis: indicators + signal + risk management
    
    Args:
        pair: Forex pair (e.g., EURUSD)
        timeframe: Timeframe (60min, 15min, etc)
    
    Returns:
        JSON with indicators, signal, and trading plan
    
    Example:
        GET /api/analysis/EURUSD/60min
    """
    
    try:
        pair = pair.upper()
        timeframe = timeframe.lower()
        
        # Fetch data
        candles = fetcher.get_intraday_data(pair, timeframe)
        
        # Analyze indicators
        indicators = analyzer.analyze(candles)
        
        # Generate signal
        signal = engine.generate_signal(candles, indicators, pair, timeframe)
        
        # Calculate risk
        signal = risk_engine.calculate_risk(signal, candles, indicators.atr)
        
        # Check validity
        is_valid = risk_engine.validate_trade(signal)
        
        # Build comprehensive response
        response = {
            'pair': pair,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'current_price': round(candles[-1].close, 6),
            'indicators': {
                'rsi': round(indicators.rsi, 2),
                'macd': round(indicators.macd, 6),
                'macd_signal': round(indicators.macd_signal, 6),
                'ema_9': round(indicators.ema_short, 6),
                'ema_21': round(indicators.ema_long, 6),
                'sma_50': round(indicators.sma_short, 6),
                'sma_200': round(indicators.sma_long, 6),
                'atr': round(indicators.atr, 6)
            },
            'signal': {
                'type': signal.signal_type,
                'confidence': round(signal.confidence, 2),
                'reasons': signal.reasons
            },
            'trading_plan': {
                'entry': round(signal.entry_price, 6),
                'stop_loss': round(signal.stop_loss, 6),
                'take_profit': round(signal.take_profit, 6),
                'risk_pips': round((signal.entry_price - signal.stop_loss) * 10000, 1) if signal.signal_type == "LONG" else round((signal.stop_loss - signal.entry_price) * 10000, 1),
                'profit_pips': round((signal.take_profit - signal.entry_price) * 10000, 1) if signal.signal_type == "LONG" else round((signal.entry_price - signal.take_profit) * 10000, 1),
                'risk_reward_ratio': round(signal.risk_reward_ratio, 2),
                'position_size_micro_lots': round(risk_engine.get_position_size(signal), 2)
            },
            'trade_validity': {
                'valid': is_valid,
                'message': 'Trade meets all quality criteria' if is_valid else 'Trade does not meet minimum standards'
            }
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error analyzing pair: {str(e)}',
            'pair': pair,
            'timeframe': timeframe
        }), 500


# ============================================================================
# SUPPORTED PAIRS ENDPOINT
# ============================================================================

@analysis_bp.route('/pairs', methods=['GET'])
def get_pairs():
    """
    Get list of supported forex pairs
    
    Returns:
        JSON with supported pairs and timeframes
    """
    
    from app.config import Config
    
    return jsonify({
        'supported_pairs': Config.FOREX_PAIRS,
        'supported_timeframes': ['1min', '5min', '15min', '30min', '60min'],
        'note': 'All pairs support all timeframes'
    }), 200


def register_analysis_routes(app):
    """
    Register analysis routes with Flask app
    
    Usage:
        from app.routes.analysis import register_analysis_routes
        register_analysis_routes(app)
    """
    app.register_blueprint(analysis_bp)