"""Archiver Appliance: appliance health, PV submission, and data retrieval.

Self-contained: submits its own PV so it does not depend on `make bootstrap`
having run first.
"""

import requests

from conftest import ARCHIVER_URL, wait_for

PV = "LAB:CRYO:TC1:TEMP"


def _get(path, **params):
    response = requests.get(f"{ARCHIVER_URL}{path}", params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def test_appliance_is_up():
    info = wait_for(
        lambda: _get("/mgmt/bpl/getApplianceInfo"),
        timeout=180, interval=5, desc="archiver mgmt webapp",
    )
    assert info["identity"] == "appliance0"


def test_pv_gets_archived():
    status = _get("/mgmt/bpl/getPVStatus", pv=PV)[0]["status"]
    if status == "Not being archived":
        requests.post(
            f"{ARCHIVER_URL}/mgmt/bpl/archivePV",
            json=[{"pv": PV, "samplingperiod": "1.0", "samplingmethod": "MONITOR"}],
            timeout=15,
        ).raise_for_status()

    wait_for(
        lambda: _get("/mgmt/bpl/getPVStatus", pv=PV)[0]["status"] == "Being archived",
        timeout=300, interval=5, desc=f"{PV} to be archived",
    )


def test_data_retrieval():
    """Once archiving, the retrieval webapp returns samples for the PV."""

    def has_samples():
        response = requests.get(
            f"{ARCHIVER_URL}/retrieval/data/getData.json",
            params={"pv": PV, "from": "1970-01-01T00:00:00.000Z"},
            timeout=30,
        )
        if response.status_code != 200:
            return False
        payload = response.json()
        return bool(payload and payload[0].get("data"))

    wait_for(has_samples, timeout=300, interval=10,
             desc=f"archived samples for {PV}")
