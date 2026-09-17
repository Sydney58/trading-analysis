"""
API Routes for Trading Analysis System - UPDATED
Now supports trading styles, custom account sizes, and dynamic risk management
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from app.services import DataFetcher, TechnicalAnalysis, SignalEngine, RiskEngine
from app.config import Config

# Create a Blueprint for analysis routes
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# Initialize services (will be recreated per request with user parameters)
# Global instances for basic operations
fetcher = DataFetcher()
analyzer = TechnicalAnalysis()
engine = SignalEngine()

# ============================================================================
# HEALTH CHECK
# ============================================================================

@analysis_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Trading analysis system is running',
        'timestamp': datetime.now().isoformat()
    }), 200


# ============================================================================
# TRADING STYLES ENDPOINT
# ============================================================================

@analysis_bp.route('/trading-styles', methods=['GET'])
def get_trading_styles():
    """
    Get all available trading styles
    
    Returns:
        JSON with all trading styles and their properties
    """
    risk_engine = RiskEngine()
    styles = risk_engine.get_all_trading_styles()
    
    return jsonify({
        'trading_styles': styles,
        'default_style': 'day_trading',
        'timestamp': datetime.now().isoformat()
    }), 200


@analysis_bp.route('/trading-styles/<string:style>', methods=['GET'])
def get_trading_style_info(style):
    """
    Get information about a specific trading style
    
    Args:
        style: Trading style key (scalping, day_trading, swing_trading, position_trading)
    
    Returns:
        JSON with style details
    """
    risk_engine = RiskEngine()
    style_info = risk_engine.get_trading_style_info(style)
    
    if not style_info:
        return jsonify({
            'error': f'Trading style "{style}" not found',
            'available_styles': ['scalping', 'day_trading', 'swing_trading', 'position_trading']
        }), 404
    
    return jsonify({
        'style': style,
        'details': style_info,
        'timestamp': datetime.now().isoformat()
    }), 200


# ============================================================================
# SIGNALS ENDPOINT - WITH TRADING STYLE & ACCOUNT SIZE
# ============================================================================

@analysis_bp.route('/signals/<string:pair>/<string:timeframe>', methods=['GET'])
def get_signal(pair, timeframe):
    """
    Get trading signal for a forex pair
    
    Query Parameters:
        trading_style: One of ['scalping', 'day_trading', 'swing_trading', 'position_trading'] (default: day_trading)
        account_size: Account size in USD (default: 10000)
        risk_percentage: Risk per trade as percentage (default: 2.0)
    
    Args:
        pair: Forex pair (e.g., EURUSD, GBPUSD, USDJPY)
        timeframe: TradingView timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
    
    Returns:
        JSON with signal, trading plan, and dynamic risk calculations
    
    Example:
        GET /api/signals/EURUSD/1h?trading_style=swing_trading&account_size=50000&risk_percentage=2.5
    """
    
    try:
        # Get query parameters
        trading_style = request.args.get('trading_style', 'day_trading').lower()
        try:
            account_size = float(request.args.get('account_size', Config.DEFAULT_ACCOUNT_SIZE))
        except ValueError:
            account_size = Config.DEFAULT_ACCOUNT_SIZE
        
        try:
            risk_percentage = float(request.args.get('risk_percentage', Config.DEFAULT_RISK_PERCENTAGE))
        except ValueError:
            risk_percentage = Config.DEFAULT_RISK_PERCENTAGE
        
        # Validate inputs
        pair = pair.upper()
        
        # Convert TradingView timeframe to yfinance format
        yf_timeframe = Config.TIMEFRAME_MAPPING.get(timeframe.lower())
        if not yf_timeframe:
            return jsonify({
                'error': f'Invalid timeframe: {timeframe}',
                'supported_timeframes': list(Config.TIMEFRAME_MAPPING.keys())
            }), 400
        
        # Validate trading style
        if trading_style not in Config.TRADING_STYLES:
            return jsonify({
                'error': f'Invalid trading style: {trading_style}',
                'supported_styles': list(Config.TRADING_STYLES.keys())
            }), 400
        
        # Fetch data
        candles = fetcher.get_intraday_data(pair, yf_timeframe)
        
        # Analyze indicators
        indicators = analyzer.analyze(candles)
        
        # Generate signal
        signal = engine.generate_signal(candles, indicators, pair, timeframe)
        
        # Create risk engine with user parameters
        risk_engine = RiskEngine(account_size=account_size, risk_percentage=risk_percentage)
        
        # Calculate risk with trading style
        signal = risk_engine.calculate_risk(signal, candles, indicators.atr, trading_style=trading_style)
        
        # Check if trade is valid
        is_valid = risk_engine.validate_trade(signal)
        
        # Build response
        response = {
            'pair': pair,
            'timeframe': timeframe,
            'display_timeframe': timeframe,  # Already in TradingView format
            'timestamp': datetime.now().isoformat(),
            'current_price': round(candles[-1].close, 6),
            'trading_style': {
                'name': Config.TRADING_STYLES[trading_style]['name'],
                'key': trading_style,
                'description': Config.TRADING_STYLES[trading_style]['description'],
            },
            'account': {
                'size': account_size,
                'risk_percentage': risk_percentage,
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
                'risk_pips': round(signal.risk_pips, 1),
                'profit_pips': round(signal.profit_pips, 1),
                'risk_reward_ratio': round(signal.risk_reward_ratio, 2),
                'position_size_micro_lots': round(signal.position_size_micro_lots, 2),
                'position_size_standard_lots': round(signal.position_size_micro_lots / 1000, 3),
            },
            'trade_validity': {
                'valid': is_valid,
                'message': 'Trade meets all quality criteria' if is_valid else 'Trade does not meet minimum standards'
            }
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
        timeframe: TradingView timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
    
    Returns:
        JSON with all indicator values
    """
    
    try:
        pair = pair.upper()
        
        # Convert TradingView timeframe to yfinance format
        yf_timeframe = Config.TIMEFRAME_MAPPING.get(timeframe.lower())
        if not yf_timeframe:
            return jsonify({
                'error': f'Invalid timeframe: {timeframe}',
                'supported_timeframes': list(Config.TIMEFRAME_MAPPING.keys())
            }), 400
        
        # Fetch data
        candles = fetcher.get_intraday_data(pair, yf_timeframe)
        
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
# COMPLETE ANALYSIS ENDPOINT - WITH TRADING STYLE & ACCOUNT SIZE
# ============================================================================

