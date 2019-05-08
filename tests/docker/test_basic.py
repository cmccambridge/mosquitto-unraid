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

def run_once(create_mosquitto_container, command):
    mosquitto = create_mosquitto_container(command=command)
    mosquitto.start()
    mosquitto.wait()
    return mosquitto.logs()

def test_container_includes_mosquitto_sub(create_mosquitto_container):
    logs = run_once(create_mosquitto_container, command='/usr/bin/mosquitto_sub --help')
    assert b'mqtt' in logs
    assert b'mosquitto_sub version' in logs

def test_container_runs_mosquitto_sub_from_PATH(create_mosquitto_container):
    logs = run_once(create_mosquitto_container, command='mosquitto_sub --help')
    assert b'mqtt' in logs
    assert b'mosquitto_sub version' in logs

def test_container_includes_mosquitto_pub(create_mosquitto_container):
    logs = run_once(create_mosquitto_container, command='/usr/bin/mosquitto_pub --help')
    assert b'mqtt' in logs
    assert b'mosquitto_pub version' in logs

def test_container_runs_mosquitto_pub_from_PATH(create_mosquitto_container):
    logs = run_once(create_mosquitto_container, command='mosquitto_pub --help')
    assert b'mqtt' in logs
    assert b'mosquitto_pub version' in logs
