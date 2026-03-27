"""WebSocket event handlers for real-time communication.

Registers Socket.IO event handlers with the Flask-SocketIO instance.
Call ``register_websocket_handlers(socketio)`` from the app factory.
"""

from flask_socketio import SocketIO

from app.api.websocket.vitals_stream import register_vitals_handlers


def register_websocket_handlers(sio: SocketIO) -> None:
    """Register all WebSocket namespaces and event handlers.

    Args:
        sio: The Flask-SocketIO instance from extensions.
    """
    register_vitals_handlers(sio)
