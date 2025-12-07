# consumer.py
import os
import json
import time
import psycopg2
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "login_events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "login_consumer_group")

# PostgreSQL Configuration
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "logindata")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "pwd")

INSERT_SQL = """
INSERT INTO login_events (user_id, country, device, plan, status, event_time)
VALUES (%s, %s, %s, %s, %s, %s);
"""


def get_db_connection():
    """Create and return a PostgreSQL connection with retry logic"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            print(f"Connected to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Failed to connect to PostgreSQL (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    raise Exception("Could not connect to PostgreSQL after multiple attempts")


def get_kafka_consumer():
    """Create and return a Kafka consumer with retry logic"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            print(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}, topic: {KAFKA_TOPIC}")
            return consumer
        except Exception as e:
            print(f"Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    raise Exception("Could not connect to Kafka after multiple attempts")


def insert_event(conn, event):
    """Insert a login event into PostgreSQL"""
    try:
        cur = conn.cursor()
        cur.execute(INSERT_SQL, (
            event.get("user_id"),
            event.get("country"),
            event.get("device"),
            event.get("plan"),
            event.get("status"),
            event.get("event_time")
        ))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Error inserting event: {e}")
        conn.rollback()
        return False


def consume_events():
    """Main consumer loop - reads from Kafka and inserts into PostgreSQL"""
    print("Starting Kafka consumer...")
    
    # Get connections
    # conn = get_db_connection()
    consumer = get_kafka_consumer()
    
    event_count = 0
    
    try:
        print("Waiting for messages...")
        for message in consumer:
            event = message.value
            
            # Log received event
            print(f"Received event: user_id={event.get('user_id')}, "
                  f"country={event.get('country')}, status={event.get('status')}, plan={event.get('plan')}, device={event.get('device')}, event_time={event.get('event_time')}")
            
            # Insert into PostgreSQL
            # if insert_event(conn, event):
            #     event_count += 1
            #     print(f"Inserted event #{event_count} into PostgreSQL")
            # else:
            #     print(f"Failed to insert event: {event}")
                
    except KeyboardInterrupt:
        print(f"\nConsumer stopped. Total events processed: {event_count}")
    except Exception as e:
        print(f"Error in consumer loop: {e}")
    finally:
        consumer.close()
        # conn.close()
        print("Connections closed.")


if __name__ == "__main__":
    consume_events()
