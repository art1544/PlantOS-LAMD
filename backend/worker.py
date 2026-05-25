"""Entry-point do worker consumidor de eventos do PlantOS (Sprint 2)."""

from app.database import init_db
from app.messaging.consumer import run


if __name__ == "__main__":
    init_db()
    run()
