from time import sleep
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
    print(f'{conf[:100]}')
    assert len(conf) > 0

@pytest.mark.skip(reason='Not yet implemented')
def test_uses_include_dir_by_default():
    pass

@pytest.mark.skip(reason='Not yet implemented')
def test_container_includes_mosquitto_sub():
    pass

@pytest.mark.skip(reason='Not yet implemented')
def test_container_includes_mosquitto_pub():
    pass
