#!/bin/ash
set -e

populate_defaults() {
    if [[ ! -f /mosquitto/config/mosquitto.conf.example ]]; then
        cp /mosquitto-unraid/mosquitto.conf.example /mosquitto/config/
    fi
}

mosquitto_1_to_2_migration() {
    # If the user doesn't already have a copy of the mosquitto-unraid default
    # config file, create it now.
    # NOTE: The default file does NOTHING until the user uncomments lines.
    if [[ ! -f /mosquitto/config/mosquitto-unraid-default.conf ]]; then
        cp /mosquitto-unraid/mosquitto-unraid-default.conf /mosquitto/config/
    fi

    # We presume the standard include_dir.conf unless overridden to the
    # insecure version below
    MOSQUITTO_CONFIG_FILE="/mosquitto-unraid/include_dir.conf"

    # Verify that the user has a configured listener, and appears to be
    # compliant with the Mosquitto 2.0 migration requirements
    if ! grep -q -E "^\s*(listener|port)\s+\d+" /mosquitto/config/*.conf ; then

        # Check for user override via environment variable
        if [[ "${RUN_INSECURE_MQTT_SERVER}" == 1 ]]; then
            echo "RUN_INSECURE_MQTT_SERVER = 1. Using insecure MQTT listener settings:"
            echo "Bind port 1883 on all interfaces, and allow anonymous connections."
            MOSQUITTO_CONFIG_FILE="/mosquitto-unraid/include_dir_and_insecure_listener.conf"
        else
            echo "!! ATTENTION: MANUAL CONFIGURATION IS REQUIRED !!"
            echo
            echo "Due to security hardening in Mosquitto 2.0, you MUST TAKE MANUAL ACTION to"
            echo "reenable MQTT in this container!"
            echo
            echo "OPTION 1: Set RUN_INSECURE_MQTT_SERVER to 1 in this container's settings"
            echo
            echo "OPTION 2: Edit the file \"mosquitto-unraid-default.conf\" in your configuration"
            echo "path for more details (Usually /mnt/user/appdata/mosquitto)"
            echo
            echo "OPTION 3: Update your customized Mosquitto configuration to configure at"
            echo "least one listener. See https://mosquitto.org/documentation/migrating-to-2-0/"

            # We will NOT launch this container until the user manually migrates
            # or overrides this security step with RUN_UN==INSECURE_MQTT_SERVER=1
            exit 1
        fi
    fi
}

initialize() {
    populate_defaults
    mosquitto_1_to_2_migration
}

if [[ "$1" == "mosquitto" ]]; then
    initialize

    exec /usr/sbin/mosquitto -c ${MOSQUITTO_CONFIG_FILE}
fi

exec "$@"
