from flask import Flask
from flask_cors import CORS
from app.database import init_db


def create_app():
    app = Flask(__name__)
    CORS(app)

    init_db()

    from app.routes.os_routes import os_bp
    app.register_blueprint(os_bp)

    try:
        from app.messaging.publisher import setup_queues
        setup_queues()
    except Exception as e:
        print(f" [!] RabbitMQ indisponível na inicialização: {e}")

    return app
