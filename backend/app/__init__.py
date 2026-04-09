"""MedAssist AI - Flask Application Factory."""

import os

from flask import Flask, jsonify

from app.config import config_map
from app.extensions import db, migrate, jwt, cors, socketio, limiter


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Configuration environment name (development, testing, production).
                     Defaults to FLASK_ENV environment variable or 'development'.

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_class = config_map[config_name]
    app.config.from_object(config_class)

    # Run production safety checks (e.g. reject default secrets)
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # Initialize extensions
    _register_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Register WebSocket event handlers
    _register_websocket_handlers()

    # Register error handlers
    _register_error_handlers(app)

    # Health check route
    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "service": "medassist-ai-backend"}), 200

    return app


def _register_extensions(app: Flask) -> None:
    """Initialize Flask extensions with the app instance."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3055").split(",")
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
    socketio.init_app(app, cors_allowed_origins=allowed_origins)
    limiter.init_app(app)


def _register_blueprints(app: Flask) -> None:
    """Register API blueprints.

    Team members: register your blueprints here as you create them.
    Example:
        from app.api.v1.auth import bp as auth_bp
        app.register_blueprint(auth_bp)
    """
    from app.api.v1.health import bp as health_bp
    from app.api.v1.auth import bp as auth_bp
    from app.api.v1.patients import bp as patients_bp
    from app.api.v1.doctors import bp as doctors_bp
    from app.api.v1.vitals import bp as vitals_bp
    from app.api.v1.care_plans import bp as care_plans_bp
    from app.api.v1.medications import bp as medications_bp
    from app.api.v1.notifications import bp as notifications_bp
    from app.api.v1.reports import bp as reports_bp
    from app.api.v1.symptoms import bp as symptoms_bp
    from app.api.v1.appointments import bp as appointments_bp
    from app.api.v1.telemedicine import bp as telemedicine_bp
    from app.api.v1.chat import bp as chat_bp
    from app.api.v1.monitoring import bp as monitoring_bp
    from app.api.v1.devices import bp as devices_bp
    from app.api.v1.analytics import bp as analytics_bp
    from app.api.v1.admin import bp as admin_bp
    from app.api.v1.voice import bp as voice_bp
    from app.api.v1.voice_symptom import bp as voice_symptom_bp
    from app.api.v1.realtime import bp as realtime_bp
    from app.api.v1.search import bp as search_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(vitals_bp)
    app.register_blueprint(care_plans_bp)
    app.register_blueprint(medications_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(symptoms_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(telemedicine_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(voice_symptom_bp)
    app.register_blueprint(realtime_bp)
    app.register_blueprint(search_bp)


def _register_websocket_handlers() -> None:
    """Register Socket.IO event handlers for real-time features."""
    from app.api.websocket import register_websocket_handlers

    register_websocket_handlers(socketio)


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found"}}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}), 500
