# fetch-example

# Overview
In order to solve the problem of reading from a Kafka stream, performing transformations, and writing to a new a Kafka topic I chose to use Apache Flink.
Flink allowed me to easily have access to a series of tools that would allow this pipeline to scale in the event that this needed to go production.

If I were moving this to production, I would use Zookeeper instead of my current local approach to allow for High Availability in the event that a JobManager node failed. 