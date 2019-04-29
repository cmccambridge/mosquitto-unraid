from datetime import datetime, timedelta

import paho.mqtt.client as mqtt
import pytest

DOCKER_IMAGE = 'mosquitto-unraid'

def test_allows_cmd_override(create_mosquitto_container):
    # Dummy command that proves /bin/sh interpreted the input and this isn't some
    # program echoing back misunderstood arguments.
    mosquitto = create_mosquitto_container(command='/bin/sh -c \'f() { echo -n ${1:2}; echo -n ${1:0:2}; }; f "lohel"; f "stpyte";\'')
    mosquitto.start()
    rc = mosquitto.wait()
    assert rc == 0
    print(mosquitto.logs()) # WORKING - hmmmmm empty logs...
    assert any(b'hellopytest' in line for line in mosquitto.logs().splitlines())

def test_basic_functionality(create_mosquitto_container):
    mosquitto = create_mosquitto_container()

    mosquitto.start()
    ran = False
    with mosquitto.connect():
        ran = True
    assert ran
