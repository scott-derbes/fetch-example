from common.config import CONFIG
from common.logging import get_logger
from pyflink.common import Duration, WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment, DataStream
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer, KafkaOffsetResetStrategy
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from schema.user_login import USER_LOGIN_SCHEMA


logger = get_logger()

def read_kafka_source(stream_env: StreamExecutionEnvironment) -> DataStream:
    """Reads the User Login Kafka Stream, Deserializes it with specified schema, and returns it as a Datastream

    Note: This function could be rebuilt to take more parameters and be able to read any Kafka Stream

    Args:
        stream_env (StreamExecutionEnvironment): _description_

    Returns:
        DataStream: _description_
    """
    deserilization_schema = JsonRowDeserializationSchema.builder().type_info(type_info=USER_LOGIN_SCHEMA).build()

    kafka_source = (
        KafkaSource.builder()
            .set_bootstrap_servers(CONFIG.KAFKA_BOOTSTRAP_SERVERS)
            .set_topics(CONFIG.KAFKA_TOPIC)
            .set_group_id(CONFIG.KAFKA_GROUP_ID)
            .set_starting_offsets(KafkaOffsetsInitializer.committed_offsets(KafkaOffsetResetStrategy.EARLIEST))
            .set_property("partiton.discovery.interval.ms", "10000")
            .set_value_only_deserializer(deserilization_schema)
            .build()
    )   

    watermark_strategy = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(20))

    return stream_env.from_source(kafka_source, watermark_strategy, "User Login Kafka Source").uid("read-user-login-kafka-stream")

def run(stream_env: StreamExecutionEnvironment):
    user_login_stream = read_kafka_source(stream_env)

    user_login_stream.print()

    stream_env.execute("Aggregate Fetch Example Stream")

if __name__ == "__main__":
    streaming_env = StreamExecutionEnvironment.get_execution_environment()
    # start a checkpoint every 1000 ms
    streaming_env.enable_checkpointing(1000)
    logger.info("Initialized Flink Stream Environment")

    run(streaming_env)