"""Every IOC serves its PVs over PV Access through the PVA gateway."""

import pytest

# (pv, lower bound, upper bound) — generous sanity ranges
PVS = [
    ("LAB:CRYO:TC1:TEMP", 0, 400),
    ("LAB:CRYO:TC2:TEMP", 0, 400),
    ("LAB:CRYO:HTR1:POWER", 0, 100),
    ("LAB:CRYO:HE:PRES", 10, 20),
    ("LAB:VAC:GA1:PRES", 1e-10, 1e-2),
    ("LAB:VAC:PMP1:SPEED", 0, 100),
    ("LAB:MOT:M1:RBV", -100, 100),
    ("LAB:CRYO:IOC:HEARTBEAT", 0, None),
    ("LAB:VAC:IOC:HEARTBEAT", 0, None),
    ("LAB:MOT:IOC:HEARTBEAT", 0, None),
]


@pytest.mark.parametrize("pv,low,high", PVS, ids=[p[0] for p in PVS])
def test_pv_readable_and_sane(pva, pv, low, high):
    value = float(pva.get(pv, timeout=15))
    assert value >= low, f"{pv} = {value} below expected range"
    if high is not None:
        assert value <= high, f"{pv} = {value} above expected range"


def test_heartbeat_increments(pva):
    first = float(pva.get("LAB:CRYO:IOC:HEARTBEAT", timeout=15))
    import time

    time.sleep(3)
    second = float(pva.get("LAB:CRYO:IOC:HEARTBEAT", timeout=15))
    assert second > first, "IOC heartbeat is not incrementing"
