#!/bin/bash
set -e
mkdir -p test-results/docker
ls ${DOCKER_CERT_PATH}
pytest --junit-xml=test-results/docker/results.xml ./