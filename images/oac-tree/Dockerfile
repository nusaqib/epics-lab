# syntax=docker/dockerfile:1.7
# oac-tree — behavior-tree based sequencer for operational procedures
# (https://github.com/oac-tree, open-sourced by ITER). Built via the
# oac-tree-bundle superbuild (core + server + ca/pvxs/control/mathexpr
# plugins, no GUI) against EPICS base + PVXS.
ARG DEBIAN_VERSION=12-slim

FROM debian:${DEBIAN_VERSION} AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ca-certificates cmake git perl pkg-config \
        libxml2-dev libevent-dev libreadline-dev libgtest-dev libgmock-dev \
    && rm -rf /var/lib/apt/lists/*

# EPICS base (same pin as images/epics)
ARG EPICS_BASE_VERSION=R7.0.8.1
RUN git clone --branch ${EPICS_BASE_VERSION} --depth 1 --recursive \
        https://github.com/epics-base/epics-base.git /opt/epics/base \
    && make -C /opt/epics/base -j"$(nproc)" \
    && EPICS_HOST_ARCH="$(perl /opt/epics/base/src/tools/EpicsHostArch.pl)" \
    && ln -s "/opt/epics/base/lib/${EPICS_HOST_ARCH}" /opt/epics/base/lib/host

# PVXS (required by sup-epics)
ARG PVXS_VERSION=1.5.2
RUN git clone --branch ${PVXS_VERSION} --depth 1 \
        https://github.com/epics-base/pvxs.git /opt/epics/pvxs \
    && echo "EPICS_BASE=/opt/epics/base" > /opt/epics/pvxs/configure/RELEASE.local \
    && make -C /opt/epics/pvxs -j"$(nproc)" \
    && EPICS_HOST_ARCH="$(perl /opt/epics/base/src/tools/EpicsHostArch.pl)" \
    && ln -s "/opt/epics/pvxs/lib/${EPICS_HOST_ARCH}" /opt/epics/pvxs/lib/host

# oac-tree-server needs Asio (header-only) and OpenSSL (separate layer so
# the EPICS/PVXS build layers above stay cached).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libasio-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# oac-tree superbuild (sup-* libraries, core, server, plugins; no Qt GUI)
ARG OAC_TREE_BUNDLE_VERSION=v1.5
RUN git clone --branch ${OAC_TREE_BUNDLE_VERSION} --depth 1 \
        --recurse-submodules --shallow-submodules \
        https://github.com/oac-tree/oac-tree-bundle.git /src/oac-tree-bundle
ENV EPICS_BASE=/opt/epics/base \
    PVXS_DIR=/opt/epics/pvxs
# LDFLAGS: the bundle's ExternalProject modules link test executables
# against libsup-epics.so, whose transitive PVXS/CA dependencies live
# outside the default linker search path.
RUN export EPICS_HOST_ARCH="$(perl /opt/epics/base/src/tools/EpicsHostArch.pl)" \
    && export LDFLAGS="-Wl,-rpath-link,/opt/epics/pvxs/lib/host -Wl,-rpath-link,/opt/epics/base/lib/host" \
    && cmake -S /src/oac-tree-bundle -B /src/build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/oac-tree \
        -DCOA_NO_GUI=ON \
        -DCOA_BUILD_TESTS=OFF \
    && cmake --build /src/build -j"$(nproc)" \
    && cmake --install /src/build

# ---------------------------------------------------------------- runtime
FROM debian:${DEBIAN_VERSION}
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        libxml2 libevent-core-2.1-7 libevent-pthreads-2.1-7 \
        libreadline8 netbase \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home --uid 907 oac

COPY --from=build /opt/oac-tree /opt/oac-tree
COPY --from=build /opt/epics/base/lib /opt/epics/base/lib
COPY --from=build /opt/epics/pvxs/lib /opt/epics/pvxs/lib

ENV PATH=/opt/oac-tree/bin:${PATH} \
    LD_LIBRARY_PATH=/opt/oac-tree/lib:/opt/oac-tree/lib/oac-tree/plugins:/opt/epics/base/lib/host:/opt/epics/pvxs/lib/host

USER oac
WORKDIR /procedures

# Procedures are mounted at /procedures (see procedures/ in the repo)
ENTRYPOINT ["oac-tree-cli"]
CMD ["--help"]
