#!/bin/ash
set -e

populate_defaults() {
    if [[ ! -f /mosquitto/config/mosquitto.conf.example ]]; then
        cp /mosquitto/mosquitto.conf.example /mosquitto/config/
    fi
}

initialize() {
    populate_defaults
}

if [[ "$1" == "mosquitto" ]]; then
    initialize

    exec /usr/sbin/mosquitto -c /mosquitto/include_dir.conf
fi

exec "$@"
