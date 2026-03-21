"""API blueprint registration.

Team members: import and register your blueprints here as you create them.

Example:
    from app.api.v1.auth import bp as auth_bp
    blueprints.append(auth_bp)
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all v1 API blueprints with the Flask app."""
    from app.api.v1.health import bp as health_bp

    from app.api.v1.auth import bp as auth_bp
    from app.api.v1.patients import bp as patients_bp
    from app.api.v1.doctors import bp as doctors_bp
    from app.api.v1.vitals import bp as vitals_bp

    blueprints = [
        health_bp,
        auth_bp,
        patients_bp,
        doctors_bp,
        vitals_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