@analysis_bp.route('/analysis/<string:pair>/<string:timeframe>', methods=['GET'])
def get_analysis(pair, timeframe):
    """
    Get complete analysis: indicators + signal + risk management
    
    Query Parameters:
        trading_style: One of ['scalping', 'day_trading', 'swing_trading', 'position_trading'] (default: day_trading)
        account_size: Account size in USD (default: 10000)
        risk_percentage: Risk per trade as percentage (default: 2.0)
    
    Args:
        pair: Forex pair (e.g., EURUSD)
        timeframe: TradingView timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
    
    Returns:
        JSON with indicators, signal, and trading plan
    
    Example:
        GET /api/analysis/EURUSD/1h?trading_style=swing_trading&account_size=50000
    """
    
    try:
        # Get query parameters
        trading_style = request.args.get('trading_style', 'day_trading').lower()
        try:
            account_size = float(request.args.get('account_size', Config.DEFAULT_ACCOUNT_SIZE))
        except ValueError:
            account_size = Config.DEFAULT_ACCOUNT_SIZE
        
        try:
            risk_percentage = float(request.args.get('risk_percentage', Config.DEFAULT_RISK_PERCENTAGE))
        except ValueError:
            risk_percentage = Config.DEFAULT_RISK_PERCENTAGE
        
        # Validate inputs
        pair = pair.upper()
        
        # Convert TradingView timeframe to yfinance format
        yf_timeframe = Config.TIMEFRAME_MAPPING.get(timeframe.lower())
        if not yf_timeframe:
            return jsonify({
                'error': f'Invalid timeframe: {timeframe}',
                'supported_timeframes': list(Config.TIMEFRAME_MAPPING.keys())
            }), 400
        
        # Validate trading style
        if trading_style not in Config.TRADING_STYLES:
            return jsonify({
                'error': f'Invalid trading style: {trading_style}',
                'supported_styles': list(Config.TRADING_STYLES.keys())
            }), 400
        
        # Fetch data
        candles = fetcher.get_intraday_data(pair, yf_timeframe)
        
        # Analyze indicators
        indicators = analyzer.analyze(candles)
        
        # Generate signal
        signal = engine.generate_signal(candles, indicators, pair, timeframe)
        
        # Create risk engine with user parameters
        risk_engine = RiskEngine(account_size=account_size, risk_percentage=risk_percentage)
        
        # Calculate risk with trading style
        signal = risk_engine.calculate_risk(signal, candles, indicators.atr, trading_style=trading_style)
        
        # Check validity
        is_valid = risk_engine.validate_trade(signal)
        
        # Build comprehensive response
        response = {
            'pair': pair,
            'timeframe': timeframe,
            'display_timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'current_price': round(candles[-1].close, 6),
            'trading_style': {
                'name': Config.TRADING_STYLES[trading_style]['name'],
                'key': trading_style,
                'description': Config.TRADING_STYLES[trading_style]['description'],
            },
            'account': {
                'size': account_size,
                'risk_percentage': risk_percentage,
                'risk_amount_usd': round(account_size * (risk_percentage / 100), 2),
            },
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
                'risk_pips': round(signal.risk_pips, 1),
                'profit_pips': round(signal.profit_pips, 1),
                'risk_reward_ratio': round(signal.risk_reward_ratio, 2),
                'position_size_micro_lots': round(signal.position_size_micro_lots, 2),
                'position_size_standard_lots': round(signal.position_size_micro_lots / 1000, 3),
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
# SUPPORTED PAIRS & TIMEFRAMES ENDPOINT
# ============================================================================

@analysis_bp.route('/pairs', methods=['GET'])
def get_pairs():
    """
    Get list of supported forex pairs and timeframes
    
    Returns:
        JSON with supported pairs and timeframes
    """
    
    return jsonify({
        'supported_pairs': Config.FOREX_PAIRS,
        'supported_timeframes': list(Config.TIMEFRAME_MAPPING.keys()),
        'supported_trading_styles': list(Config.TRADING_STYLES.keys()),
        'default_account_size': Config.DEFAULT_ACCOUNT_SIZE,
        'default_risk_percentage': Config.DEFAULT_RISK_PERCENTAGE,
    }), 200


def register_analysis_routes(app):
    """
    Register analysis routes with Flask app
    
    Usage:
        from app.routes.analysis import register_analysis_routes
        register_analysis_routes(app)
    """
    app.register_blueprint(analysis_bp)