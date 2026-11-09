"""Flies in the ArduPilot simulator. Opt in: DRONELOAD_SITL=1 python -m pytest tests/test_flight_sitl.py"""

import os
import subprocess
import time

import pytest
from pymavlink import mavutil

from droneload.flight import vehicle as fl

pytestmark = pytest.mark.skipif(not os.environ.get("DRONELOAD_SITL"),
                                reason="set DRONELOAD_SITL=1 to fly in the simulator")


SPEEDUP = 5


@pytest.fixture(scope="module")
def vehicle():
    sim = subprocess.Popen(["bash", "scripts/sim.sh", "--speedup", str(SPEEDUP)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    # Simulated time runs faster, so heartbeats must too, or the failsafe fires
    period = fl.HEARTBEAT_PERIOD_S
    fl.HEARTBEAT_PERIOD_S = period / SPEEDUP
    try:
        time.sleep(2)
        yield fl.Vehicle.connect(fl.DEFAULT_CONNECT)
    finally:
        fl.HEARTBEAT_PERIOD_S = period
        sim.terminate()
        sim.wait(timeout=10)


def take_off(v):
    v.set_mode(fl.MISSION_MODE)
    v.arm()
    v.takeoff(fl.DEMO_ALT_M)


def wait_landed(v):
    v.expected_mode = None
    v._wait(lambda msg: not v.armed, fl.LAND_TIMEOUT_S, "landing")


def test_demo_flight(vehicle):
    fl.demo(vehicle)
    assert not vehicle.armed
    assert fl.horizontal_distance((0, 0), vehicle.position) == pytest.approx(1.0, abs=0.3)


def test_pilot_takeover(vehicle):
    # A second link stands in for the pilot's transmitter
    pilot = mavutil.mavlink_connection("tcp:127.0.0.1:5762")
    pilot.wait_heartbeat(timeout=10)
    take_off(vehicle)
    pilot.set_mode("LOITER")
    with pytest.raises(fl.PilotTakeover):
        vehicle.move(5.0)
    pilot.set_mode("LAND")
    wait_landed(vehicle)


def test_failsafe_lands_when_program_stops(vehicle):
    take_off(vehicle)
    # Read messages without sending heartbeats, as if the program had hung
    landing = None
    deadline = time.monotonic() + 10
    while landing is None and time.monotonic() < deadline:
        msg = vehicle.master.recv_match(type="HEARTBEAT", blocking=True, timeout=0.5)
        if msg and msg.autopilot != mavutil.mavlink.MAV_AUTOPILOT_INVALID \
                and mavutil.mode_string_v10(msg) == fl.LAND_MODE:
            landing = msg
    assert landing is not None, "failsafe did not switch to LAND"
    wait_landed(vehicle)
