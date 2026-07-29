#!/usr/bin/env python3
"""Submit PVs to the EPICS Archiver Appliance.

Reads a PV list file (one PV per line, `#` comments), waits for the mgmt
webapp to come up, submits any PVs that are not yet being archived, and
prints a status summary. Idempotent — safe to run repeatedly.

Uses only the Python standard library so it can run in a bare python image.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SAMPLING_PERIOD = "1.0"  # seconds
SAMPLING_METHOD = "MONITOR"


def read_pvlist(path: str) -> list[str]:
    pvs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                pvs.append(line)
    return pvs


def get_json(url: str, timeout: float = 10.0):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def post_json(url: str, payload, timeout: float = 30.0):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def wait_for_appliance(base_url: str, deadline: float) -> None:
    url = f"{base_url}/mgmt/bpl/getApplianceInfo"
    while True:
        try:
            info = get_json(url)
            print(f"Appliance up: {info.get('identity', '?')}")
            return
        except (urllib.error.URLError, OSError, ValueError) as exc:
            if time.monotonic() > deadline:
                sys.exit(f"ERROR: appliance not reachable: {exc}")
            print("Waiting for archiver appliance mgmt webapp...")
            time.sleep(5)


def pv_statuses(base_url: str, pvs: list[str]) -> dict[str, str]:
    quoted = urllib.parse.quote(",".join(pvs))
    url = f"{base_url}/mgmt/bpl/getPVStatus?pv={quoted}"
    return {item["pvName"]: item["status"] for item in get_json(url)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://archiver:17665",
                        help="Base URL of the appliance (default: %(default)s)")
    parser.add_argument("--pvlist", required=True, help="Path to the PV list file")
    parser.add_argument("--wait", type=float, default=300,
                        help="Seconds to wait for the appliance (default: %(default)s)")
    args = parser.parse_args()

    pvs = read_pvlist(args.pvlist)
    if not pvs:
        sys.exit("ERROR: PV list is empty")

    deadline = time.monotonic() + args.wait
    wait_for_appliance(args.url, deadline)

    statuses = pv_statuses(args.url, pvs)
    to_submit = [pv for pv in pvs
                 if statuses.get(pv, "Not being archived") == "Not being archived"]

    if to_submit:
        print(f"Submitting {len(to_submit)} PV(s) for archiving...")
        payload = [{"pv": pv,
                    "samplingperiod": SAMPLING_PERIOD,
                    "samplingmethod": SAMPLING_METHOD} for pv in to_submit]
        post_json(f"{args.url}/mgmt/bpl/archivePV", payload)
    else:
        print("All PVs already known to the appliance.")

    # Give the engine a moment, then report status; workflow completion can
    # take a while and is not an error, so this never fails on "pending".
    time.sleep(10)
    statuses = pv_statuses(args.url, pvs)
    width = max(len(pv) for pv in pvs)
    print("\nArchiving status:")
    for pv in pvs:
        print(f"  {pv:<{width}}  {statuses.get(pv, 'unknown')}")

    pending = [pv for pv, st in statuses.items() if st != "Being archived"]
    if pending:
        print(f"\n{len(pending)} PV(s) still working through the archive "
              "workflow; re-run this tool to check progress.")


if __name__ == "__main__":
    main()
