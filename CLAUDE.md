# EPICS Lab — notes for coding agents

Containerized EPICS 7 control-system ecosystem. No code runs on the host;
everything is Docker Compose (`compose.yaml` is the source of truth).

## Commands

- `make build | up | down | restart | status | logs S=<svc>` — lifecycle
- `make bootstrap` — submit archiver PVs + import alarm config (idempotent;
  needed again after `make down`/`clean` because Kafka has no volume)
- `make test` — integration suite (containerized pytest; needs the stack up)
- `make console I=<ioc-service>` — attach to an IOC shell via procServ
- `make caputlog` — follow the CA write audit trail
- `make monitoring` — Prometheus + Grafana profile

## Service URLs (host)

- Archiver Appliance: http://localhost:17665/mgmt/ui/index.html
- ChannelFinder: http://localhost:8080/ChannelFinder
- Grafana: http://localhost:3000 · Prometheus: http://localhost:9090
- PV exporter: http://localhost:9114/metrics
- CA gateway: localhost:5064 · PVA gateway: localhost:5075/5076 · Kafka: localhost:9092

## Layout rules

- IOC instances live in `iocs/<name>/` (st.cmd, db/, req/) and are mounted
  read-only into the generic `softioc` image — DB changes need only
  `docker compose restart <svc>`, not a rebuild. `iocs/common/lab.acf` is the
  shared CA access file (TRAPWRITE for caPutLog).
- The generic IOC binary and CA gateway are built by the multi-target
  `images/epics/Dockerfile`; all upstream versions are pinned `ARG`s.
- Adding an IOC: follow docs/development.md — it must be wired into the
  gateway addr lists, archiver/alarm/exporter configs, and tests, and given a
  static IP on the `epics` network (gateways resolve IOC hostnames once at
  startup). ChannelFinder needs no wiring (RecSync auto-registers IOCs); keep
  the compose subnet in sync with the announce address in
  channelfinder/recceiver.conf.
- PV naming: `LAB:<AREA>:<DEVICE><N>:<SIGNAL>` (docs/naming-conventions.md).
- Tests must access PVs only through the gateways (env is preset in the
  `tests` compose service). caproto writes need `notify=True` or they may be
  dropped on disconnect.

## Hard-won gotchas (encoded in the repo — don't regress)

- The IOC app links `PVAServerRegister.dbd` + `qsrv.dbd`; without the former
  the PVA server never starts (caget works, pvget times out).
- PVA servers don't bind 127.0.0.1 — test with the container's eth0 IP or a
  peer container, never loopback.
- Archiver Appliance 1.1.0 WARs need Java 17 (`tomcat:9-jdk17-temurin`).
- pyCFClient isn't on PyPI; recsync's `pip install ./server` pins it itself.
