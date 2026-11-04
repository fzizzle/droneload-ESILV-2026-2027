"""Flies in the ArduPilot simulator. Opt in: DRONELOAD_SITL=1 python -m pytest tests/test_flight_sitl.py"""

import os
import subprocess
import time

import pytest
from pymavlink import mavutil

from droneload.flight import vehicle as fl


@pytest.mark.skipif(not os.environ.get("DRONELOAD_SITL"),
                    reason="set DRONELOAD_SITL=1 to fly in the simulator")
def test_simulator_flight_and_takeover():
    sim = subprocess.Popen(["bash", "scripts/sim.sh", "--speedup", "5"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        time.sleep(2)
        v = fl.Vehicle.connect(fl.DEFAULT_CONNECT)
        fl.demo(v)
        assert not v.armed
        assert fl.horizontal_distance((0, 0), v.position) == pytest.approx(1.0, abs=0.3)

        # A second link stands in for the pilot's transmitter
        pilot = mavutil.mavlink_connection("tcp:127.0.0.1:5762")
        pilot.wait_heartbeat(timeout=10)
        v.set_mode(fl.MISSION_MODE)
        v.arm()
        v.takeoff(fl.DEMO_ALT_M)
        pilot.set_mode("LOITER")
        with pytest.raises(fl.PilotTakeover):
            v.move(5.0)
        pilot.set_mode("LAND")
    finally:
        sim.terminate()
        sim.wait(timeout=10)
