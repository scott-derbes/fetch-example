# fetch-example

# Overview
This is a simple Flink application to read from a Kafka stream, perform a basic aggregation, and then write to a Kafka topic. 

The main script running the Flink code can be found in `src/aggregate_stream.py`

There is also a secondary script that generates a Kafka Topic under `src/generate_kafka_topic.py`

# Running Locally
This application will require that you have Docker and Python installed on your computer. 

In order to ensure your local environment is set up properly, run the command `make build_local_env`. This will generate a virtual environment and install the needed Pip packages

In order to build the local Docker container, run the command `make build_local_flink_image`. This will be used for the Flink and Kafka Topic Generator Script

In order to launch the Flink job run `make run_compose`. This will kick off the Docker Compose steps starting the local environment. Once the Flink job is running, the Flink UI can be accessed at [this url](http://localhost:8081/)

# Additional Question Answers:

1. How would you deploy this application in production?
    - I would either use a tool like Kubernetes where I can deploy Zookeeper and Flink in their own pods or a managed service like AWS Managed Flink. I would most likely submit the jobs using the Session Mode, and then set up checkpoints and store the data off the local filesystem like S3 to allow recovery in the event that the Flink jobs dies.

2. What other components would you want to add to make this production ready?
    - I think the biggest thing this will need is better observability. In order to ensure that the service is constantly up and not being over-utilized, I would use a tool Datadog and set up alerts with Slack and Email for Task Failures and high resource utilization. 

3. How can this application scale with a growing dataset?
    - This application should scale fairly well with an increasing dataset as long as the cluster it is running on has proper autoscaling rules. Flink would just need a way to add more task nodes to handle its data processing