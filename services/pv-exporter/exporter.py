#!/usr/bin/env python3
"""Prometheus exporter for EPICS PVs.

Monitors a configurable list of PVs over PV Access and exposes their value,
alarm severity, and connection state as Prometheus metrics on /metrics.

Config file (YAML):

    pvs:
      - LAB:CRYO:TC1:TEMP
      - LAB:VAC:GA1:PRES
"""

from __future__ import annotations

import argparse
import logging
import threading

import yaml
from p4p.client.thread import Context, Disconnected
from prometheus_client import Gauge, start_http_server

log = logging.getLogger("pv-exporter")

VALUE = Gauge("epics_pv_value", "Current PV value", ["pv"])
SEVERITY = Gauge(
    "epics_pv_severity",
    "PV alarm severity (0=NONE 1=MINOR 2=MAJOR 3=INVALID)",
    ["pv"],
)
CONNECTED = Gauge("epics_pv_connected", "PV connection state (1=connected)", ["pv"])


def make_callback(pv: str):
    def callback(update):
        if isinstance(update, Disconnected):
            CONNECTED.labels(pv=pv).set(0)
            log.warning("%s disconnected", pv)
            return
        if isinstance(update, Exception):
            CONNECTED.labels(pv=pv).set(0)
            log.error("%s error: %s", pv, update)
            return
        CONNECTED.labels(pv=pv).set(1)
        try:
            VALUE.labels(pv=pv).set(float(update))
        except (TypeError, ValueError):
            pass  # non-numeric PV; connection/severity are still exported
        severity = getattr(update, "severity", None)
        if severity is not None:
            SEVERITY.labels(pv=pv).set(int(severity))

    return callback


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="YAML file with a `pvs:` list")
    parser.add_argument("--port", type=int, default=9114, help="Metrics port")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    with open(args.config, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    pvs = config.get("pvs") or []
    if not pvs:
        raise SystemExit("No PVs configured")

    for pv in pvs:
        CONNECTED.labels(pv=pv).set(0)

    start_http_server(args.port)
    log.info("Serving metrics on :%d for %d PV(s)", args.port, len(pvs))

    context = Context("pva")
    subscriptions = [context.monitor(pv, make_callback(pv), notify_disconnect=True)
                     for pv in pvs]
    assert subscriptions  # keep references alive

    threading.Event().wait()  # run until the container is stopped


if __name__ == "__main__":
    main()
