# Phoebus alarm server, built from source at a pinned tag so the image is
# reproducible. Kafka topics are created by the `kafka-init` compose service.
FROM maven:3.9-eclipse-temurin-17 AS build

ARG PHOEBUS_VERSION=v4.7.3

RUN git clone --depth 1 --branch ${PHOEBUS_VERSION} \
        https://github.com/ControlSystemStudio/phoebus.git /phoebus
WORKDIR /phoebus
RUN mvn -q -B -DskipTests -pl services/alarm-server -am install

# ---------------------------------------------------------------- runtime
FROM eclipse-temurin:17-jre

RUN useradd --system --create-home --uid 903 alarm

COPY --from=build /phoebus/services/alarm-server/target/lib /opt/alarm-server/lib
COPY --from=build /phoebus/services/alarm-server/target/service-alarm-server-*.jar /opt/alarm-server/

RUN ln -s /opt/alarm-server/service-alarm-server-*.jar /opt/alarm-server/service-alarm-server.jar

USER alarm

# Settings and alarm configuration are mounted at /config (see alarms/)
ENTRYPOINT ["java", "-jar", "/opt/alarm-server/service-alarm-server.jar"]
CMD ["-settings", "/config/alarm-server.ini", "-config", "Lab", "-noshell"]
