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
    mqtt_port = mosquitto.get_host_port(1883)
    assert mqtt_port is not None

    connection_rc = None
    def on_connect(client, user_data, flags, rc):
        nonlocal connection_rc
        connection_rc = rc
        client.disconnect()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("127.0.0.1", port=mqtt_port)

    timeout_time = datetime.now() + timedelta(seconds=5)
    while datetime.now() < timeout_time and connection_rc is None:
        client.loop()

    assert connection_rc == 0
