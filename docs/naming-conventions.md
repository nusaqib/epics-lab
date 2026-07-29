# PV naming conventions

All process variables follow:

```
LAB:<AREA>:<DEVICE><N>:<SIGNAL>
```

| Element | Rule | Examples |
|---|---|---|
| `LAB` | Facility root, fixed. Gateways only expose `LAB:*`. | |
| `AREA` | Subsystem, 3–6 uppercase letters | `CRYO`, `VAC`, `MOT` |
| `DEVICE` | Device class + instance number | `TC1`, `PMP1`, `VLV1`, `M1` |
| `SIGNAL` | Signal name, uppercase | `TEMP`, `SP`, `RBV`, `PRES`, `RUN`, `STS` |

Common signal suffixes:

| Suffix | Meaning |
|---|---|
| `:SP` | setpoint / target (operator writable) |
| `:RBV` | readback value |
| `:RUN` / `:CMD` | run / actuation command (writable) |
| `:STS` | device status readback |
| `:ILK` | interlock logic |
| `:IOC:*` | IOC health PVs (iocStats), e.g. `LAB:CRYO:IOC:HEARTBEAT` |

Rules:

- Only operator-facing *settings* are autosaved (never commands that would
  cause motion or state changes on reboot — see `iocs/motion/req/`).
- Every alarm-worthy PV declares its limits in the database (`HIGH/HIHI/...`)
  so CA clients, the alarm server, and the archiver all see the same alarms.
- New areas must be added to `gateway/ca-gateway.pvlist` only if they live
  under a prefix other than `LAB:`.
