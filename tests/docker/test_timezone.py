def test_default_timezone_is_utc(create_mosquitto_container):
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1883.conf': 'mqtt_on_1883.conf',
            '/mosquitto/config/log_timestamps.conf': 'log_timestamps.conf'
            }
        )
    mosquitto.start()

    # Ensure container is up, running, and logging messages
    with mosquitto.connect() as client:
        client.disconnect()

    mosquitto.stop()
    mosquitto.wait()

    assert b'@@Z+0000@@' in mosquitto.logs()

def test_timzeone_can_be_overridden(create_mosquitto_container):
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1883.conf': 'mqtt_on_1883.conf',
            '/mosquitto/config/log_timestamps.conf': 'log_timestamps.conf'
            },
        environment={
            'TZ': 'US/Hawaii'  # NB: Constant UTC-10 offset due to no DST
        }
        )
    mosquitto.start()

    # Ensure container is up, running, and logging messages
    with mosquitto.connect() as client:
        client.disconnect()

    mosquitto.stop()
    mosquitto.wait()

    assert b'@@Z-1000@@' in mosquitto.logs()
