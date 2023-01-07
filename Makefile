MKDIR_P := mkdir -p

.PHONY: all clean images test release

all: images test

clean:
	-rm -f mosquitto-unraid mosquitto-unraid-tests
	-docker image rm mosquitto-unraid
	-docker image rm mosquitto-unraid-tests

images: mosquitto-unraid mosquitto-unraid-tests

mosquitto-unraid: Dockerfile *.conf docker-entrypoint.sh
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

release:
ifndef RELEASE_TAG
	$(error Missing RELEASE_TAG)
endif
	docker pull cmccambridge/mosquitto-unraid:beta
	docker tag cmccambridge/mosquitto-unraid:beta cmccambridge/mosquitto-unraid:$(RELEASE_TAG)
	docker push cmccambridge/mosquitto-unraid:$(RELEASE_TAG)