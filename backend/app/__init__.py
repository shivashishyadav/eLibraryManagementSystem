from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    
    app.config.from_object(config_class)

    db.init_app(app)

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.book_routes import book_bp
    from app.routes.borrow_routes import borrow_bp
    from app.routes.ai_routes import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(book_bp)
    app.register_blueprint(borrow_bp)
    app.register_blueprint(ai_bp)

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'name': 'E-Library Management API',
            'version': '1.0.0',
            'health_check': '/health',
            'documentation': 'Refer to README.md for complete endpoint spec'
        }), 200

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'}), 200

    with app.app_context():
        db.create_all()

    return app