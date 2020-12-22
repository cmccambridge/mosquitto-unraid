import re
from io import BytesIO
from time import sleep

import pytest

def test_container_dies_with_message_and_unraid_config_if_unmigrated(create_mosquitto_container):
    mosquitto = create_mosquitto_container()
    mosquitto.start()

    # Expect container to exit promptly, without explicit termination
    mosquitto.wait()
    assert b'MANUAL CONFIGURATION IS REQUIRED' in mosquitto.logs()

    conf = mosquitto.get_file('/mosquitto/config/mosquitto-unraid-default.conf')
    assert len(conf) > 0
    assert b'mosquitto-unraid' in conf


def test_creates_unraid_default_conf_if_migrated_but_missing(create_mosquitto_container):
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

    conf = mosquitto.get_file('/mosquitto/config/mosquitto-unraid-default.conf')
    assert len(conf) > 0
    assert b'mosquitto-unraid' in conf
    

def test_does_not_overwrite_unraid_default_conf_if_present(create_mosquitto_container):
    # Pre-populate mosquitto-unraid-default.conf with a customized file
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mosquitto-unraid-default.conf': 'mqtt_on_1885.conf'
            }
        )
    mosquitto.start()

    # Ensure container is up and running
    with mosquitto.connect(container_port=1885) as client:
        client.disconnect()

    mosquitto.stop()
    mosquitto.wait()

    conf = mosquitto.get_file('/mosquitto/config/mosquitto-unraid-default.conf')
    assert len(conf) > 0
    assert b'mosquitto-unraid' not in conf
    assert b'1885' in conf


def test_uses_insecure_default_if_override_env_var_set_properly(create_mosquitto_container):
    mosquitto_noenv = create_mosquitto_container()
    mosquitto_noenv.start()

    # Expect container to exit promptly, without explicit termination
    mosquitto_noenv.wait()
    assert b'MANUAL CONFIGURATION IS REQUIRED' in mosquitto_noenv.logs()
    assert b'Using insecure' not in mosquitto_noenv.logs()

    mosquitto_env = create_mosquitto_container(environment={"RUN_INSECURE_MQTT_SERVER": 1})
    mosquitto_env.start()

    # Ensure container is up and running
    with mosquitto_env.connect() as client:
        client.disconnect()

    mosquitto_env.stop()
    mosquitto_env.wait()

    assert b'Using insecure' in mosquitto_env.logs()


def test_no_insecure_default_if_override_env_var_set_wrong(create_mosquitto_container):
    mosquitto_wrong = create_mosquitto_container(environment={"RUN_INSECURE_MQTT_SERVER": 0})
    mosquitto_empty = create_mosquitto_container(environment={"RUN_INSECURE_MQTT_SERVER": 0})
    mosquitto_wrong.start()
    mosquitto_empty.start()

    # Expect container to exit promptly, without explicit termination
    mosquitto_wrong.wait()
    mosquitto_empty.wait()
    assert b'MANUAL CONFIGURATION IS REQUIRED' in mosquitto_wrong.logs()
    assert b'MANUAL CONFIGURATION IS REQUIRED' in mosquitto_empty.logs()


def test_uses_migrated_config_if_listener_configured(create_mosquitto_container):
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1885.conf': 'mqtt_on_1885.conf'
            }
        )
    mosquitto_env = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_on_1885.conf': 'mqtt_on_1885.conf'
            },
        environment={'RUN_INSECURE_MQTT_SERVER': 1}
        )

    # Ensure running on 1885 (mqtt_on_1885.conf)
    connected = 0
    for mq in [mosquitto, mosquitto_env]:
        mq.start()

        with mq.connect(container_port=1885):
            connected += 1
        mq.stop()
        mq.wait()

        assert b'Using insecure' not in mq.logs()
        assert b'include_dir.conf' in mq.logs()

    assert connected == 2


def test_uses_migrated_config_if_default_listener_configured(create_mosquitto_container):
    mosquitto = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_default_listener.conf': 'mqtt_default_listener.conf'
            }
        )
    mosquitto_env = create_mosquitto_container(
        initial_filespecs={
            '/mosquitto/config/mqtt_default_listener.conf': 'mqtt_default_listener.conf'
            },
        environment={'RUN_INSECURE_MQTT_SERVER': 1}
        )

    connected = 0
    for mq in [mosquitto, mosquitto_env]:
        mq.start()
        
        with mq.connect():
            connected += 1
        mq.stop()
        mq.wait()

        assert b'Using insecure' not in mq.logs()
        assert b'include_dir.conf' in mq.logs()

    assert connected == 2


def enable_config_options(conf_file, option_number):
    cur_option = 0
    if isinstance(conf_file, bytes):
        conf_file = conf_file.decode('utf-8')
    result = ''
    for line in conf_file.split('\n'):
        if m := re.match(r'# OPTION (\d+):.*', line):
            cur_option = int(m.group(1))
        if cur_option == option_number and (m := re.match(r'#(\S.*)', line)):
            line = m.group(1)
        result += f'{line}\n'
    return result


def test_default_config_option_1_sets_up_anonymous_listener(create_mosquitto_container):
    # 1. Create container without any configuration to generate default
    mosquitto = create_mosquitto_container()
    mosquitto.start()
    mosquitto.wait()
    assert b'MANUAL CONFIGURATION IS REQUIRED' in mosquitto.logs()

    # 2. Extract the default config file and edit
    conf = mosquitto.get_file('/mosquitto/config/mosquitto-unraid-default.conf')
    conf = enable_config_options(conf, 1)
    print(conf)

    # 3. Reinject the edited config
    mosquitto.put_files({
        '/mosquitto/config/mosquitto-unraid-default.conf': BytesIO(conf.encode('utf-8'))
        })

    # 4. Start the container and expect it to accept connections
    mosquitto.start()
    with mosquitto.connect() as client:
        client.disconnect()


def test_default_config_option_2_sets_up_password_listener(create_mosquitto_container):
    # single container, create passwd, user, connect with auth
    # 1. Create container without any configuration to generate default
    mosquitto = create_mosquitto_container()
    mosquitto.start()
    mosquitto.wait()
    assert b'MANUAL CONFIGURATION IS REQUIRED' in mosquitto.logs()

    # 2. Extract the default config file and edit to enable option 2: password_file
    conf = mosquitto.get_file('/mosquitto/config/mosquitto-unraid-default.conf')
    conf = enable_config_options(conf, 2)
    print(conf)

    # 3. Reinject the edited config and an empty initial password file
    mosquitto.put_files({
        '/mosquitto/config/mosquitto-unraid-default.conf': BytesIO(conf.encode('utf-8')),
        '/mosquitto/config/passwd': BytesIO(b'')
        })

    # 4. Start the container, create a password file, and signal Mosquitto to reload it
    mosquitto.start()
    USER = 'user1'
    PASSWORD = 'password1'
    mosquitto.exec_run(cmd=f'mosquitto_passwd -c -b /mosquitto/config/passwd {USER} {PASSWORD}')
    mosquitto.exec_run(cmd='killall -SIGHUP mosquitto')

    # 5. Expect anonymous connection to be REJECTED
    with pytest.raises(ConnectionError):
        with mosquitto.connect():
            assert False
    
    # 6. Expect incorrect user/password to be REJECTED
    with pytest.raises(ConnectionError):
        with mosquitto.connect(username=f'x{USER}x', password=f'no{PASSWORD}'):
            assert False
    
    # 7. Expect correct user/password to be accepted
    with mosquitto.connect(username=USER, password=PASSWORD) as client:
        client.disconnect()
