FROM flink:1.19.1

RUN curl -L https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.19/flink-sql-connector-kafka-3.3.0-1.19.jar -o /opt/flink/lib/flink-sql-connector-kafka-3.3.0.1.19.jar

# Dockerfile Inspired By: https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/deployment/resource-providers/standalone/docker/#using-flink-python-on-docker

# install python3 and pip3
RUN apt-get update -y && \
apt-get install -y python3 python3-pip python3-dev && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/python3 /usr/bin/python

COPY requirements.txt tmp/requirements.txt

# install PyFlink and other Python Packages
RUN pip3 install -r tmp/requirements.txt