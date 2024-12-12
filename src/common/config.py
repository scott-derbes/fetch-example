import os

from common.logging import get_logger

logger = get_logger()

class CONFIG:
    """Generates a Config Object which can be used to ensure correct
    values for each environment

    Raises:
        ValueError: _description_
    """
    ENVIRONMENT = os.getenv('ENV', 'local')
    
    if ENVIRONMENT == 'local':
        KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
        KAFKA_TOPIC = 'user-login'
        KAFKA_GROUP_ID = 'flink-kafka-fetch-example-local'
        WRITE_KAFKA_TOPIC = 'user-login-aggregated-local'
    else:
        message = "Invalid Environment Passed"
        logger.error(message)
        raise ValueError(message)