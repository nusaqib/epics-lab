"""caPutLog: trapped CA writes end up in the central caput log.

The tests container mounts the caputlog volume read-only at /caputlog, so
after writing a PV through the CA gateway the put must appear in the log
file (via IOC access-security TRAPWRITE -> caPutLog -> iocLogServer).
"""

import pathlib

from caproto.sync.client import read, write

from conftest import wait_for

LOG_FILE = pathlib.Path("/caputlog/caput.log")
PV = "LAB:CRYO:TC1:SP"


def test_caput_is_logged():
    original = float(read(PV, timeout=15).data[0])
    marker = 83.25  # distinctive value to look for in the log
    try:
        write(PV, [marker], notify=True, timeout=15)

        def logged():
            if not LOG_FILE.exists():
                return False
            text = LOG_FILE.read_text(errors="replace")
            return PV in text and "83.25" in text

        wait_for(logged, timeout=90, interval=3,
                 desc=f"put on {PV} to appear in {LOG_FILE}")
    finally:
        write(PV, [original], notify=True, timeout=15)
