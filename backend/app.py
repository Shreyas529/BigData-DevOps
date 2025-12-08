import os
import json
import random
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "login_events")

# Device and Plan options for random generation
DEVICES = ["mobile", "web", "tv", "tablet", "desktop"]
PLANS = ["basic", "standard", "premium", "free"]

# Initialize Kafka Producer
producer = None

def get_kafka_producer():
    """Get or create Kafka producer with retry logic"""
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")
            return None
    return producer

def generate_login_event(username: str, region: str, status: str) -> dict:
    """
    Generate a complete login event with random data for missing fields
    
    Schema:
    - user_id: from username
    - country: from region
    - device: randomly generated
    - plan: randomly generated
    - status: from login result
    - event_time: current timestamp in milliseconds
    """
    return {
        "user_id": username,
        "country": region,
        "device": random.choice(DEVICES),
        "plan": random.choice(PLANS),
        "status": status,
        "event_time": int(time.time() * 1000)  # Current time in milliseconds
    }

def push_to_kafka(event: dict) -> bool:
    """Push event to Kafka topic"""
    kafka_producer = get_kafka_producer()
    if kafka_producer is None:
        return False
    
    try:
        future = kafka_producer.send(KAFKA_TOPIC, value=event)
        # Wait for the message to be delivered
        record_metadata = future.get(timeout=10)
        print(f"Event sent to {record_metadata.topic} partition {record_metadata.partition}")
        return True
    except Exception as e:
        print(f"Failed to send event to Kafka: {e}")
        return False

@app.route('/api/login-event', methods=['POST'])
def handle_login_event():
    """
    Handle login event from frontend
    
    Expected payload:
    {
        "username": "string",
        "region": "string",
        "status": "success" | "failed"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get("username")
        region = data.get("region")
        status = data.get("status")
        
        if not all([username, region, status]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if status not in ["success", "failed"]:
            return jsonify({"error": "Invalid status value"}), 400
        
        # Generate complete event with random data
        event = generate_login_event(username, region, status)
        
        # Push to Kafka
        kafka_success = push_to_kafka(event)
        
        if kafka_success:
            return jsonify({
                "message": "Login event processed successfully",
                "event": event
            }), 200
        else:
            # Still return success for frontend but log the issue
            return jsonify({
                "message": "Login event received (Kafka unavailable)",
                "event": event
            }), 202
            
    except Exception as e:
        print(f"Error processing login event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    kafka_status = "connected" if get_kafka_producer() is not None else "disconnected"
    return jsonify({
        "status": "healthy",
        "kafka": kafka_status
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("BACKEND_PORT", 5002))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug)
