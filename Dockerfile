FROM eclipse-mosquitto:1.6.11

RUN cp /mosquitto/config/mosquitto.conf /mosquitto/mosquitto.conf.example
COPY docker-entrypoint.sh /
COPY include_dir.conf /mosquitto/include_dir.conf

ENTRYPOINT [ "/docker-entrypoint.sh" ]

CMD ["mosquitto"]
