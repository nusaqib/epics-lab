"""Behavioral checks of the simulated subsystems (through the PVA gateway)."""

import time

from conftest import wait_for


def test_motion_moves_to_target(pva):
    """Commanding a move slews the readback to the target at finite speed."""
    original = float(pva.get("LAB:MOT:M1:SP", timeout=15))
    target = 10.0 if abs(original - 10.0) > 1.0 else -10.0
    try:
        pva.put("LAB:MOT:M1:SP", target, timeout=15)

        # DMOV must drop while moving...
        moving = wait_for(
            lambda: float(pva.get("LAB:MOT:M1:DMOV", timeout=10)) == 0.0,
            timeout=10, interval=0.2, desc="axis to start moving",
        )
        assert moving

        # ...and the axis must arrive.
        wait_for(
            lambda: float(pva.get("LAB:MOT:M1:DMOV", timeout=10)) == 1.0,
            timeout=60, interval=0.5, desc="axis to reach target",
        )
        rbv = float(pva.get("LAB:MOT:M1:RBV", timeout=10))
        assert abs(rbv - target) < 0.01
    finally:
        pva.put("LAB:MOT:M1:SP", original, timeout=15)


def test_cryo_cools_towards_setpoint(pva):
    """With the compressor running, the cold head approaches the setpoint."""
    pva.put("LAB:CRYO:CMP1:RUN", 1, timeout=15)
    setpoint = float(pva.get("LAB:CRYO:TC1:SP", timeout=15))
    start = float(pva.get("LAB:CRYO:TC1:TEMP", timeout=15))
    if abs(start - setpoint) < 5:
        return  # already converged — nothing to prove
    time.sleep(20)
    now = float(pva.get("LAB:CRYO:TC1:TEMP", timeout=15))
    assert abs(now - setpoint) < abs(start - setpoint), (
        f"temperature not converging: {start} -> {now} (SP {setpoint})"
    )


def test_vacuum_pumpdown(pva):
    """With the pump at speed the chamber reaches good vacuum, and the
    interlock permit follows the pressure."""
    pva.put("LAB:VAC:PMP1:RUN", 1, timeout=15)
    wait_for(
        lambda: float(pva.get("LAB:VAC:PMP1:SPEED", timeout=10)) > 80,
        timeout=120, desc="turbo pump at speed",
    )
    wait_for(
        lambda: float(pva.get("LAB:VAC:GA1:PRES", timeout=10)) < 1e-4,
        timeout=180, desc="chamber below 1e-4 mbar",
    )
    assert float(pva.get("LAB:VAC:ILK:OK", timeout=10)) == 1.0
