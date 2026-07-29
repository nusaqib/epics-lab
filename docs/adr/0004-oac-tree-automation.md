# ADR 0004 — Operational automation with oac-tree

Status: accepted · Date: 2026-07-29

## Context

The stack covers monitoring (archiver, alarms, directory) but has no layer
for *automated operational procedures* — multi-step sequences like
"pump down, verify vacuum, open the valve" that operators would otherwise
execute by hand or encode in ad-hoc scripts.

## Decision

- Package **oac-tree** (ITER's behavior-tree sequencer,
  https://github.com/oac-tree) via the `oac-tree-bundle` superbuild at a
  pinned tag (`v1.5`), with the CA/PVXS/control/mathexpr plugins and the
  server, but no Qt GUI (`COA_NO_GUI=ON`). The image also builds EPICS base
  (same pin as the IOC image) and PVXS `1.5.2`, which sup-epics requires.
- Procedures are **versioned XML behavior trees in `procedures/`**, executed
  on demand by a `tools`-profile service (`make procedure P=<name>`), with
  `-V` available for validate-only runs.
- The sequencer reaches the plant **through the gateways** (CA/PVA addr
  lists point at `ca-gateway`/`pva-gateway`), the same path operators use —
  so its writes are name-filtered, access-controlled, and caPutLog-audited
  like any other client.
- One worked example ships: `vacuum_pumpdown.xml` (start pump →
  WaitForCondition on pressure → open + verify gate valve).

## Alternatives considered

- **Python scripts (pyepics/p4p)** — flexible but unstructured: no built-in
  tree semantics, no validate mode, no path to the oac-tree GUI/server for
  supervised execution.
- **EPICS sequencer (SNL)** — compiled state machines living inside an IOC;
  better for machine-protection-adjacent logic than for operator-level
  procedures, and much harder to review than XML trees.

## Consequences

- Procedures are reviewable config, testable with `-V`, and auditable via
  caPutLog.
- The image is another heavy source build (base + PVXS + ~10 CMake
  modules); it is only needed by the `tools` profile.
- The oac-tree GUI and server-supervised execution are natural follow-ups
  (the server binaries are already in the image).
