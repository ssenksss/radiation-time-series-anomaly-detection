from pathlib import Path
import os
from typing import Optional, Tuple, List

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Please create a .env file in the project root."
        )

    return psycopg2.connect(DATABASE_URL)


def fetch_one(query: str, params: Optional[Tuple] = None):
    with get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()


def fetch_all(query: str, params: Optional[Tuple] = None):
    with get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def execute_query(query: str, params: Optional[Tuple] = None):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()


def execute_many(query: str, params_list: List[Tuple]):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(query, params_list)
            connection.commit()
