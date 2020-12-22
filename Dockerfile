FROM eclipse-mosquitto:2.0.3

LABEL maintainer="Colin McCambridge <colin@mccambridge.org>" \
    description="mosquitto-unraid: Eclipse Mosquitto Broker tweaked for unRAID"

RUN cp /mosquitto/config/mosquitto.conf /mosquitto/mosquitto.conf.example
COPY docker-entrypoint.sh /
COPY include_dir.conf /mosquitto/include_dir.conf

ENTRYPOINT [ "/docker-entrypoint.sh" ]

CMD ["mosquitto"]
