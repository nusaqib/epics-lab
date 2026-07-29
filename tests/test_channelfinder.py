"""ChannelFinder directory service, populated automatically by RecSync.

Every IOC carries the reccaster module, so all records must show up in
ChannelFinder with hostName/iocName properties without any manual
registration.
"""

import os

import requests

from conftest import wait_for

CF_URL = os.environ.get("CF_URL", "http://channelfinder:8080/ChannelFinder")


def _channels(pattern):
    response = requests.get(
        f"{CF_URL}/resources/channels", params={"~name": pattern}, timeout=15
    )
    response.raise_for_status()
    return response.json()


def test_service_is_up():
    info = wait_for(
        lambda: requests.get(CF_URL, timeout=10).json(),
        timeout=180, interval=5, desc="ChannelFinder service",
    )
    assert info, "ChannelFinder returned no service info"


def test_recsync_populates_channels():
    channels = wait_for(
        lambda: _channels("LAB:CRYO:TC1:TEMP") or None,
        timeout=300, interval=10, desc="RecSync to register LAB:CRYO:TC1:TEMP",
    )
    properties = {p["name"]: p.get("value") for p in channels[0].get("properties", [])}
    assert "hostName" in properties, f"missing hostName property: {properties}"
    assert "iocName" in properties, f"missing iocName property: {properties}"
    assert properties.get("pvStatus") == "Active"


def test_info_tags_become_properties():
    """db info() tags (infotags in recceiver.conf) surface as CF properties."""
    channels = wait_for(
        lambda: _channels("LAB:CRYO:TC1:TEMP") or None,
        timeout=120, interval=10, desc="LAB:CRYO:TC1:TEMP in ChannelFinder",
    )
    properties = {p["name"]: p.get("value") for p in channels[0]["properties"]}
    assert properties.get("archive") == "monitor@1.0", properties
    assert properties.get("recordType") == "calc", properties
    assert properties.get("recordDesc"), "recordDesc missing"


def test_all_areas_registered():
    for prefix, ioc in (("LAB:CRYO", "ioc-cryo"),
                        ("LAB:VAC", "ioc-vacuum"),
                        ("LAB:MOT", "ioc-motion")):
        channels = wait_for(
            lambda p=prefix: _channels(f"{p}:*") or None,
            timeout=120, interval=10, desc=f"{prefix}:* channels",
        )
        names = {c["name"] for c in channels}
        assert names, f"no channels registered for {prefix}"
        iocs = {p.get("value") for c in channels
                for p in c.get("properties", []) if p["name"] == "iocName"}
        assert ioc in iocs, f"{prefix} channels not attributed to {ioc}: {iocs}"
