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

def test_container_includes_mosquitto_sub(create_mosquitto_container):
    mosquitto_sub = create_mosquitto_container(command='/usr/bin/mosquitto_sub --help')
    mosquitto_sub.start()
    mosquitto_sub.wait()

    logs = mosquitto_sub.logs()
    assert b'mqtt' in logs
    assert b'mosquitto_sub version' in logs

def test_container_includes_mosquitto_pub(create_mosquitto_container):
    mosquitto_pub = create_mosquitto_container(command='/usr/bin/mosquitto_pub --help')
    mosquitto_pub.start()
    mosquitto_pub.wait()

    logs = mosquitto_pub.logs()
    assert b'mqtt' in logs
    assert b'mosquitto_pub version' in logs
