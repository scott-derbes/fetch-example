from pyflink.common import Duration, WatermarkStrategy, Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import StreamExecutionEnvironment, DataStream
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaSink, KafkaOffsetsInitializer, KafkaOffsetResetStrategy, KafkaRecordSerializationSchema, DeliveryGuarantee
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from pyflink.datastream.functions import ProcessFunction, MapFunction
from pyflink.table import DataTypes, Schema, StreamTableEnvironment, Table
from pyflink.table.expressions import lit, col, to_timestamp_ltz
from pyflink.table.window import Tumble
from schema.user_login import USER_LOGIN_SCHEMA

from common.config import CONFIG
from common.logging import get_logger

logger = get_logger()

class PrintWatermarkProcessFunction(ProcessFunction):
    def process_element(self, value, ctx: ProcessFunction.Context):
        logger.info(f"Processing Element: {value}")
        logger.info(f"Current Watermark: {ctx.timer_service().current_watermark()}")


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

    watermark_strategy = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(30))

    return stream_env.from_source(kafka_source, watermark_strategy, "User Login Kafka Source").uid("read-user-login-kafka-stream")

def generate_table(table_env: StreamTableEnvironment, data_stream: DataStream) -> Table:
    """Generates a Table from the DataStream with the specified schema, this allows for SQL operations on the stream and better control over the watermark

    Args:
        table_env (StreamTableEnvironment): Flink Table Environment
        data_stream (DataStream): Flink DataStream

    Returns:
        Table: Flink Table
    """
    schema = (Schema.new_builder()
                .column("user_id", DataTypes.STRING())
                .column("app_version", DataTypes.STRING())
                .column("device_type", DataTypes.STRING())
                .column("ip", DataTypes.STRING())
                .column("locale", DataTypes.STRING())
                .column("device_id", DataTypes.STRING())
                .column("timestamp", DataTypes.STRING())
                .column_by_expression("event_time", to_timestamp_ltz(col("timestamp").cast(DataTypes.BIGINT()), 3))
                .watermark("event_time", "event_time - INTERVAL '5' SECOND")
                .build()
            )
    return table_env.from_data_stream(data_stream, schema)

    
def aggregate_stream(table: Table) -> Table:
    table = table.window(Tumble.over(lit(5).seconds).on(col("event_time")).alias("w"))
    table = table.group_by(col('device_type'), col('locale'), col('w')) \
        .select(
            col('device_type'), 
            col('locale'), 
            col('w').start.alias('window_start'), 
            col('w').end.alias('window_end'), 
            col('user_id').count.alias('user_count')
        )
    
    return table

class RowToStringMapFunction(MapFunction):
    def map(self, value):
        return str(value)

def run(stream_env: StreamExecutionEnvironment, t_env: StreamTableEnvironment):
    ds = read_kafka_source(stream_env)
    table = generate_table(t_env, ds)
    # table.print_schema()
    # table = aggregate_stream(table)
    table.print_schema()

    ds = t_env.to_data_stream(table)

    # ds.print()
    ds.process(PrintWatermarkProcessFunction())

    # Convert the Row to a String so it can be sent to Kafka
    ds = ds.map(RowToStringMapFunction(), Types.STRING())

    sink = KafkaSink.builder() \
        .set_bootstrap_servers(CONFIG.KAFKA_BOOTSTRAP_SERVERS) \
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
                .set_topic(CONFIG.WRITE_KAFKA_TOPIC)
                .set_value_serialization_schema(SimpleStringSchema())
                .build()
        ) \
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE) \
        .build()
    
    ds.sink_to(sink).name("Aggregate Kafka Sink")

    stream_env.execute("Aggregate Fetch Example Stream")

if __name__ == "__main__":
    streaming_env = StreamExecutionEnvironment.get_execution_environment()
    # start a checkpoint every 1000 ms
    # streaming_env.enable_checkpointing(1000)
    logger.info("Initialized Flink Stream Environment")

    table_env = StreamTableEnvironment.create(stream_execution_environment=streaming_env)

    run(streaming_env, table_env)