# ADR 0003 — CA put audit via caPutLog + iocLogServer

Status: accepted · Date: 2026-07-29

## Context

A production control system needs an audit trail of operator writes: who
changed which setpoint, from where, and what the value was before.

## Decision

- All IOCs load a shared access-security file (`iocs/common/lab.acf`,
  mounted at `/common`) that keeps the open development read/write policy
  but marks WRITE rules with `TRAPWRITE`.
- The **caPutLog** module (pinned `R4.2`) in the generic IOC forwards each
  trapped put to a central **iocLogServer** (`caputlog` service — the
  binary ships with EPICS base, so the service reuses the `softioc` image
  with an entrypoint override). `CAPUTLOG_ADDR` is injected per IOC by
  compose.
- The log is a size-rotated file on the `caputlog-data` volume, followed
  via `make caputlog`, and covered by an integration test that writes a PV
  through the CA gateway and asserts the entry appears.

## Alternatives considered

- **caPutLog JSON → central log stack** (Loki/Elasticsearch) — better for
  querying at scale, but adds a log pipeline; the plain iocLogServer file
  is the standard, zero-dependency starting point and the JSON option
  remains a config change (`caPutJsonLogInit`).
- **Relying on container stdout logs** — loses the structured old→new
  values and mixes audit data with operational noise.

## Consequences

- Writes arriving through the CA gateway are attributed to the gateway
  identity; per-user attribution requires access rules on the gateway
  itself (documented as a hardening item).
- The ACF file is now the single place to tighten write permissions for
  all IOCs.
