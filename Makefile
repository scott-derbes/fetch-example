image_name := fetch_kafka_transformation

build_local_env:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Use the platform build argument even thoughim using mac m1
# Flink had issues building on my mac, and I used platform argument instead of altering the 
# dockerfile to install openjdk which also worked
build_local_flink_image:
	docker build --platform linux/amd64 -t fetch-example-flink-transform:latest .

run_compose:
	docker compose -f docker-compose.yml up