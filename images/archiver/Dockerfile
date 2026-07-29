# EPICS Archiver Appliance — single-JVM deployment (all four webapps in one
# Tomcat), suitable for a lab-scale installation. The config database lives
# in the `archiver-db` MariaDB service.
# AA 1.1.0 class files target Java 16 — needs a JDK 17 Tomcat.
FROM tomcat:9-jdk17-temurin

ARG AA_VERSION=1.1.0
ARG MYSQL_CONNECTOR_VERSION=8.0.33

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl default-mysql-client gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Deploy the four appliance WARs and keep the MySQL schema for first boot.
RUN curl -fsSL -o /tmp/archappl.tar.gz \
        "https://github.com/archiver-appliance/epicsarchiverap/releases/download/${AA_VERSION}/archappl_v${AA_VERSION}.tar.gz" \
    && mkdir -p /tmp/aa /opt/archappl/sql /opt/archappl/conf \
    && tar -xzf /tmp/archappl.tar.gz -C /tmp/aa \
    && rm -rf /usr/local/tomcat/webapps/* \
    && find /tmp/aa -name '*.war' -exec cp {} /usr/local/tomcat/webapps/ \; \
    && find /tmp/aa -iname '*mysql*.sql' -exec cp {} /opt/archappl/sql/archappl_mysql.sql \; \
    && test -f /opt/archappl/sql/archappl_mysql.sql \
    && rm -rf /tmp/aa /tmp/archappl.tar.gz

# JDBC driver for the JNDI datasource.
RUN curl -fsSL -o /usr/local/tomcat/lib/mysql-connector-j.jar \
    "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/${MYSQL_CONNECTOR_VERSION}/mysql-connector-j-${MYSQL_CONNECTOR_VERSION}.jar"

# The appliance is addressed on 17665 everywhere (see conf/appliances.xml).
RUN sed -i 's/port="8080"/port="17665"/' /usr/local/tomcat/conf/server.xml

COPY conf/appliances.xml /opt/archappl/conf/appliances.xml
COPY conf/context.xml.template /opt/archappl/conf/context.xml.template
COPY archappl-entrypoint.sh /usr/local/bin/archappl-entrypoint.sh
RUN chmod +x /usr/local/bin/archappl-entrypoint.sh

ENV ARCHAPPL_APPLIANCES=/opt/archappl/conf/appliances.xml \
    ARCHAPPL_MYIDENTITY=appliance0 \
    ARCHAPPL_ALL_APPS_ON_ONE_JVM=true \
    ARCHAPPL_SHORT_TERM_FOLDER=/data/sts \
    ARCHAPPL_MEDIUM_TERM_FOLDER=/data/mts \
    ARCHAPPL_LONG_TERM_FOLDER=/data/lts

EXPOSE 17665

ENTRYPOINT ["/usr/local/bin/archappl-entrypoint.sh"]
