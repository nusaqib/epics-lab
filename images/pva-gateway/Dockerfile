# PV Access gateway based on p4p (https://epics-base.github.io/p4p/gw.html)
FROM python:3.12-slim

ARG P4P_VERSION=4.2.0

RUN pip install --no-cache-dir "p4p==${P4P_VERSION}" \
    && useradd --system --create-home --uid 902 gateway

USER gateway

# Configuration is mounted at /config (see gateway/pva-gateway.json)
CMD ["pvagw", "/config/pva-gateway.json"]
