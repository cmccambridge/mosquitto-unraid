import logging
import os
import tarfile

from contextlib import contextmanager
from datetime import datetime, timedelta
from io import BytesIO
from time import sleep

import docker
import paho.mqtt.client as mqtt
import pytest

@pytest.fixture
def create_volume():
    docker_client = docker.from_env()
    volumes = []

    def _create_volume(name=None, **kwargs):
        """Create a docker volume with the given name (or None for
           an anonymous volume), which will be automatically deleted
           at the end of the test
        """
        volume = docker_client.volumes.create(name=name, **kwargs)
        volumes.append(volume)
        return volume

    yield _create_volume

    for volume in volumes:
        volume.remove(force=True)


@pytest.fixture
def create_container(request, create_volume):
    default_image_name = getattr(request.module, 'DOCKER_IMAGE', 'alpine')

    docker_client = docker.from_env()
    containers = []
    
    def _create_container(image_name=default_image_name, anonymous_volumes=None, **kwargs):
        """Create a docker container with the given parameters that will
           be automatically cleaned up at the end of the test
        """
        if anonymous_volumes:
            anon_volumes = {create_volume().id : mount for mount in anonymous_volumes}
            if 'volumes' not in kwargs:
                kwargs['volumes'] = {}
            if isinstance(kwargs['volumes'], dict):
                kwargs['volumes'].update({ vol_id : { 'bind': mount, 'mode': 'rw' } for vol_id, mount in anon_volumes.items() })
            else:
                kwargs['volumes'].extend([f'{vol_id}:{mount}' for vol_id, mount in anon_volumes.items()])

        container = docker_client.containers.create(image_name, **kwargs)
        containers.append(container)
        return container
    
    yield _create_container

    for container in containers:
        container.stop()
        container.remove(force=True)

def create_tar_archive(filespecs):
    tar_stream = BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        for archive_name, source in filespecs.items():
            if isinstance(source, str):
                tar.add(name=source, arcname=archive_name)
            else:
                # Assume BytesIO-like object
                tarinfo = tarfile.TarInfo(archive_name)
                tarinfo.size = len(source.getvalue())
                tar.addfile(tarinfo, fileobj=source)
    tar_stream.seek(0)
    return tar_stream


class MosquittoContainerHelper:
    def __init__(self, container, initial_filespecs=None):
        self.logger = logging.getLogger('MosquittoContainerHelper')
        self.container = container
        self.put_files(initial_filespecs)

    def start(self):
        return self.container.start()

    def stop(self):
        return self.container.stop()

    def exec_run(self, **kwargs):
        return self.container.exec_run(**kwargs)

    def logs(self):
        return self.container.logs()

    @contextmanager
    def connect(
            self,
            container_port=1883,
            protocol='tcp',
            timeout=timedelta(seconds=5),
            username=None,
            password=None
            ):
        container_host = self.get_container_ip()

        connection_rc = None
        def _on_connect(client, user_data, flags, rc):
            nonlocal connection_rc
            connection_rc = rc

        client = mqtt.Client()
        client.on_connect = _on_connect
        if username or password:
            client.username_pw_set(username, password)
        client.connect_async(container_host, port=container_port)

        try:
            client.loop_start()

            timeout_time = datetime.now() + timeout
            while datetime.now() < timeout_time and connection_rc is None:
                sleep(0.050)

            if connection_rc == 0:
                yield client
            else:
                raise ConnectionError()
        finally:
            client.disconnect()
            client.loop_stop()

    def wait(self, timeout=None):
        result = self.container.wait(timeout=timeout)
        rc = int(result['StatusCode'])
        self.logger.log(
            (logging.WARNING if rc != 0 else logging.DEBUG),
            'Container exited with status %d. Logs:\n%s',
            rc,
            self.logs()
        )
        return rc

    def cleanup(self):
        self.stop()

    def get_host_port(self, container_port):
        container_port = str(container_port)
        if '/' not in container_port:
            container_port = str(container_port) + '/tcp'
        # TODO: Waiting for next docker-py release which adds `.ports` attribute
        api_client = self.container.client.api
        port_bindings = api_client.inspect_container(self.container.id)['NetworkSettings']['Ports']
        if container_port in port_bindings:
            assert len(port_bindings[container_port]) == 1
            print(f'Binding for port {container_port}: {port_bindings[container_port][0]}')
            return int(port_bindings[container_port][0]['HostPort'])
        return None

    def get_container_ip(self):
        api_client = self.container.client.api
        return api_client.inspect_container(self.container.id)['NetworkSettings']['IPAddress']

    def put_files(self, filespecs):
        if not filespecs:
            return

        with create_tar_archive(filespecs) as tar:
            self.container.put_archive('/', tar)

    def get_file(self, path):
        stream, _ = self.container.get_archive(path)
        tar_io = BytesIO()
        for chunk in stream:
            tar_io.write(chunk)
        tar_io.seek(0)
        tar = tarfile.open(fileobj=tar_io)
        tar.list()
        file_io = BytesIO()
        for chunk in tar.extractfile(os.path.basename(path)):
            file_io.write(chunk)
        file_io.seek(0)
        return file_io.getvalue()


@pytest.fixture
def create_mosquitto_container(create_container, create_volume):
    helpers = []

    def _create_container(initial_filespecs=None, **kwargs):
        mounts = ['/mosquitto/config', '/mosquitto/log', '/mosquitto/data']
        ports = { '1883/tcp': None }

        container = create_container(
            image_name='mosquitto-unraid',
            anonymous_volumes = mounts,
            ports = ports,
            **kwargs
        )
        helper = MosquittoContainerHelper(container, initial_filespecs=initial_filespecs)
        helpers.append(helper)
        return helper

    yield _create_container

    for helper in helpers:
        helper.cleanup()
