# Development guide

## Prerequisites

- Docker Engine with the Compose plugin (or Podman with `podman compose`;
  set `COMPOSE="podman compose" make ...`) — on Debian/Ubuntu or
  Fedora/RHEL, `sudo ./scripts/install_requirements.sh` installs everything
- GNU make
- Optional on the host: `epics-base` CLI tools or Python `p4p`/`caproto` for
  ad-hoc PV access via the gateways

## Everyday loop

```bash
make up                      # start / apply compose changes
make logs S=ioc-cryo         # follow one service
make console I=ioc-cryo      # attach to the IOC shell (Ctrl-] quit to leave)
make test                    # full integration suite
```

Database or `st.cmd` changes only need a container restart, not a rebuild:

```bash
docker compose restart ioc-cryo
```

Rebuilds are needed only when you change `images/**` (e.g. adding a support
module to the generic IOC).

## Adding a new IOC

1. Create `iocs/<name>/{st.cmd,db/<name>.db,req/<name>_settings.req}` —
   copy `iocs/cryo` as a template. Follow
   [naming-conventions.md](naming-conventions.md) for PV names.
2. Add a service to `compose.yaml` (copy an existing IOC block): set
   `IOC_NAME`, `IOC_PREFIX`, `CAPUTLOG_ADDR`, the three volume mounts
   (instance config, `iocs/common`, autosave), a **static IP** on the
   `epics` network (next free 172.28.1.x — gateways resolve IOC addresses
   once at startup), and add a named autosave volume to the top-level
   `volumes:`.
3. Wire it into the ecosystem:
   - append the hostname to the `-cip` list of `ca-gateway`, the `addrlist`
     in `gateway/pva-gateway.json`, and the `EPICS_CA_ADDR_LIST` /
     `EPICS_PVA_ADDR_LIST` of `archiver`, `alarm-server` (also
     `alarms/alarm-server.ini`), and `pv-exporter`;
   - add PVs to `archiver/pvlist.txt`, `alarms/lab_alarms.xml`,
     `monitoring/pv-exporter.yaml` as appropriate (ChannelFinder needs
     nothing — reccaster registers the new IOC automatically);
   - add `depends_on` entries for the gateways/tests if the new IOC should
     gate them.
4. `make up && make bootstrap && make test`, and extend `tests/` with at
   least a read test for the new PVs.

## Adding a support module to the generic IOC

1. Add a build step in `images/epics/Dockerfile` (stage `build-modules`),
   pinned to a release tag.
2. Reference it in `images/epics/top/configure/RELEASE` and add its DBD/LIB
   to `images/epics/top/labiocApp/src/Makefile`.
3. `make build` and restart the IOCs.

## Displays

Edit `phoebus/displays/*.bob` with the Phoebus Display Builder (run Phoebus
with `-settings phoebus/settings.ini` so PVs resolve through the gateways).
Keep one display per subsystem and link it from `main.bob`.

## Tests

The suite runs inside the compose network and reaches PVs only through the
gateways. Structure:

- `test_iocs_pva.py` — PV reachability and sanity over PVA
- `test_gateway_ca.py` — CA reads/writes and gateway name filtering
- `test_simulation.py` — plant behavior (moves complete, pumpdown, cooldown)
- `test_archiver.py` — appliance health, archiving workflow, data retrieval
- `test_alarms.py` — Kafka/alarm-server round trip
- `test_channelfinder.py` — directory service + RecSync auto-registration

Run a subset: `docker compose --profile test run --rm tests test_iocs_pva.py -k heartbeat`.
