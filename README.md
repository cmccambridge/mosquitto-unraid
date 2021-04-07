![mosquitto logo](https://raw.githubusercontent.com/cmccambridge/mosquitto-unraid/master/media/eclipse-mosquitto.png)

# cmccambridge/mosquitto-unraid
[![](https://img.shields.io/circleci/project/github/cmccambridge/mosquitto-unraid/master.svg)](https://circleci.com/gh/cmccambridge/mosquitto-unraid/tree/master) [![](https://img.shields.io/docker/pulls/cmccambridge/mosquitto-unraid.svg)](https://hub.docker.com/r/cmccambridge/mosquitto-unraid/)

This container is a minimal port of the official [Eclipse Mosquitto][eclipse-mosquitto] Docker container with minor tweaks to work more conveniently in unRAID.

> # Breaking Change: Mosquitto 2.x
> **You must take manual action to update your `mosquitto-unraid` configuration** as per the [2.x Breaking Change](#breaking-change) section below.
>
> `mosquitto-unraid` has taken a breaking change from the upstream Eclipse Mosquitto project to restrict access to unauthenticated clients and non-loopback networks without explicit configuration.

* [Usage](#usage)
* [Environment Variables](#environment-variables)
* [Volumes](#volumes)
* [Ports](#ports)
* [Configuration](#configuration)
* [Advanced Configuration](#advanced-configuration)
* [Command Line MQTT Clients](#command-line-mqtt-clients)
* [unRAID Integration](#unraid-integration)
* [2.x Breaking Change](#breaking-change)

[eclipse-mosquitto]: https://mosquitto.org

## Usage

Quick & Easy:
1. Install from [Community Applications][ca]
2. Configure port mappings
3. Enable `RUN_INSECURE_MQTT_SERVER` **or** set up an [authenticated configuration](#authentication)
4. Done!

Full Custom:
```
docker create \
  -v <config directory>:/mosquitto/config \
  -v <data directory>:/mosquitto/data \
  -v <log directory>:/mosquitto/log \
  -p 1883:1883 \
  -p 8883:8883 \
  -p 9001:9001 \
  -e RUN_INSECURE_MQTT_SERVER=1 \
  cmccambridge/mosquitto-unraid
```

## Environment Variables

The following environment variables may be used to configure `mosquitto-unraid`:

|Environment Variable|Default|Description|
|---|---|---|
|`RUN_INSECURE_MQTT_SERVER`|_not set_|Set this environment variable to `1` to run an insecure default MQTT server accepting anonymous clients on port 1883. Any other value will have no effect.<br/><br/>This was the default configuration prior to Mosquitto 2.0.0. For more information, refer to the [2.x Breaking Change](#breaking-change) section.|

## Volumes

The following volumes are defined by the [official Docker image][official-docker] for Eclipse Mosquitto and are available for use in `mosquitto-unraid` as well:

|Volume|Description|
|---|---|
|`/mosquitto/config`|Directory holding `*.conf` files to configure mosquitto|
|`/mosquitto/data`|Directory to hold persistent data. Not enabled by default. See [persistent data](#persistent-data) configuration requirements.|
|`/mosquitto/log`|Directory to hold mosquitto logs. Not enabled by default. See [logging](#logging) configuration requirements.|

## Ports

The following ports are standard MQTT ports:

|Port|Description|
|---|---|
|1883|Standard MQTT port|
|8883|_Optional:_ Frequently used as a MQTT TLS port. Not enabled by default. See [enabling TLS](#enabling-tls) configuration requirements.|
|9001|_Optional:_ Standard MQTT Websockets port. Not enabled by default. See [Websockets](#websockets) configuration requirements.|

**Note:** Starting with Mosquitto 2.0.0, no listener will be started without explicit configuration. You can define listening ports through `*.conf` files, or enable a default insecure MQTT listener on port 1883 using the `RUN_INSECURE_MQTT_SERVER` environment variable. If you configure custom listeners, you should update the corresponding port mappings as well.

## Configuration

To configure `mosquitto-unraid`, place one or more `*.conf` files in the volume bound to `/mosquitto/config`. If the container is run and no existing `mosquitto.conf.example` exists in the mounted volume, a new copy is created containing the [default contents][default-mosquitto-conf] of `mosquitto.conf`, which can be consulted as a reference.

Starting with Mosquitto 2.0.0, you **must** explicitly configure listeners, or set the `RUN_INSECURE_MQTT_SERVER` override variable. If the container is run and no listeners have been explicitly configured and the override variable is not set, then a `mosquitto-unraid-default.conf` file will be generated in the `/mosquitto/config` volume with examples of valid explicit configurations, and the container will terminate with instructions printed to the logs.

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

For example, you might create the following files:

|File|Content|
|----|-------|
|`mosquitto.conf`|Master mosquitto config file|
|`tls.conf`|Additional listener config for TLS|
|`websockets.conf`|Additional listener config for Websockets|

**Warning:** The order that individual `*.conf` files are applied to the `mosquitto` configuration is not necessarily alphabetical, and is determined by idiosynchrosies of the operating system and filesystem, so it is not safe to attempt to "override" settings in one file from another.

## Advanced Configuration

A quick reference follows for a few common advanced configuration topics. For full details of the available configuration options, consult `man mosquitto.conf`, the [online documentation][online-man-page], or the [default content][default-mosquitto-conf] of `mosquitto.conf`.

### Persistent Data

To enable persistent data, set the following configuration options in your `mosquitto.conf` or another `*.conf` [configuration](#configuration) file:

```
persistence true
persistence_location /mosquitto/data/
```

Restart the container for your changes to take effect.

### Logging

To enable logging, set the following configuration options in your `mosquitto.conf` or another `*.conf` [configuration](#configuration) file, uncommenting your desired log level(s):

```
log_dest file /mosquitto/log/mosquitto.log
log_type error
#log_type warning
#log_type notice
#log_type information
```

Restart the container for your changes to take effect.

### Authentication

To enable password-based authentication, you'll need to run `mosquitto_passwd` within the Docker container. For persistence of the generated file across container invocations, it is _highly_ recommended that you store it in the same mounted volume as your configuration file, i.e. `/mosquitto/config`.

You can run `mosquitto_passwd` to create and manage your password file in a container named `mosquitto` like this:

```
# Create the file if it does not yet exist
docker exec -it mosquitto touch /mosquitto/config/passwd

# Create a new user named user_name, enter password interactively
docker exec -it mosquitto mosquitto_passwd /mosquitto/config/passwd user_name

# Create a new user named user_2 with password pass_2.
# WARNING: pass_2 will appear in your command history!
docker exec -it mosquitto mosquitto_passwd -b /mosquitto/config/passwd user_2 pass_2

# Delete a user named user_2
docker exec -it mosquitto mosquitto_passwd -D /mosquitto/config/passwd user_2
```

You can then refer to the password file from your configuration:

```
password_file /mosquitto/config/passwd
```

Restart the container for your changes to take effect.

### Enabling TLS
TODO

_In the meantime, consult the [official documentation][official-docs]_

[official-docs]: http://mosquitto.org/man/mosquitto-conf-5.html

### Websockets
TODO

_In the meantime, consult the [official documentation][official-docs]_

## Command Line MQTT Clients

For convenience of testing MQTT environments, this container includes the command-line interface tools `mosquitto_sub` and `mosquitto_pub`. You can find the details of their usage in their respective man pages ([`mosquitto_sub`][man-mosquitto_sub], [`mosquitto_pub`][man-mosquitto_pub]), but here are some quick examples:

Use `mosquitto_sub` in a new container to subscribe to an MQTT topic `$MQTT_TOPIC` on a remote host `$MQTT_HOST`:
```
docker run --rm -it mosquitto-unraid mosquitto_sub -h ${MQTT_HOST} -p 1883 -t ${MQTT_TOPIC}
```

Use `mosquitto_pub` to publish a message `$MQTT_MESSAGE` to an MQTT topic `$MQTT_TOPIC` on the mosquitto instance in an _existing_ running `mosquitto-unraid` container named `$CONTAINER`:
```
docker exec -it ${CONTAINER} mosquitto_pub -h 127.0.0.1 -p 1883 -t ${MQTT_TOPIC} -m ${MQTT_MESSAGE}
```

[man-mosquitto_sub]: https://mosquitto.org/man/mosquitto_sub-1.html
[man-mosquitto_pub]: https://mosquitto.org/man/mosquitto_pub-1.html

## unRAID Integration

If you're an [unRAID][unraid] user, you may want to install `mosquitto-unraid` through [Community Applications][ca] instead of directly installing this Docker image. The unRAID template will set some default settings that integrate well with unRAID (see below), as well as the latest updates if the container template itself changes over time.

Notes:
* _I'm using unRAID terminology such as_ `path` _and_ `variable` _here, for clarity, in place of Docker terminology_ `volume` _and_ `environment variable`.
* _You can also review these settings in the [mosquitto-unraid template][template] itself_

|Type|Setting|Value|Notes|
|----|-------|-----|-----|
|Variable|`RUN_INSECURE_MQTT_SERVER`|`0`|Set to `1` to enable a default insecure MQTT server on port 1883. See [Environment Variables](#environment-variables)|
|Path|`/mosquitto/config`|`/mnt/user/appdata/mosquitto`|Store mosquitto `*.conf` configuration files|
|Path|`/mosquitto/data`||Store persistent MQTT data|
|Path|`/mosquitto/log`||Store `mosquitto` logs|
|Port|1883|1883|Standard MQTT port|
|Port|8883|8883|_Optional:_ Common MQTT TLS port. Not enabled by default. See [enabling TLS](#enabling-tls) configuration requirements.|
|Port|9001|9001|_Optional:_ Standard MQTT Websockets port. Not enabled by default. See [Websockets](#websockets) configuration requirements.|

[unraid]: https://lime-technology.com/
[ca]: https://lime-technology.com/forums/topic/38582-plug-in-community-applications/
[template]: https://raw.githubusercontent.com/cmccambridge/unraid-templates/master/cmccambridge/mosquitto-unraid.xml

## 2.x Breaking Change <a name="breaking-change"></a>

The upstream Eclipse Mosquitto project has taken a breaking change with their 2.x series of releases, beginning with 2.0.0. `mosquitto-unraid` has taken this breaking change as well to comply with the upstream change in security posture.

**This change will require manual configuration update if you have _not_ previously configured a custom MQTT listener.**

In short, the container now requires that you either:
1. Explicitly configure an MQTT listener **or**
2. Explicitly set the environment variable `RUN_INSECURE_MQTT_SERVER=1` to re-enable the 1.x series default configuration.

To learn more about the details and motivation for the upstream change, you can read the [Mosquitto 2.0 release notes](https://mosquitto.org/blog/2020/12/version-2-0-0-released/) or the Eclipse [migration guide](https://mosquitto.org/documentation/migrating-to-2-0/).

To migrate your existing `mosquitto-unraid` container, take one of the following paths:

### Option 1: Set `RUN_INSECURE_MQTT_SERVER` to `1` in this container's configuration
Update your docker command line or unRAID variables to set the environment variable `RUN_INSECURE_MQTT_SERVER` = `1`. This will enable the same insecure default settings that were in effect by default in the Mosquitto 1.x series:
* A default listener on port 1883
* Anonymous (unauthenticated) connections

These settings corresponding with this configuration snippet:
```
listener 1883
protocol mqtt
allow_anonymous true
```

### Option 2: Edit the generated file `mosquitto-unraid-default.conf`
If `mosquitto-unraid` detects that it is started in an unmigrated configuration (i.e. with no explicit listener configured and without `RUN_INSECURE_MQTT_SERVER` set), then the container will create a default configuration file in the `/mosquitto/config` volume.

This default configuration file contains a few simple examples which can be uncommented to satisfy the explicit configuration requirement, including:
* A Mosquitto 1.x-like anonymous connections on port 1883 configuration, identical to the `RUN_INSECURE_MQTT_SERVER` configuration.
* A password-file authentication configuration which requires additional steps to establish user accounts. See [Authentication](#authentication) for more information on creating user accounts.

See the generated `mosquitto-unraid-default.conf` file for further details.

### Option 3: Configure Mosquitto to your preferences, including at least one listener
See the [Configuration](#configuration) section for more details.

## Future Work

Please see the [GitHub Issues][issues], where you can report any problems or make any feature requests as well!

[issues]: https://github.com/cmccambridge/mosquitto-unraid/issues/

## Credits

The Eclipse Mosquitto logo

## CHANGELOG <a name="changelog"></a>

**2.0.10 (2021-04-06)**
* Upgrade to [upstream 2.0.10 release](https://mosquitto.org/blog/2021/04/version-2-0-10-released/)
* This upstream update includes security fixes

**2.0.9 (2021-03-14)**
* Upgrade to [upstream 2.0.9 release](http://www.mosquitto.org/blog/2021/03/version-2-0-9-released/)

**2.0.8 (2021-03-01)**
* Upgrade to upstream 2.0.8 release

**2.0.7 (2021-02-05)**
* Upgrade to upstream 2.0.7 release

**2.0.6 (2021-02-04)**
* Upgrade to upstream 2.0.6 release

**2.0.5 (2021-01-20)**
* **BREAKING CHANGE: Manual Configuration Required**
* Upgrade to upstream 2.0.5 release, the first 2.x release supported by `mosquitto-unraid`
* Follow upstream security posture: Without explicit configuration, do not run a wide open MQTT server
* Add migration logic and document breaking changes in README:
    - On container start, check for user-defined listeners or customization of default listener
    - If no listeners, check for override variable `RUN_INSECURE_MQTT_SERVER`
    - If no listeners and no override, exit the container with a message.
