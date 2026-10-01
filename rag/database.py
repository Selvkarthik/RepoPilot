import psycopg
from core.config import settings


def get_connection():
    return psycopg.connect(settings.DB_URL)