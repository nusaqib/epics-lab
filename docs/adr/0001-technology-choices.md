# ADR 0001 — Technology choices

Status: accepted · Date: 2026-07-29

## Context

We need a complete, scalable, maintainable EPICS ecosystem that serves as a
development/testing environment and is structurally ready for production.

## Decisions

1. **EPICS 7 (CA + PV Access)** — current upstream line; QSRV serves every
   record over both protocols, so modern (PVA) and legacy (CA) tooling work.

2. **Containers + Docker Compose** — one file describes the whole facility;
   `make up` reproduces it anywhere. Compose (not Kubernetes) because the
   target is a lab-scale deployment on one or a few hosts; the images are
   orchestrator-agnostic, so a later move to k8s only replaces the
   orchestration layer.

3. **Build EPICS components from pinned source tags** rather than trusting
   third-party images — the resulting images are exactly reproducible and
   upgrades are explicit one-line changes (`ARG` values in Dockerfiles).

4. **Generic IOC binary + mounted instance config** (ESS/DLS-style) — one
   `labioc` binary (base + qsrv + iocStats + autosave); each IOC is a config
   directory. Adding an IOC requires no compilation, and every IOC gets
   health PVs and autosave for free. Device simulation uses plain `calc`
   record databases so the generic image needs no site-specific C code.

5. **Gateways as the boundary** — ca-gateway and p4p PVA gateway are the
   only published control-plane endpoints, mirroring production
   office/control network separation and giving one place for access rules.

6. **Archiver Appliance** for history (the de-facto EPICS standard), single
   JVM + MariaDB at this scale; **Phoebus alarm server + Kafka** for alarms
   (current CS-Studio ecosystem, config-as-code via XML import);
   **Phoebus** as operator UI (displays are versioned `.bob` files).

7. **procServ in containers** — preserves the operator-facing IOC console
   workflow while compose handles supervision/restart.

8. **pv-exporter + Prometheus/Grafana** as an optional profile — plant and
   infrastructure observability without burdening the control path.

9. **Containerized pytest integration suite** that talks only through the
   gateways — CI proves the same path operators use.

## Consequences

- First build compiles EPICS base and Phoebus from source (15–30 min);
  cached thereafter. CI uses the same builds, keeping runs honest but slow.
- Scaling beyond one host means splitting the compose file per host (or
  moving to k8s); no image changes required.
- The motor record / synApps modules are intentionally absent; adding them
  is a documented Dockerfile + top change (docs/development.md).
