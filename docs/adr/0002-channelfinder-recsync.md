# ADR 0002 — ChannelFinder populated via RecSync

Status: accepted · Date: 2026-07-29

## Context

The stack needs a PV directory service so operators and tools can discover
which PVs exist, on which IOC and host — without maintaining hand-written
lists. ChannelFinder is the standard EPICS directory service; the question
is how it gets populated.

## Decision

1. **ChannelFinder service** (Spring Boot, pinned tag) backed by a
   single-node **Elasticsearch**; only the HTTP API (`:8080`) is published.
   Development auth uses in-memory `demo_auth` accounts (reads anonymous,
   writes authenticated).

2. **Populate via RecSync**, not static lists:
   - the generic IOC links the **reccaster** module, so every IOC announces
     its complete record list and identifying environment (`IOCNAME`,
     hostname) at boot;
   - a **recceiver** service collects announcements and syncs them into
     ChannelFinder with `hostName`/`iocName`/`pvStatus` properties.

3. recceiver discovers IOCs via **UDP broadcast**, so the compose network
   pins subnet `172.28.0.0/16` and recceiver announces to
   `172.28.255.255:5049`. The subnet and the announce address must change
   together.

## Alternatives considered

- **Bootstrap script posting a static PV list** (like the archiver's) —
  simpler, but defeats the purpose of a directory: it documents what we
  *think* is running rather than what *is* running, and adds a manual step
  per IOC.
- **cf-store/pvAccess-based discovery** — less mature/standard than
  RecSync for this purpose.

## Consequences

- New IOCs appear in ChannelFinder with zero configuration; a restarted
  IOC refreshes its own entries (`pvStatus` tracks liveness).
- The Elasticsearch index is disposable — it is rebuilt from IOC
  announcements, so it needs no backup.
- The IOC image grows one more pinned module (recsync `1.9.6`); the fixed
  compose subnet is now load-bearing (documented in compose.yaml and
  recceiver.conf).
