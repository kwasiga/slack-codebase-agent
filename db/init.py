import os
from pathlib import Path

import psycopg2

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_PATH.read_text())
        conn.commit()
    finally:
        conn.close()
