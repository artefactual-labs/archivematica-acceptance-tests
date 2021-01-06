#!/usr/bin/env bash

set -e

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the black-box tests if tags are not provided
TAGS=${1:-black-box}

cd ${__dir}

# Build containers
env COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build --parallel archivematica-mcp-server archivematica-mcp-client archivematica-dashboard archivematica-storage-service

# Create databases
docker-compose up -d mysql
docker-compose run --rm --entrypoint bash -v $PWD:/tmp mysql /tmp/wait-for-it.sh mysql:3306 --timeout=30
docker-compose exec -T mysql mysql -h mysql -P 3306 --protocol=tcp -uroot -p12345 -e "DROP DATABASE IF EXISTS SS; CREATE DATABASE SS; GRANT ALL ON SS.* TO 'archivematica'@'%' IDENTIFIED BY 'demo';"
docker-compose exec -T mysql mysql -h mysql -P 3306 --protocol=tcp -uroot -p12345 -e "DROP DATABASE IF EXISTS MCP; CREATE DATABASE MCP; GRANT ALL ON MCP.* TO 'archivematica'@'%' IDENTIFIED BY 'demo';"

# Bootstrap services
docker-compose up -d archivematica-mcp-server archivematica-mcp-client archivematica-dashboard archivematica-storage-service
docker-compose run --rm --entrypoint python archivematica-storage-service /src/storage_service/manage.py migrate --noinput
docker-compose run --rm --entrypoint python archivematica-storage-service /src/storage_service/manage.py create_user --username="test" --password="test" --email="test@test.com" --api-key="test" --superuser
docker-compose restart archivematica-storage-service
docker-compose run --rm --entrypoint /src/dashboard/src/manage.py archivematica-dashboard migrate --noinput
docker-compose run --rm --entrypoint /src/dashboard/src/manage.py archivematica-dashboard install --username="test" --password="test" --email="test@test.com" --org-name="test" --org-id="test" --api-key="test" --ss-url="http://archivematica-storage-service:8000" --ss-user="test" --ss-api-key="test" --site-url="http://archivematica-dashboard:8000"

# Restart services
docker-compose up -d archivematica-mcp-server archivematica-mcp-client archivematica-dashboard archivematica-storage-service nginx

# Run AMAUAT tag
docker-compose run --rm -e HEADLESS=1 --no-deps archivematica-acceptance-tests /usr/local/bin/behave --no-capture --no-capture-stderr --no-logcapture --tags=$TAGS --no-skipped --stop -v -D driver_name=Firefox -D ssh_accessible=no -D am_url=http://nginx/ -D am_username=test -D am_password=test -D am_api_key=test -D am_version=1.8 -D ss_url=http://nginx:8000/ -D ss_username=test -D ss_password=test -D ss_api_key=test -D transfer_source_path=archivematica/archivematica-sampledata/TestTransfers/acceptance-tests -D home=archivematica

# Tear down containers
docker-compose down --volumes
