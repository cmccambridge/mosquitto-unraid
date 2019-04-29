MKDIR_P := mkdir -p

.PHONY: all clean images test circleci-test

clean:
	rm -f mosquitto-unraid mosquitto-unraid-test
	docker image rm mosquitto-unraid
	docker image rm mosquitto-unraid-tests

images: mosquitto-unraid mosquitto-unraid-tests

mosquitto-unraid: Dockerfile include_dir.conf docker-entrypoint.sh
	docker build -t mosquitto-unraid . && touch mosquitto-unraid

mosquitto-unraid-tests: tests/Dockerfile tests/requirements.txt tests/run_tests.sh tests/docker/*.py
	docker build -t mosquitto-unraid-tests tests/ && touch mosquitto-unraid-tests

test: mosquitto-unraid mosquitto-unraid-tests
	$(MKDIR_P) test-results/docker
	$(eval CONTAINER := $(shell docker create -v /var/run/docker.sock:/var/run/docker.sock mosquitto-unraid-tests))
	docker start $(CONTAINER)
	TEST_RC=$$(docker wait $(CONTAINER));\
		docker logs $(CONTAINER);\
		docker cp $(CONTAINER):/tests/test-results/docker/. test-results/docker/;\
		docker rm $(CONTAINER);\
		exit $$TEST_RC

circleci-test: mosquitto-unraid mosquitto-unraid-tests
	$(MKDIR_P) test-results/docker
	$(eval CONTAINER := $(shell docker create -e DOCKER_HOST=$(DOCKER_HOST) -e DOCKER_CERT_PATH=$(DOCKER_CERT_PATH) -e DOCKER_MACHINE_NAME=$(DOCKER_MACHINE_NAME) -e DOCKER_TLS_VERIFY=$(DOCKER_TLS_VERIFY) -e NO_PROXY=$(NO_PROXY) mosquitto-unraid-tests))
	docker cp $(DOCKER_CERT_PATH) $(CONTAINER):$(DOCKER_CERT_PATH)
	docker inspect $(CONTAINER)
	docker start $(CONTAINER)
	TEST_RC=$$(docker wait $(CONTAINER));\
		docker logs $(CONTAINER);\
		docker cp $(CONTAINER):/tests/test-results/docker/. test-results/docker/;\
		docker rm $(CONTAINER);\
		exit $$TEST_RC