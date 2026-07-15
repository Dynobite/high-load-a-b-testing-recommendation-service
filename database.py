import os
import psycopg2
from loguru import logger

def postgres_connection():
    """Establishes and returns a connection to PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "6432")),
            database=os.getenv("POSTGRES_DB", "recommendation_db"),
            user=os.getenv("POSTGRES_USER", "user"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
        )
    except Exception as e:
        logger.error(f"Error: failed to connect to database. {e}")
        raise e

    conn.autocommit = True

    return conn
