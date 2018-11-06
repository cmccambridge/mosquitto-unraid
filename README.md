![mosquitto logo](https://raw.githubusercontent.com/cmccambridge/mosquitto-unraid/master/media/eclipse-mosquitto.png)

# cmccambridge/mosquitto-unraid

This container is a minimal port of the official [Eclipse Mosquitto][eclipse-mosquitto] Docker container with minor tweaks to work more conveniently in unRAID.

* [Usage](#usage)
* [Volumes](#volumes)
* [Ports](#ports)
* [Configuration](#configuration)
* [unRAID Integration](#unraid-integration)

[eclipse-mosquitto]: https://mosquitto.org

## Usage

Quick & Easy:
1. Install from Community Applications
2. Configure port mappings
3. Done!

Full Custom:
```
docker create \
  -v <config directory>:/mosquitto/config \
  -v <data directory>:/mosquitto/data \
  -v <log directory>:/mosquitto/log \
  -p 1883:1883 \
  -p 8883:8883 \
  -p 9001:9001 \
  quay.io/cmccambridge/mosquitto-unraid
```

## Volumes

The following volumes are defined by the [official Docker image][official-docker] for Eclipse Mosquitto and are available for use in `mosquitto-unraid` as well:

|Volume|Description|
|---|---|
|`/mosquitto/config`|Directory holding `*.conf` files to configure mosquitto|
|`/mosquitto/data`|Directory to hold persistent data. Not enabled by default. See [persistent data](#persistent-data) configuration requirements.|
|`/mosquitto/log`|Directory to hold mosquitto logs. Not enabled by default. See [logging](#logging) configuration requirements.|

## Ports

The following ports are used by the default mosquitto configuration:

|Port|Description|
|---|---|
|1883|Standard MQTT port|
|8883|_Optional:_ frequently used as a MQTT TLS port. Not enabled by default. See [enabling TLS](#enabling-tls) configuration requirements.|
|9001|_Optional:_ standard MQTT Websockets port. Not enabled by default. See [Websockets](#websockets) configuration requirements.|

**Note:** You can modify the default listening ports through `*.conf` files, in which case you should update the corresponding port mappings as well.

## Configuration

To configure `mosquitto-unraid`, place one or more `*.conf` files in the volume bound to `/mosquitto/config`. If the container is run and no existing `mosquitto.conf.example` exists in the mounted volume, a new copy is created containing the [default contents][default-mosquitto-conf] of `mosquitto.conf`, which can be consulted as a reference.

For full details of the available configuration options, consult `man mosquitto.conf`, the [online documentation][online-man-page], or the [default content][default-mosquitto-conf] of `mosquitto.conf`.

[official-docker]: https://hub.docker.com/_/eclipse-mosquitto/
[default-mosquitto-conf]: https://github.com/eclipse/mosquitto/blob/master/mosquitto.conf
[online-man-page]: https://mosquitto.org/man/mosquitto-conf-5.html

### `mosquitto-unraid` Specifics

Mosquitto is typically configured through a single master config file named `mosquitto.conf`. However, for ease of use in the unRAID scenario, this container instead uses a default master config file containing only a single option:

```
include_dir /mosquitto/config
```

This configuration causes `mosquitto` to enumerate all `*.conf` files in the mount point `/mosquitto/config` and incorporate them into the shared configuration. You can create a single `mosquitto.conf` at this location, or a collection of separate `*.conf` files.

**Warning:** The order that individual `*.conf` files are applied to the `mosquitto` configuration is not necessarily alphabetical, and is determined by idiosynchrosies of the operating system and filesystem, so it is not safe to attempt to "override" settings in one file from another.

## Advanced Configuration

A quick reference follows for a few common advanced configuration topics. For full details of the available configuration options, consult `man mosquitto.conf`, the [online documentation][online-man-page], or the [default content][default-mosquitto-conf] of `mosquitto.conf`.

### Persistent Data
TODO

### Logging
TODO

### Enabling TLS
TODO

### Websockets
TODO

## unRAID Integration

If you're an [unRAID][unraid] user, you may want to install `mosquitto-unraid` through [Community Applications][ca] instead of directly installing this Docker image. The unRAID template will set some default settings that integrate well with unRAID (see below), as well as the latest updates if the container template itself changes over time.

Notes:
* _I'm using unRAID terminology such as_ `path` _and_ `variable` _here, for clarity, in place of Docker terminology_ `volume` _and_ `environment variable`.
* _You can also review these settings in the [mosquitto-unraid template][template] itself_

|Type|Setting|Value|Notes|
|----|-------|-----|-----|
|Path|`/mosquitto/config`|`/mnt/user/appdata/mosquitto`|Store mosquitto `*.conf` configuration files|
|Path|`/mosquitto/data`||Store persistent MQTT data|
|Path|`/mosquitto/log`||Store `mosquitto` logs|
|Port|1883|1883|Standard MQTT port|
|Port|8883|8883|_Optional:_ Common MQTT TLS port. Not enabled by default. See [enabling TLS](#enabling-tls) configuration requirements.|
|Port|9001|9001|_Optional:_ Standard MQTT Websockets port. Not enabled by default. See [Websockets](#websockets) configuration requirements.|

[unraid]: https://lime-technology.com/
[ca]: https://lime-technology.com/forums/topic/38582-plug-in-community-applications/
[template]: https://raw.githubusercontent.com/cmccambridge/unraid-templates/master/cmccambridge/mosquitto-unraid.xml

## Future Work

Please see the [GitHub Issues][issues], where you can report any problems or make any feature requests as well!

[issues]: https://github.com/cmccambridge/mosquitto-unriad/issues/

## Credits

The Eclipse Mosquitto logo