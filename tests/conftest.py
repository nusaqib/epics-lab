"""Shared fixtures for the EPICS Lab integration tests.

All PV traffic is routed through the gateways (EPICS_CA_ADDR_LIST /
EPICS_PVA_ADDR_LIST are set in compose.yaml), so a passing suite proves the
whole chain IOC -> gateway -> client works.
"""

from __future__ import annotations

import os
import time

import pytest

ARCHIVER_URL = os.environ.get("ARCHIVER_URL", "http://archiver:17665")
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:29092")
ALARM_TOPIC = os.environ.get("ALARM_TOPIC", "Lab")


def wait_for(check, timeout: float, interval: float = 2.0, desc: str = "condition"):
    """Poll `check` until it returns a truthy value or `timeout` expires."""
    deadline = time.monotonic() + timeout
    last_exc = None
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except Exception as exc:  # noqa: BLE001 — services may still be starting
            last_exc = exc
        time.sleep(interval)
    raise TimeoutError(f"Timed out waiting for {desc} (last error: {last_exc})")


@pytest.fixture(scope="session")
def pva():
    """PV Access client context (routed through the PVA gateway)."""
    from p4p.client.thread import Context

    context = Context("pva")
    yield context
    context.close()
