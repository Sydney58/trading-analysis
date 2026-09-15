from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    from app.routes.analysis import register_analysis_routes
    register_analysis_routes(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)