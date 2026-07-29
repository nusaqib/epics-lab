# RecSync server (recceiver): collects record inventories announced by the
# reccaster module inside every IOC and synchronizes them to ChannelFinder.
FROM python:3.12-slim

ARG RECSYNC_VERSION=1.9.6

ENV DEBIAN_FRONTEND=noninteractive
# recceiver's pyproject pins its own dependencies (twisted, requests, and
# the pyCFClient "channelfinder" package fetched from GitHub).
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 --branch ${RECSYNC_VERSION} \
        https://github.com/ChannelFinder/recsync.git /tmp/recsync \
    && pip install --no-cache-dir /tmp/recsync/server \
    && rm -rf /tmp/recsync \
    && apt-get purge -y git && apt-get autoremove -y \
    && useradd --system --create-home --uid 906 recceiver

USER recceiver
WORKDIR /home/recceiver

# recceiver.conf and /etc/channelfinderapi.conf are mounted by compose.
CMD ["twistd", "--nodaemon", "--pidfile=", "recceiver", "-f", "/config/recceiver.conf"]
