from datetime import timedelta
from time import sleep
import docker
import os
import pytest

def test_creates_example_mosquitto_conf(create_mosquitto_container):
    mosquitto = create_mosquitto_container()
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

@pytest.mark.skip(reason='Test not yet implemented')
def test_container_includes_mosquitto_sub():
    pass

@pytest.mark.skip(reason='Test not yet implemented')
def test_container_includes_mosquitto_pub():
    pass
