"""
app/routes/news.py

Register in app/__init__.py inside create_app():

    from app.routes.news import news_bp
    app.register_blueprint(news_bp)
"""
from flask import Blueprint, jsonify, request

from app.services.news_service import INSTRUMENTS, get_news_payload

news_bp = Blueprint("news", __name__)


@news_bp.route("/api/news")
def news():
    symbol = request.args.get("symbol", "EURUSD").upper()
    if symbol not in INSTRUMENTS:
        return jsonify({"error": f"Unsupported symbol. Use one of {list(INSTRUMENTS)}"}), 400
    try:
        return jsonify(get_news_payload(symbol))
    except Exception as exc:
        return jsonify({"error": "News unavailable", "detail": str(exc)}), 503