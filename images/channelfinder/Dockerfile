# ChannelFinder directory service (Spring Boot), built from source at a
# pinned tag. Backed by the `channelfinder-es` Elasticsearch service.
FROM maven:3.9-eclipse-temurin-17 AS build

ARG CF_VERSION=ChannelFinder-4.7.3

RUN git clone --depth 1 --branch ${CF_VERSION} \
        https://github.com/ChannelFinder/ChannelFinderService.git /cf
WORKDIR /cf
RUN mvn -q -B -DskipTests clean package

# ---------------------------------------------------------------- runtime
FROM eclipse-temurin:17-jre

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home --uid 905 channelfinder

COPY --from=build /cf/target/ChannelFinder-*.jar /opt/channelfinder/
RUN ln -s /opt/channelfinder/ChannelFinder-*.jar /opt/channelfinder/channelfinder.jar

USER channelfinder

# Site settings are mounted at /config/application.properties
ENV SPRING_CONFIG_ADDITIONAL_LOCATION=/config/

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/opt/channelfinder/channelfinder.jar"]
