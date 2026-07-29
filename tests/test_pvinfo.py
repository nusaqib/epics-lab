"""PV Info web UI: SPA served and its same-origin service proxies work."""

import requests

from conftest import wait_for

PVINFO_URL = "http://pvinfo:8080"


def test_spa_is_served():
    response = wait_for(
        lambda: requests.get(f"{PVINFO_URL}/pvinfo/", timeout=10),
        timeout=60, interval=5, desc="pvinfo SPA",
    )
    assert response.status_code == 200
    assert "<div id=\"root\"" in response.text or "PV Info" in response.text


def test_channelfinder_proxy():
    """The nginx same-origin proxy reaches ChannelFinder."""
    response = requests.get(
        f"{PVINFO_URL}/ChannelFinder/resources/channels",
        params={"~name": "LAB:CRYO:TC1:TEMP"}, timeout=15,
    )
    response.raise_for_status()
    channels = response.json()
    assert channels and channels[0]["name"] == "LAB:CRYO:TC1:TEMP"


def test_archiver_proxy():
    """The nginx same-origin proxy reaches the archiver retrieval webapp."""
    response = requests.get(
        f"{PVINFO_URL}/retrieval/data/getData.json",
        params={"pv": "LAB:CRYO:TC1:TEMP", "from": "1970-01-01T00:00:00.000Z"},
        timeout=30,
    )
    assert response.status_code == 200
