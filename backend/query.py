import os
import time
import json
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "database": os.getenv("POSTGRES_DB", "logindata"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "pwd"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432)
}

WINDOW_SIZE = 30000        # 30 seconds
RETENTION_MS = 60000       # cleanup older than 60 seconds
POLL_INTERVAL = 5          # seconds


WINDOW_QUERY = """
WITH success_data AS (
    SELECT 
        country,
        COUNT(*) AS success_count
    FROM login_events
    WHERE status = 'success'
      AND event_time >= $1 
      AND event_time < $2
    GROUP BY country
),

failed_data AS (
    SELECT 
        country,
        COUNT(*) AS failed_count
    FROM login_events
    WHERE status = 'failed'
      AND event_time >= $1 
      AND event_time < $2
    GROUP BY country
)

SELECT
    COALESCE(s.country, f.country) AS country,
    COALESCE(s.success_count, 0) AS successes,
    COALESCE(f.failed_count, 0) AS failures,
    CASE 
        WHEN COALESCE(f.failed_count, 0) = 0 THEN NULL
        ELSE s.success_count::float / f.failed_count
    END AS ratio
FROM success_data s
FULL OUTER JOIN failed_data f USING (country)
ORDER BY ratio DESC NULLS LAST;
"""

DELETE_OLD_QUERY = """
DELETE FROM login_events IF EXISTS
WHERE event_time < $1;
"""

async def delete_query(DB_CONFIG, table_name):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.fetchrow(f"""DELETE FROM {table_name}""")

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered window analytics → {msg.topic()} [{msg.partition()}]")


async def query_loop(DB_CONFIG, WINDOW_SIZE, WINDOW_QUERY, TABLE_NAME, RETENTION_MS=None, DELETE_OLD_QUERY=None):
    conn = await asyncpg.connect(**DB_CONFIG)
    print("Connected to Postgres.")

    results = []

    while True:
        row = await conn.fetchrow(f"SELECT MIN(event_time) AS min_ts FROM {TABLE_NAME};")

        if row["min_ts"] is None:
            print("No events yet... retrying...")
            await asyncio.sleep(2)
            continue

        min_time = int(row["min_ts"])
        break

    window_start = (min_time // WINDOW_SIZE) * WINDOW_SIZE
    window_end = window_start + WINDOW_SIZE
    print(f"Starting from aligned window: {window_start}")

    flag = False

    last_watermark = -1

    while True:
        row = await conn.fetchrow(f"SELECT MAX(event_time) AS max_ts FROM {TABLE_NAME};")

        if row["max_ts"] is None:
            continue

        watermark = int(row["max_ts"])
        await asyncio.sleep(0.5)    
        # print(watermark, last_watermark)
        
        if (watermark == last_watermark):
            print(watermark)
            break

        last_watermark = watermark

        if (watermark < window_end):
            continue

        print(f"\nProcessing window {window_start} → {window_end}")

        rows = await conn.fetch(WINDOW_QUERY, window_start, window_end)

        payload = {
            "window_start": window_start,
            "window_end": window_end,
            "results": [
                {
                    "country": r["country"],
                    "success": r["successes"],
                    "failed": r["failures"],
                    "ratio": float(r["ratio"]) if r["ratio"] is not None else None
                }
                for r in rows
            ]
        }

        # print(json.dumps(payload, indent=2))

        results.append(payload)

        if (DELETE_OLD_QUERY and RETENTION_MS):
            delete_before = window_end - RETENTION_MS
            await conn.execute(DELETE_OLD_QUERY, delete_before)
            print(f"Deleted older than {delete_before}")

        window_start += WINDOW_SIZE
        window_end = window_start + WINDOW_SIZE


    return results


if __name__ == "__main__":
    asyncio.run(query_loop(DB_CONFIG,WINDOW_SIZE,WINDOW_QUERY,"logindata",RETENTION_MS,DELETE_OLD_QUERY))
