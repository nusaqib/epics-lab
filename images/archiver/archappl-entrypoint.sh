#!/bin/bash
# Archiver Appliance entrypoint:
#   1. wait for the configuration database
#   2. apply the appliance schema on first boot
#   3. render the JNDI datasource from environment variables
#   4. start Tomcat in the foreground
set -euo pipefail

: "${ARCHAPPL_DB_HOST:?ARCHAPPL_DB_HOST must be set}"
: "${ARCHAPPL_DB_NAME:?ARCHAPPL_DB_NAME must be set}"
: "${ARCHAPPL_DB_USER:?ARCHAPPL_DB_USER must be set}"
: "${ARCHAPPL_DB_PASSWORD:?ARCHAPPL_DB_PASSWORD must be set}"

mysql_cmd() {
    mysql --host="$ARCHAPPL_DB_HOST" --user="$ARCHAPPL_DB_USER" \
          --password="$ARCHAPPL_DB_PASSWORD" "$ARCHAPPL_DB_NAME" "$@"
}

echo "Waiting for configuration database at ${ARCHAPPL_DB_HOST}..."
for i in $(seq 1 60); do
    if mysql_cmd -e 'SELECT 1' >/dev/null 2>&1; then
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "ERROR: database not reachable after 120 s" >&2
        exit 1
    fi
    sleep 2
done

if ! mysql_cmd -e 'SELECT 1 FROM PVTypeInfo LIMIT 1' >/dev/null 2>&1; then
    echo "Applying Archiver Appliance schema..."
    mysql_cmd < /opt/archappl/sql/archappl_mysql.sql
else
    echo "Archiver Appliance schema already present."
fi

echo "Rendering JNDI datasource configuration..."
export ARCHAPPL_DB_HOST ARCHAPPL_DB_NAME ARCHAPPL_DB_USER ARCHAPPL_DB_PASSWORD
envsubst '${ARCHAPPL_DB_HOST} ${ARCHAPPL_DB_NAME} ${ARCHAPPL_DB_USER} ${ARCHAPPL_DB_PASSWORD}' \
    < /opt/archappl/conf/context.xml.template \
    > /usr/local/tomcat/conf/context.xml

mkdir -p "$ARCHAPPL_SHORT_TERM_FOLDER" "$ARCHAPPL_MEDIUM_TERM_FOLDER" "$ARCHAPPL_LONG_TERM_FOLDER"

export CATALINA_OPTS="${CATALINA_OPTS:-} \
    -DARCHAPPL_APPLIANCES=${ARCHAPPL_APPLIANCES} \
    -DARCHAPPL_MYIDENTITY=${ARCHAPPL_MYIDENTITY} \
    -Dorg.epics.archiverappliance.config.persistence.MySQLPersistence=jdbc/archappl"

exec catalina.sh run
