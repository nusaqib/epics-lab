"""Channel Access through the CA gateway (read, write, and name filtering)."""

from caproto.sync.client import read, write


def test_read_through_gateway():
    result = read("LAB:CRYO:TC1:TEMP", timeout=15)
    value = float(result.data[0])
    assert 0 <= value <= 400


def test_write_and_readback_through_gateway():
    original = float(read("LAB:CRYO:TC1:SP", timeout=15).data[0])
    try:
        # notify=True waits for put completion; the fire-and-forget default
        # may be dropped when this short-lived client disconnects.
        write("LAB:CRYO:TC1:SP", [90.0], notify=True, timeout=15)
        value = float(read("LAB:CRYO:TC1:SP", timeout=15).data[0])
        assert value == 90.0
    finally:
        write("LAB:CRYO:TC1:SP", [original], notify=True, timeout=15)


def test_gateway_denies_foreign_prefix():
    """The pvlist only ALLOWs LAB:* — anything else must not resolve."""
    import pytest
    from caproto.sync.client import read as ca_read

    with pytest.raises(Exception):
        ca_read("OTHER:SOME:PV", timeout=3)
