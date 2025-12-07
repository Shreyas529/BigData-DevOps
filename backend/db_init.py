# db_init.py
import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "logindata")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "pwd")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS login_events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    country VARCHAR(50),
    device VARCHAR(50),
    plan VARCHAR(50),
    status VARCHAR(20),
    event_time BIGINT
);
"""

CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION insert_login_event(
    p_user_id VARCHAR,
    p_country VARCHAR,
    p_device VARCHAR,
    p_plan VARCHAR,
    p_status VARCHAR,
    p_event_time BIGINT
);
"""

def main():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        conn.autocommit = True
        cur = conn.cursor()
        print("Creating table...")
        cur.execute(CREATE_TABLE_SQL)
        print("Creating function table...")
        cur.execute(CREATE_FUNCTION_SQL)

    except Exception as e:
        print("Error during DB init:", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
