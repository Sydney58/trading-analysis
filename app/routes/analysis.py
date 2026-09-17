"""
Optimized API Routes - Memory efficient
Includes garbage collection to free memory after requests
"""

import gc
from flask import Blueprint, jsonify, request
from datetime import datetime
from app.services import DataFetcher, TechnicalAnalysis, SignalEngine, RiskEngine
from app.config import Config

# Create a Blueprint for analysis routes
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# Initialize services (will be recreated per request with user parameters)
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
    """Get all available trading styles"""
    risk_engine = RiskEngine()
    styles = risk_engine.get_all_trading_styles()
    
    response = jsonify({
        'trading_styles': styles,
        'default_style': 'day_trading',
        'timestamp': datetime.now().isoformat()
    })
    
    # Clean up memory
    gc.collect()
    return response, 200


@analysis_bp.route('/trading-styles/<string:style>', methods=['GET'])
def get_trading_style_info(style):
    """Get information about a specific trading style"""
    risk_engine = RiskEngine()
    style_info = risk_engine.get_trading_style_info(style)
    
    if not style_info:
        gc.collect()
        return jsonify({
            'error': f'Trading style "{style}" not found',
            'available_styles': ['scalping', 'day_trading', 'swing_trading', 'position_trading']
        }), 404
    
    response = jsonify({
        'style': style,
        'details': style_info,
        'timestamp': datetime.now().isoformat()
    })
    
    gc.collect()
    return response, 200


# ============================================================================
# SIGNALS ENDPOINT - OPTIMIZED
# ============================================================================

@analysis_bp.route('/signals/<string:pair>/<string:timeframe>', methods=['GET'])
def get_signal(pair, timeframe):
    """
    Get trading signal for a forex pair (OPTIMIZED - less memory)
    
    Query Parameters:
        trading_style: One of ['scalping', 'day_trading', 'swing_trading', 'position_trading']
        account_size: Account size in USD (default: 10000)
        risk_percentage: Risk per trade as percentage (default: 2.0)
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
            gc.collect()
            return jsonify({
                'error': f'Invalid timeframe: {timeframe}',
                'supported_timeframes': list(Config.TIMEFRAME_MAPPING.keys())
            }), 400
        
        # Validate trading style
        if trading_style not in Config.TRADING_STYLES:
            gc.collect()
            return jsonify({
                'error': f'Invalid trading style: {trading_style}',
                'supported_styles': list(Config.TRADING_STYLES.keys())
            }), 400
        
        # Fetch data (OPTIMIZED: 250 candles, not 714)
        candles = fetcher.get_intraday_data(pair, yf_timeframe, limit=250)
        
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
            'timestamp': datetime.now().isoformat(),
            'current_price': round(candles[-1].close, 6),
            'trading_style': {
                'name': Config.TRADING_STYLES[trading_style]['name'],
                'key': trading_style,
            },
            'signal': {
                'type': signal.signal_type,
                'confidence': round(signal.confidence, 2),
            },
            'trading_plan': {
                'entry': round(signal.entry_price, 6),
                'stop_loss': round(signal.stop_loss, 6),
                'take_profit': round(signal.take_profit, 6),
                'risk_pips': round(signal.risk_pips, 1),
                'profit_pips': round(signal.profit_pips, 1),
                'risk_reward_ratio': round(signal.risk_reward_ratio, 2),
                'position_size_micro_lots': round(signal.position_size_micro_lots, 2),
            },
            'trade_validity': {
                'valid': is_valid,
            }
        }
        
        # Clean up memory before returning
        del candles, indicators, signal, risk_engine
        gc.collect()
        
        return jsonify(response), 200
    
    except ValueError as e:
        gc.collect()
        return jsonify({'error': str(e), 'pair': pair, 'timeframe': timeframe}), 400
    except Exception as e:
        gc.collect()
        return jsonify({'error': f'Error generating signal: {str(e)}'}), 500


# ============================================================================
# COMPLETE ANALYSIS ENDPOINT - OPTIMIZED
# ============================================================================

@analysis_bp.route('/analysis/<string:pair>/<string:timeframe>', methods=['GET'])
def get_analysis(pair, timeframe):
    """
    Get complete analysis (OPTIMIZED - less memory)
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
            gc.collect()
            return jsonify({
                'error': f'Invalid timeframe: {timeframe}',
                'supported_timeframes': list(Config.TIMEFRAME_MAPPING.keys())
            }), 400
        
        # Validate trading style
        if trading_style not in Config.TRADING_STYLES:
            gc.collect()
            return jsonify({
                'error': f'Invalid trading style: {trading_style}',
                'supported_styles': list(Config.TRADING_STYLES.keys())
            }), 400
        
        # Fetch data (OPTIMIZED: 250 candles)
        candles = fetcher.get_intraday_data(pair, yf_timeframe, limit=250)
        
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
        
        # Clean up memory before returning
        del candles, indicators, signal, risk_engine
        gc.collect()
        
        return jsonify(response), 200
    
    except Exception as e:
        gc.collect()
        return jsonify({'error': f'Error analyzing pair: {str(e)}'}), 500


# ============================================================================
# SUPPORTED PAIRS ENDPOINT
# ============================================================================

@analysis_bp.route('/pairs', methods=['GET'])
def get_pairs():
    """Get list of supported forex pairs and timeframes"""
    
    response = jsonify({
        'supported_pairs': Config.FOREX_PAIRS,
        'supported_timeframes': list(Config.TIMEFRAME_MAPPING.keys()),
        'supported_trading_styles': list(Config.TRADING_STYLES.keys()),
        'default_account_size': Config.DEFAULT_ACCOUNT_SIZE,
        'default_risk_percentage': Config.DEFAULT_RISK_PERCENTAGE,
        'optimization': 'Using 250 candles per request (optimized for free tier)',
    })
    
    gc.collect()
    return response, 200


def register_analysis_routes(app):
    """Register analysis routes with Flask app"""
    app.register_blueprint(analysis_bp)