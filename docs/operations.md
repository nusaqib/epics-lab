# Operations runbook

## Bring-up from scratch

```bash
sudo ./scripts/install_requirements.sh   # once per host: Docker + Compose v2, git, make
cp .env.example .env                     # set real passwords
make build                               # 15-30 min first time (source builds)
make up                                  # start everything
make bootstrap                           # archiver PV list + alarm config import
make test                                # verify the whole chain
```

`make bootstrap` must be re-run after `make down` or `make clean` (Kafka
holds the live alarm configuration and has no persistent volume); plain
`make restart` / single-service restarts do not need it.

## Service URLs

| Service | URL |
|---|---|
| Archiver Appliance UI | <http://localhost:17665/mgmt/ui/index.html> |
| Archiver retrieval API | `http://localhost:17665/retrieval/data/getData.json?pv=<PV>` |
| ChannelFinder | <http://localhost:8080/ChannelFinder> |
| PV Info (PV browser) | <http://localhost:8082/pvinfo/> |
| Grafana / Prometheus | <http://localhost:3000> / <http://localhost:9090> (monitoring profile) |
| PV exporter | <http://localhost:9114/metrics> |
| CA / PVA gateways | `localhost:5064` / `localhost:5075` |
| Kafka (alarm apps) | `localhost:9092` |

## Service management

```bash
make up / down / restart     # whole stack (down keeps data volumes)
make status                  # health overview (compose healthchecks)
make logs S=<service>        # follow logs
docker compose restart <service>   # one service, e.g. after editing iocs/<name>/db
docker compose stop <service> && docker compose start <service>
make clean                   # stop and DELETE all volumes (archive data, autosave)
```

Start order is encoded in `depends_on` + healthchecks; a plain `make up`
after a host reboot brings everything back (`restart: unless-stopped`).

The IOCs and the caputlog server have **static IPs** on the `epics` network
(172.28.1.x, set in compose.yaml) because gateways, archiver, and alarm
server resolve those hostnames once at startup. If you recreate an IOC with
a *different* address (or add one without a static IP), restart the
dependents: `docker compose restart ca-gateway pva-gateway alarm-server`.

## Health

| Check | How |
|---|---|
| IOC alive | compose healthcheck = `pvget <PREFIX>:IOC:HEARTBEAT`; also archived + exported to Prometheus |
| Archiver | `curl http://localhost:17665/mgmt/bpl/getApplianceMetrics` |
| Alarm server | `docker compose logs alarm-server`; state messages on the `Lab` topic |
| ChannelFinder | `curl http://localhost:8080/ChannelFinder` and `docker compose logs recceiver` |
| PV connectivity | `epics_pv_connected` metrics at `:9114/metrics` |

## Common tasks

**Attach to an IOC shell** — `make console I=ioc-vacuum` (detach with
`Ctrl-]` then `quit`). From there: `dbl`, `dbpr LAB:VAC:GA1:PRES`, `casr`.

**Archive more PVs** — append to `archiver/pvlist.txt`, run
`make bootstrap` (idempotent). Pause/resume/inspect via the mgmt UI at
`:17665/mgmt/ui/index.html`.

**Change alarms** — edit `alarms/lab_alarms.xml`, run
`docker compose --profile tools run --rm alarm-import`. Clients pick up the
new tree immediately (compacted Kafka topic is the source of truth).

**Run an operational procedure** — `make procedure P=vacuum_pumpdown` runs
an oac-tree behavior-tree procedure (`procedures/*.xml`) against the plant
through the gateways; add `-V` via a custom run to validate a procedure
without executing it:
`docker compose --profile tools run --rm oac-tree -f /procedures/<name>.xml -V`.

**Audit CA writes** — `make caputlog` follows the central put log (who
changed which PV, old → new value). The file lives on the `caputlog-data`
volume (`/logs/caput.log`, size-rotated by iocLogServer).

**Find PVs** — query ChannelFinder:
`curl 'http://localhost:8080/ChannelFinder/resources/channels?~name=LAB:VAC:*'`
(filter by IOC with `&iocName=ioc-vacuum`). The directory is maintained by
RecSync — restarting an IOC refreshes its entries automatically.

**Autosave** — `.sav` files live in the per-IOC `*-autosave` volumes; the
IOC restores them on boot (`pass0/pass1`). To reset an IOC to defaults:
`docker compose down ioc-cryo && docker volume rm epics-lab_ioc-cryo-autosave`.

## Backup

State worth backing up:

| Data | Location |
|---|---|
| Archiver config DB | `archiver-db-data` volume (or `mysqldump` from `archiver-db`) |
| Archived data | `archiver-sts/mts/lts` volumes |
| Autosave settings | `ioc-*-autosave` volumes |
| Alarm configuration | `alarms/lab_alarms.xml` in git (the Kafka topic is derived) |
| ChannelFinder index | none needed — `channelfinder-es-data` is fully rebuilt by RecSync on IOC restarts |
| CA put audit log | `caputlog-data` volume (retain per your audit policy) |

Everything else is reproducible from this repository.

## Hardening for production

This stack is production-*shaped*; before real beamline duty:

1. **Secrets** — set real passwords in `.env` (never commit it); move to
   compose secrets or an external store.
2. **Network** — bind published ports to specific interfaces
   (`"host-ip:5064:5064"`), restrict CA gateway writes via UAG/HAG rules in
   `gateway/ca-gateway.access`, and consider `readOnly: true` for the PVA
   gateway.
3. **Kafka** — enable authentication/TLS on the external listener or stop
   publishing `9092`.
4. **ChannelFinder** — replace the `demo_auth` accounts in
   `channelfinder/application.properties` (and the matching credentials in
   `channelfinder/channelfinderapi.conf`) with LDAP/AD.
5. **Storage** — put archiver LTS on real disks (bind mounts), size STS/MTS,
   and set up ETL monitoring; schedule DB dumps.
6. **Redundancy** — run gateways and the archiver on separate hosts (the
   compose file splits cleanly; appliance clustering is supported via
   `appliances.xml`).
7. **Time** — ensure hosts run NTP/PTP; archived timestamps come from the
   IOCs.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `caget` from host times out | Not using the gateway: set `EPICS_CA_ADDR_LIST=localhost`, `EPICS_CA_AUTO_ADDR_LIST=NO` |
| `caget` works but `pvget` times out | The IOC binary must link `PVAServerRegister.dbd` (it does — check for regressions in `images/epics/top/labiocApp/src/Makefile`); also PVA servers never bind 127.0.0.1 — test against the container IP, not loopback |
| PVs unreachable through gateways after recreating an IOC | Gateways resolve IOC hostnames at startup; IOCs have static IPs to prevent this — `docker compose restart ca-gateway pva-gateway alarm-server` if addresses changed |
| CA write "succeeds" but value unchanged | Fire-and-forget put dropped on disconnect — use `caput -w`/`notify=True` semantics (put-with-callback) |
| PV visible on PVA but not CA | Name not matched by `gateway/ca-gateway.pvlist` |
| Archiver stuck "Initial sampling" | Engine cannot reach the IOC — check `EPICS_CA_ADDR_LIST` on the `archiver` service |
| Alarm server logs Kafka errors | `kafka-init` must complete first: `docker compose up -d kafka-init` |
| PVs missing from ChannelFinder | Check `docker compose logs recceiver` — the announce address must match the compose subnet broadcast (`channelfinder/recceiver.conf`); restart the IOC to re-announce |
| IOC unhealthy right after start | Autosave restore + qsrv startup can take a few seconds; check `make logs S=<ioc>` |
