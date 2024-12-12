from pyflink.common import Duration, WatermarkStrategy, Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import StreamExecutionEnvironment, DataStream
from pyflink.datastream.connectors.kafka import ( 
    KafkaSource,
    KafkaSink, 
    KafkaOffsetsInitializer, 
    KafkaOffsetResetStrategy,
    KafkaRecordSerializationSchema, 
    DeliveryGuarantee
)
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from pyflink.datastream.functions import MapFunction
from pyflink.table import DataTypes, Schema, StreamTableEnvironment, Table
from pyflink.table.expressions import lit, col, to_timestamp_ltz
from pyflink.table.window import Tumble

from common.config import CONFIG
from common.logging import get_logger
from schema.user_login import USER_LOGIN_SCHEMA

logger = get_logger()


class RowToStringMapFunction(MapFunction):
    """Simple Map Function to convert a Row to a String

    Args:
        MapFunction (): Base Class for Map Transformation
    """
    def map(self, value):
        return str(value)

def read_kafka_source(stream_env: StreamExecutionEnvironment) -> DataStream:
    """Reads the User Login Kafka Stream, Deserializes it with specified schema, and returns it as a Datastream

    Note: This function could be rebuilt to take more parameters and be able to read any Kafka Stream instead of just User Login

    Args:
        stream_env (StreamExecutionEnvironment): Flink Stream Execution Environment

    Returns:
        DataStream: Stream of User Login Data from Kafka
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

    watermark_strategy = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(20)).with_idleness(Duration.of_minutes(1))

    return stream_env.from_source(kafka_source, watermark_strategy, "User Login Kafka Source").uid("read-user-login-kafka-stream")

def generate_table(t_env: StreamTableEnvironment, data_stream: DataStream) -> Table:
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
                .column_by_expression("ts", to_timestamp_ltz(col("timestamp").cast(DataTypes.BIGINT()), 0))
                .watermark("ts", "ts - INTERVAL '5' SECOND")
                .build()
            )
    return t_env.from_data_stream(data_stream, schema)

    
def aggregate_stream(table: Table) -> Table:
    """Aggregates the Stream by Device Type and Window. This will count the number of users for each device type in a 1 minute window
    Very simple aggregation that generates a count of users based on device_type and locale, but shows how Table API can be used for realtime analytics

    Other examples of aggregations could be:
        1. Aggregate App Version and Device Type to see which versions are most popular on each device and watch upgrade trends
        2. Aggregate IP and Device Type to see if there are any IP addresses that are associated with multiple devices
        3. Aggregate Locale and Device Type to see if there are any locales that are more popular on certain devices

    Args:
        table (Table): Unaggregated Table

    Returns:
        Table: Aggregated Table containing the number of users for each device type in a 1 minute window
    """
    # Coalesece None Device Types to Unknown
    table = table.select(
        col('user_id'),
        col('device_type').if_null('Unknown').alias('device_type'),
        col('locale').if_null('Unknown').alias('locale'),
        col('ts')
    )

    table = table.window(Tumble.over(lit(1).minute).on(col("ts")).alias("w"))
    table = table.group_by(col('device_type'), col('locale'), col('w')) \
        .select(
            col('device_type'), 
            col('locale'),
            col('w').start.alias('window_start'), 
            col('w').end.alias('window_end'), 
            col('user_id').count.alias('user_count')
        )
    
    return table

def write_kafka_sink(ds: DataStream):
    """Writes the DataStream to Kafka Topic

    Args:
        ds (DataStream): DataStream containing aggregated data
    """
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

def run(stream_env: StreamExecutionEnvironment, t_env: StreamTableEnvironment):
    """Driver function to run the Flink Job

    Args:
        stream_env (StreamExecutionEnvironment): Streaming Environment for DataStream API
        t_env (StreamTableEnvironment): Table Environment for Table API
    """
    ds = read_kafka_source(stream_env)
    table = generate_table(t_env, ds)
    table = aggregate_stream(table)
    table.print_schema()

    ds = t_env.to_data_stream(table)

    # Convert the Row to a String so it can be sent to Kafka
    ds = ds.map(RowToStringMapFunction(), Types.STRING())

    # Write to Kafka
    write_kafka_sink(ds)
    stream_env.execute("Fetch Example Aggregation Stream")

if __name__ == "__main__":
    streaming_env = StreamExecutionEnvironment.get_execution_environment()

    # start a checkpoint every 1000 ms
    streaming_env.enable_checkpointing(1000)
    logger.info("Initialized Flink Stream Environment")

    table_env = StreamTableEnvironment.create(stream_execution_environment=streaming_env)

    run(streaming_env, table_env)