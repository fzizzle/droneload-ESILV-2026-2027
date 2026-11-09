"""Flies in the ArduPilot simulator. Opt in: DRONELOAD_SITL=1 python -m pytest tests/test_flight_sitl.py"""

import math
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


def true_position(v):
    """North and east in metres from the simulator's own position, not the estimate."""
    v.master.mav.command_long_send(
        v.master.target_system, v.master.target_component,
        mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE, 0,
        mavutil.mavlink.MAVLINK_MSG_ID_SIMSTATE, 0, 0, 0, 0, 0, 0)
    msg = v._wait(lambda m: m is not None and m.get_type() == "SIMSTATE", 5, "SIMSTATE")
    lat, lon, _ = fl.ORIGIN
    metres_per_deg = 6378137 * math.pi / 180
    return ((msg.lat / 1e7 - lat) * metres_per_deg,
            (msg.lng / 1e7 - lon) * metres_per_deg * math.cos(math.radians(lat)))


def test_demo_flight_on_optical_flow(vehicle):
    start = true_position(vehicle)
    fl.demo(vehicle)
    assert not vehicle.armed
    assert fl.horizontal_distance((0, 0), vehicle.position) == pytest.approx(1.0, abs=0.3)
    # The estimate comes from optical flow; check the drone really moved
    moved = fl.horizontal_distance(start, true_position(vehicle))
    assert moved == pytest.approx(1.0, abs=0.3)


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
