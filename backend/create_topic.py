#Code to create kafka topic 
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "login_events"

def create_kafka_topic(topic_name: str, num_partitions: int = 1, replication_factor: int = 1):
    """Create a Kafka topic if it does not already exist"""
    admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","))
    
    topic_list = [NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)]
    
    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print(f"Kafka topic '{topic_name}' created successfully.")
    except TopicAlreadyExistsError:
        print(f"Kafka topic '{topic_name}' already exists.")
    except Exception as e:
        print(f"Failed to create Kafka topic '{topic_name}': {e}")
    finally:
        admin_client.close()

if __name__ == "__main__":
    create_kafka_topic(KAFKA_TOPIC)