from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from common.config import CONFIG
from common.logging import get_logger

logger = get_logger()

def create_kafka_topic(topic_name, num_partitions=1, replication_factor=1):
    admin_client = KafkaAdminClient(
        bootstrap_servers=CONFIG.KAFKA_BOOTSTRAP_SERVERS,
        client_id="flink-kafka-fetch-example"
    )

    topic_list = []
    topic_list.append(NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor))

    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        logger.info("Kafka topic %s created successfully.", topic_name)
    except TopicAlreadyExistsError:
        logger.warning("Kafka topic %s already exists.", topic_name)

if __name__ == "__main__":
    logger.info("Initializing Kafka Topic Creation")

    # Create a new Kafka topic
    create_kafka_topic(CONFIG.WRITE_KAFKA_TOPIC)
