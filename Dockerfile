ARG VERSION=1.5.3

FROM eclipse-mosquitto:$VERSION

RUN cp /mosquitto/config/mosquitto.conf /mosquitto/mosquitto.conf.example
COPY docker-entrypoint.sh /
COPY include_dir.conf /mosquitto/include_dir.conf

ENTRYPOINT [ "/docker-entrypoint.sh" ]

CMD ["mosquitto"]