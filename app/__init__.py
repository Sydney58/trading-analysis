from flask import Flask


def create_app():
    app = Flask(__name__)

    # Health check endpoint
    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Register analysis API routes
    from app.routes.analysis import register_analysis_routes
    register_analysis_routes(app)

    return app