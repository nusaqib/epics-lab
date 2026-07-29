# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# EPICS build tree — one Dockerfile, multiple targets sharing cached stages:
#
#   softioc     generic IOC binary (base + qsrv + iocStats + autosave)
#               run under procServ; per-instance config is mounted at /config
#   ca-gateway  Channel Access gateway (pcas + ca-gateway)
# ---------------------------------------------------------------------------

ARG DEBIAN_VERSION=12-slim

# ------------------------------------------------------------- EPICS base
FROM debian:${DEBIAN_VERSION} AS build-base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl git perl libreadline-dev \
    && rm -rf /var/lib/apt/lists/*

ARG EPICS_BASE_VERSION=R7.0.8.1
RUN git clone --branch ${EPICS_BASE_VERSION} --depth 1 --recursive \
        https://github.com/epics-base/epics-base.git /opt/epics/base
RUN make -C /opt/epics/base -j"$(nproc)" \
    && EPICS_HOST_ARCH="$(perl /opt/epics/base/src/tools/EpicsHostArch.pl)" \
    && ln -s "/opt/epics/base/bin/${EPICS_HOST_ARCH}" /opt/epics/base/bin/host \
    && ln -s "/opt/epics/base/lib/${EPICS_HOST_ARCH}" /opt/epics/base/lib/host

# --------------------------------------------------------------- procServ
FROM build-base AS build-procserv
ARG PROCSERV_VERSION=2.8.0
RUN curl -fsSL -o /tmp/procServ.tar.gz \
        https://github.com/ralphlange/procServ/releases/download/v${PROCSERV_VERSION}/procServ-${PROCSERV_VERSION}.tar.gz \
    && mkdir /tmp/procServ && tar -xzf /tmp/procServ.tar.gz -C /tmp/procServ --strip-components=1 \
    && cd /tmp/procServ && ./configure --disable-doc && make && make install \
    && rm -rf /tmp/procServ /tmp/procServ.tar.gz

# ---------------------------------------------------- support modules
FROM build-base AS build-modules
ARG IOCSTATS_VERSION=3.2.0
ARG AUTOSAVE_VERSION=R5-11
ARG RECSYNC_VERSION=1.9.6
ARG CAPUTLOG_VERSION=R4.2
RUN git clone --branch ${IOCSTATS_VERSION} --depth 1 \
        https://github.com/epics-modules/iocStats.git /opt/epics/modules/iocStats \
    && echo "EPICS_BASE=/opt/epics/base" > /opt/epics/modules/iocStats/configure/RELEASE.local \
    && make -C /opt/epics/modules/iocStats -j"$(nproc)"
RUN git clone --branch ${AUTOSAVE_VERSION} --depth 1 \
        https://github.com/epics-modules/autosave.git /opt/epics/modules/autosave \
    && echo "EPICS_BASE=/opt/epics/base" > /opt/epics/modules/autosave/configure/RELEASE.local \
    && make -C /opt/epics/modules/autosave -j"$(nproc)"
# reccaster (RecSync client): announces every record to the recceiver
# service, which populates ChannelFinder.
RUN git clone --branch ${RECSYNC_VERSION} --depth 1 \
        https://github.com/ChannelFinder/recsync.git /opt/epics/modules/recsync \
    && echo "EPICS_BASE=/opt/epics/base" > /opt/epics/modules/recsync/client/configure/RELEASE.local \
    && make -C /opt/epics/modules/recsync/client -j"$(nproc)"
# caPutLog: forwards trapped CA writes (who/what/old->new) to a log server.
RUN git clone --branch ${CAPUTLOG_VERSION} --depth 1 \
        https://github.com/epics-modules/caPutLog.git /opt/epics/modules/caPutLog \
    && echo "EPICS_BASE=/opt/epics/base" > /opt/epics/modules/caPutLog/configure/RELEASE.local \
    && make -C /opt/epics/modules/caPutLog -j"$(nproc)"

# --------------------------------------------------- generic IOC binary
FROM build-modules AS build-ioc
COPY top/ /opt/epics/ioc/
RUN make -C /opt/epics/ioc -j"$(nproc)" \
    && EPICS_HOST_ARCH="$(perl /opt/epics/base/src/tools/EpicsHostArch.pl)" \
    && ln -s "/opt/epics/ioc/bin/${EPICS_HOST_ARCH}" /opt/epics/ioc/bin/host

# --------------------------------------------------- softioc runtime image
FROM debian:${DEBIAN_VERSION} AS softioc
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreadline8 telnet netbase \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build-ioc /opt/epics/base /opt/epics/base
COPY --from=build-ioc /opt/epics/modules /opt/epics/modules
COPY --from=build-ioc /opt/epics/ioc /opt/epics/ioc
COPY --from=build-procserv /usr/local/bin/procServ /usr/local/bin/procServ
COPY softioc-entrypoint.sh /usr/local/bin/softioc-start
COPY console /usr/local/bin/console

RUN chmod +x /usr/local/bin/softioc-start /usr/local/bin/console \
    && useradd --system --create-home --uid 900 ioc \
    && mkdir -p /autosave /config /logs \
    && chown -R ioc:ioc /autosave /logs

ENV PATH=/opt/epics/base/bin/host:${PATH}
USER ioc
WORKDIR /config

# CA (5064/5065) and PVA (5075/5076) stay on the internal network; the
# procServ console listens on 2000 inside the container only.
ENTRYPOINT ["/usr/local/bin/softioc-start"]

# ------------------------------------------------------ CA gateway build
FROM build-base AS build-cagateway
ARG PCAS_VERSION=v4.13.3
ARG CAGATEWAY_VERSION=v2.1.3
RUN git clone --branch ${PCAS_VERSION} --depth 1 \
        https://github.com/epics-modules/pcas.git /opt/epics/modules/pcas \
    && echo "EPICS_BASE=/opt/epics/base" > /opt/epics/modules/pcas/configure/RELEASE.local \
    && make -C /opt/epics/modules/pcas -j"$(nproc)"
RUN git clone --branch ${CAGATEWAY_VERSION} --depth 1 \
        https://github.com/epics-extensions/ca-gateway.git /opt/epics/extensions/ca-gateway \
    && { echo "PCAS=/opt/epics/modules/pcas"; \
         echo "EPICS_BASE=/opt/epics/base"; } \
         > /opt/epics/extensions/ca-gateway/configure/RELEASE.local \
    && make -C /opt/epics/extensions/ca-gateway -j"$(nproc)"

# ---------------------------------------------------- CA gateway runtime
FROM debian:${DEBIAN_VERSION} AS ca-gateway
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreadline8 netbase \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build-cagateway /opt/epics/base/lib /opt/epics/base/lib
COPY --from=build-cagateway /opt/epics/modules/pcas/lib /opt/epics/modules/pcas/lib
COPY --from=build-cagateway /opt/epics/extensions/ca-gateway/bin /opt/epics/extensions/ca-gateway/bin

RUN EPICS_HOST_ARCH="$(ls /opt/epics/extensions/ca-gateway/bin | head -1)" \
    && ln -s "/opt/epics/extensions/ca-gateway/bin/${EPICS_HOST_ARCH}/gateway" /usr/local/bin/gateway \
    && useradd --system --create-home --uid 901 gateway

USER gateway
CMD ["gateway", "-help"]
