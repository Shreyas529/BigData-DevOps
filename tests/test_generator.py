import asyncio
import asyncpg
import random
import time

async def generate_events(db_config, throughput, duration_ms):
    """
    throughput: events per second
    duration_ms: how long to generate events
    """
    conn = await asyncpg.connect(**db_config)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS test_login_events (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(50),
        country VARCHAR(50),
        device VARCHAR(50),
        plan VARCHAR(50),
        status VARCHAR(20),
        event_time BIGINT);
    """)

    await conn.execute("DELETE FROM test_login_events;")

    events = []
    interval = 1 / throughput  # seconds per event
    end_time = time.time() + (duration_ms / 1000)

    while time.time() < end_time:
        event_time = int(time.time() * 1000)
        status = random.choice(["success", "failed"])
        country = random.choice(["US", "IN", "UK", "DE", "CA"])
        user_id = f"user_{random.randint(1, 50)}"
        device = random.choice(["mobile", "web", "tv"])
        plan = random.choice(["basic", "standard", "premium"])

        event = {
            "event_time": event_time,
            "status": status,
            "country": country,
            "user_id": user_id,
            "device": device,
            "plan": plan
        }

        events.append(event)

        await conn.execute("""
            INSERT INTO test_login_events(user_id, country, device, plan, status, event_time)
            VALUES($1, $2, $3, $4, $5, $6)
        """, user_id, country, device, plan, status, event_time)

        await asyncio.sleep(interval)

    await conn.close()
    return events
