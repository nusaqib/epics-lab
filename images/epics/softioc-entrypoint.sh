#!/bin/sh
# Start the generic IOC under procServ so operators can attach to the IOC
# shell (`make console I=<service>`) and the process is restarted cleanly.
set -eu

: "${IOC_NAME:?IOC_NAME must be set}"
: "${IOC_PREFIX:?IOC_PREFIX must be set}"

if [ ! -f /config/st.cmd ]; then
    echo "ERROR: /config/st.cmd not found — mount an IOC instance directory at /config" >&2
    exit 1
fi

exec /usr/local/bin/procServ \
    --foreground \
    --name "$IOC_NAME" \
    --logfile - \
    --logstamp \
    --ignore=^C^D \
    --chdir /config \
    2000 \
    /opt/epics/ioc/bin/host/labioc /config/st.cmd
