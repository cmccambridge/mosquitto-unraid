FROM eclipse-mosquitto:2.0.14

LABEL maintainer="Colin McCambridge <colin@mccambridge.org>" \
    description="mosquitto-unraid: Eclipse Mosquitto Broker tweaked for unRAID"

RUN apk add --no-cache \
        tzdata

COPY docker-entrypoint.sh /
COPY *.conf /mosquitto-unraid/
RUN cp /mosquitto/config/mosquitto.conf /mosquitto-unraid/mosquitto.conf.example

ENTRYPOINT [ "/docker-entrypoint.sh" ]

CMD ["mosquitto"]
