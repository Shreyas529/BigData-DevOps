# backend/db_init.py
import os
import asyncpg
from psycopg2 import sql  # just for formatting table names safely

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "logindata")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "pwd")


async def main(table_name: str = "test_login_events"):
    """
    Initialize the database:
    - Create the specified table if it does not exist.
    """
    conn = None
    try:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50),
            country VARCHAR(50),
            device VARCHAR(50),
            plan VARCHAR(50),
            status VARCHAR(20),
            event_time BIGINT
        );
        """

        print(f"Creating table '{table_name}' if it does not exist...")
        await conn.execute(create_table_sql)
        print(f"Table '{table_name}' ready.")

    except Exception as e:
        print("Error during DB init:", e)
    finally:
        if conn:
            await conn.close()
