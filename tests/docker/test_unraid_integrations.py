from datetime import timedelta
from time import sleep
import docker
import os
import pytest

def test_creates_example_mosquitto_conf(create_mosquitto_container):
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1883.conf': 'mqtt_on_1883.conf'
            }
        )
    mosquitto.start()

    # Ensure container is up and running
    with mosquitto.connect() as client:
        client.disconnect()
    
    mosquitto.stop()
    mosquitto.wait()

    conf = mosquitto.get_file('/mosquitto/config/mosquitto.conf.example')
    assert len(conf) > 0
    assert b'osquitto' in conf

def test_uses_include_dir_by_default(create_mosquitto_container, tmpdir):
    # Create mosquitto-unraid container with pre-injected mqtt_on_1885.conf file
    # to exercies the built-in include_dir support for *.conf files
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1885.conf': 'mqtt_on_1885.conf'
            }
        )
    mosquitto.start()

    # Ensure running on 1885 (mqtt_on_1885.conf)
    connected = False
    with mosquitto.connect(container_port=1885):
        connected = True

    # Ensure not running on 1883 (default)
    with pytest.raises(ConnectionError):
        with mosquitto.connect(container_port=1883, timeout=timedelta(seconds=1)):
            assert False

    assert connected

def test_end_to_end_pub_sub_cli(create_mosquitto_container):
    # Create an MQTT server on default port 1883
    server = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1883.conf': 'mqtt_on_1883.conf'
            }
        )
    server.start()

    # Create an MQTT subscriber listening up to 30 seconds for 1 message on /test/topic
    sub = create_mosquitto_container(command=f'/usr/bin/mosquitto_sub -h {server.get_container_ip()} -p 1883 -t /test/topic -C 1 -W 30')
    sub.start()

    # Finally, use an MQTT publisher to push a message to /test/topic
    message = b'mqtt_test_mesage'
    pub = create_mosquitto_container(command=f'/usr/bin/mosquitto_pub -h {server.get_container_ip()} -p 1883 -t /test/topic -m \'f{message}\'')
    pub.start()
    pub.wait()

    sub.wait()

    # Inspect subscriber's logs, expecting to see the message from the publisher
    assert message in sub.logs()

def test_end_to_end_pub_sub_cli_single_container(create_mosquitto_container):
    # Create an MQTT server on dfeault port 1883
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1883.conf': 'mqtt_on_1883.conf'
            }
        )
    mosquitto.start()

    # Create an MQTT subscriber listening up to 30 seconds for 1 message on /test/topic
    (sub_rc, sub_logs) = mosquitto.exec_run(
        cmd=f'/usr/bin/mosquitto_sub -h 127.0.0.1 -p 1883 -t /test/topic -C 1 -W 30',
        stream=True
        )

    # Finally, use an MQTT publisher to push a message to /test/topic
    message = b'mqtt_test_mesage'
    (pub_rc, pub_logs) = mosquitto.exec_run(
        cmd=f'/usr/bin/mosquitto_pub -h 127.0.0.1 -p 1883 -t /test/topic -m \'f{message}\'',
        stream=True
        )

    # Inspect subscriber's logs, expecting to see the message from the publisher
    assert any(message in line for line in sub_logs)
