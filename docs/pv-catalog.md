# PV catalog

Every process variable in the facility, with its role in each high-level
service. Columns: **Save** = autosaved across IOC restarts, **Arch** =
archived (Archiver Appliance, `archiver/pvlist.txt` + `info(archive)` tag),
**Alm** = in the alarm tree (`alarms/lab_alarms.xml`), **Prom** = exported
to Prometheus (`monitoring/pv-exporter.yaml`).

This file is the human-readable index; the *live* index is ChannelFinder —
browse it at <http://localhost:8082/pvinfo/> (PV Info web UI) or query the
REST API (see [Discovering PVs](#discovering-pvs-at-runtime)).

## Cryogenics — `LAB:CRYO:*` (ioc-cryo)

| PV | Type | EGU | Description | Alarm limits | Save | Arch | Alm | Prom |
|---|---|---|---|---|:-:|:-:|:-:|:-:|
| `LAB:CRYO:TC1:SP` | ao | K | Cold head setpoint (4–350) | — | ✓ | ✓ | | ✓ |
| `LAB:CRYO:TC1:TEMP` | calc | K | Cold head temperature | HIGH 150 MINOR, HIHI 250 MAJOR | | ✓ | ✓ | ✓ |
| `LAB:CRYO:TC2:TEMP` | calc | K | Radiation shield temperature | HIGH 200 MINOR, HIHI 280 MAJOR | | ✓ | ✓ | ✓ |
| `LAB:CRYO:HTR1:POWER` | calc | % | Heater output (P controller) | — | | ✓ | | ✓ |
| `LAB:CRYO:CMP1:RUN` | bo | — | Compressor run command | — | ✓ | | | |
| `LAB:CRYO:CMP1:STS` | bi | — | Compressor status | Stopped → MINOR | | | ✓ | |
| `LAB:CRYO:HE:PRES` | calc | bar | Helium supply pressure | LOW 15 MINOR, LOLO 13 MAJOR | | ✓ | ✓ | ✓ |

## Vacuum — `LAB:VAC:*` (ioc-vacuum)

| PV | Type | EGU | Description | Alarm limits | Save | Arch | Alm | Prom |
|---|---|---|---|---|:-:|:-:|:-:|:-:|
| `LAB:VAC:PMP1:RUN` | bo | — | Turbo pump run command | — | ✓ | | | |
| `LAB:VAC:PMP1:SPEED` | calc | % | Turbo pump speed | — | | ✓ | | ✓ |
| `LAB:VAC:GA1:PRES` | calc | mbar | Chamber pressure | HIGH 1e-4 MINOR, HIHI 8e-4 MAJOR | | ✓ | ✓ | ✓ |
| `LAB:VAC:VLV1:CMD` | bo | — | Gate valve command | — | ✓ | | | |
| `LAB:VAC:VLV1:STS` | bi | — | Gate valve status | — | | | | |
| `LAB:VAC:VLV1:ILK` | calcout | — | Interlock: closes valve above 1e-4 mbar | — | | | | |
| `LAB:VAC:ILK:OK` | calc | — | Vacuum interlock permit (1 = OK) | not-OK → MAJOR | | ✓ | ✓ | ✓ |

## Motion — `LAB:MOT:*` (ioc-motion)

| PV | Type | EGU | Description | Alarm limits | Save | Arch | Alm | Prom |
|---|---|---|---|---|:-:|:-:|:-:|:-:|
| `LAB:MOT:M1:SP` | ao | mm | Axis 1 target position (±100) | — | | ✓ | | ✓ |
| `LAB:MOT:M1:VELO` | ao | mm/s | Axis 1 velocity (0.1–20) | — | ✓ | | | |
| `LAB:MOT:M1:RBV` | calc | mm | Axis 1 position readback (10 Hz) | — | | ✓ | | ✓ |
| `LAB:MOT:M1:DMOV` | calc | — | Done moving (1 = done) | — | | | | |
| `LAB:MOT:M1:HLS` | calc | — | High limit switch | at limit → MINOR | | | ✓ | |
| `LAB:MOT:M1:LLS` | calc | — | Low limit switch | at limit → MINOR | | | ✓ | |

`M1:SP` is deliberately **not** autosaved — restoring it would command a
move on IOC reboot (see `iocs/motion/req/`).

## IOC health — `LAB:<AREA>:IOC:*` (iocStats, all IOCs)

Every IOC loads `iocAdminSoft.db` under the prefix `LAB:<AREA>:IOC`. Most
used signals (the module provides ~40 per IOC — `dbl` in the IOC console
lists them all):

| PV pattern | Description | Notes |
|---|---|---|
| `LAB:*:IOC:HEARTBEAT` | Increments 1/s | container healthcheck, archived, Prometheus |
| `LAB:*:IOC:UPTIME` | Seconds since boot | |
| `LAB:*:IOC:CPU_LOAD` / `MEM_USED` | Resource usage | |
| `LAB:*:IOC:CA_CLNT_CNT` | Connected CA clients | |

## Gateway status PVs

| Prefix | Source |
|---|---|
| `LAB:CAGW:*` | CA gateway internal statistics (`-prefix LAB:CAGW`) |
| `LAB:PVAGW:*` | PVA gateway status (`statusprefix` in `gateway/pva-gateway.json`) |

## Discovering PVs at runtime

ChannelFinder is the live, always-current version of this catalog — RecSync
rebuilds it from the running IOCs, including the `archive` property derived
from `info(archive, "...")` tags in the databases:

```bash
# everything in an area
curl 'http://localhost:8080/ChannelFinder/resources/channels?~name=LAB:VAC:*'
# every PV on one IOC
curl 'http://localhost:8080/ChannelFinder/resources/channels?iocName=ioc-cryo'
# every PV declared for archiving in its database
curl 'http://localhost:8080/ChannelFinder/resources/channels?archive=*'
```

Or from an IOC shell: `make console I=ioc-cryo`, then `dbl` (all records)
or `dbpr LAB:CRYO:TC1:TEMP 2` (record detail).

## Keeping this catalog honest

When adding or changing PVs (see [development.md](development.md)):

1. Describe the record in its `.db` file (`DESC`, `EGU`, alarm fields) and
   add `info(archive, "monitor@1.0")` if it should be archived.
2. Update `archiver/pvlist.txt`, `alarms/lab_alarms.xml`,
   `monitoring/pv-exporter.yaml` as appropriate.
3. Update the tables above.
