"""Commands an ArduPilot copter over MAVLink. Simulator only for now.

Run: python -m droneload.flight --connect tcp:127.0.0.1:5760
"""

import argparse
import math
import sys
import time

from pymavlink import mavutil

# ===== SETTINGS =====
DEFAULT_CONNECT   = "tcp:127.0.0.1:5760"   # ArduPilot simulator, instance 0
SIMULATOR_HOSTS   = ("127.0.0.1", "localhost")
MISSION_MODE      = "GUIDED"
LAND_MODE         = "LAND"
POSITION_RATE_HZ  = 10        # LOCAL_POSITION_NED stream rate
RECV_TIMEOUT_S    = 0.5       # longest wait for one message
HEARTBEAT_TIMEOUT_S = 30
HEARTBEAT_PERIOD_S = 1        # if these stop, ArduPilot's GCS failsafe lands the drone
FAILSAFE_PARAM    = "FS_GCS_ENABLE"   # set in failsafe.parm
PARAM_TIMEOUT_S   = 5
BOOT_TIMEOUT_S    = 60        # commands sent while booting can be undone
MODE_TIMEOUT_S    = 10
ARM_TIMEOUT_S     = 60        # the simulator needs time for its position estimate
ARM_RETRY_S       = 2
TAKEOFF_TIMEOUT_S = 30
MOVE_TIMEOUT_S    = 30
LAND_TIMEOUT_S    = 60
ALT_TOLERANCE_M   = 0.1
MOVE_TOLERANCE_M  = 0.15
DEMO_ALT_M        = 1.0
DEMO_FORWARD_M    = 1.0

# Position only: ignore velocity, acceleration, yaw and yaw rate
POSITION_ONLY_MASK = 0b110111111000


class PilotTakeover(Exception):
    """The flight mode changed without this program asking."""


class FlightTimeout(Exception):
    """The vehicle did not do what was asked in time."""


class FailsafeOff(Exception):
    """The flight controller would not land if this program stopped."""


def is_simulator(url):
    """True if url reaches a simulator on this computer, not a real drone."""
    parts = url.split(":")
    return len(parts) == 3 and parts[0] in ("tcp", "udp", "udpin", "udpout") \
        and parts[1] in SIMULATOR_HOSTS


class Vehicle:
    """One MAVLink connection. Any mode change by the pilot raises PilotTakeover."""

    def __init__(self, master):
        self.master        = master
        self.mode          = None
        self.booted        = False
        self.armed         = False
        self.position      = None   # (north, east, down) in metres from home
        self.expected_mode = None   # None while no mode is being held
        self.last_beat     = None   # when this program last sent a heartbeat

    @classmethod
    def connect(cls, url):
        master = mavutil.mavlink_connection(url)
        if master.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT_S) is None:
            raise FlightTimeout(f"no heartbeat from {url}")
        vehicle = cls(master)
        vehicle.wait_booted()
        vehicle.request_position_stream()
        return vehicle

    def wait_booted(self):
        self._wait(lambda msg: self.booted, BOOT_TIMEOUT_S, "boot")

    def request_position_stream(self):
        self._command(mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                      mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
                      1e6 / POSITION_RATE_HZ)

    def set_mode(self, mode):
        self.expected_mode = None
        self.master.set_mode(mode)
        self._wait(lambda msg: self.mode == mode, MODE_TIMEOUT_S, f"mode {mode}")
        self.expected_mode = mode

    def param(self, name):
        self.master.mav.param_request_read_send(
            self.master.target_system, self.master.target_component, name.encode(), -1)
        msg = self._wait(lambda msg: msg is not None and msg.get_type() == "PARAM_VALUE"
                         and msg.param_id == name, PARAM_TIMEOUT_S, f"parameter {name}")
        return msg.param_value

    def arm(self):
        """Arms only if the flight controller lands when this program stops."""
        if not self.param(FAILSAFE_PARAM):
            raise FailsafeOff(f"{FAILSAFE_PARAM} is 0: load droneload/flight/failsafe.parm")
        deadline = time.monotonic() + ARM_TIMEOUT_S
        while not self.armed:
            if time.monotonic() > deadline:
                raise FlightTimeout("arming")
            self._command(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 1)
            try:
                self._wait(lambda msg: self.armed, ARM_RETRY_S, "arming")
            except FlightTimeout:
                pass   # pre-arm checks not passed yet; ask again

    def takeoff(self, alt_m):
        self._command(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, alt_m)
        self._wait(lambda msg: self.altitude() >= alt_m - ALT_TOLERANCE_M,
                   TAKEOFF_TIMEOUT_S, f"takeoff to {alt_m} m")

    def move(self, forward_m, right_m=0.0):
        """Move relative to the drone's position and heading, at the same height."""
        self._wait(lambda msg: self.position, TAKEOFF_TIMEOUT_S, "position")
        start = self.position
        self.master.mav.set_position_target_local_ned_send(
            0, self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, POSITION_ONLY_MASK,
            forward_m, right_m, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        target = math.hypot(forward_m, right_m)
        self._wait(lambda msg: abs(horizontal_distance(start, self.position) - target)
                   <= MOVE_TOLERANCE_M, MOVE_TIMEOUT_S, f"move {target} m")

    def land(self):
        self.set_mode(LAND_MODE)
        self._wait(lambda msg: not self.armed, LAND_TIMEOUT_S, "landing")

    def altitude(self):
        return -self.position[2] if self.position else 0.0

    def _command(self, command, *params):
        params = (list(params) + [0] * 7)[:7]
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            command, 0, *params)

    def _wait(self, done, timeout_s, what):
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            self._heartbeat()
            msg = self.master.recv_match(blocking=True, timeout=RECV_TIMEOUT_S)
            if msg is not None:
                self._update(msg)
            if done(msg):
                return msg
        raise FlightTimeout(what)

    def _heartbeat(self):
        now = time.monotonic()
        if self.last_beat is None or now - self.last_beat >= HEARTBEAT_PERIOD_S:
            self.master.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                                           mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
            self.last_beat = now

    def _update(self, msg):
        kind = msg.get_type()
        if kind == "HEARTBEAT":
            if msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_INVALID:
                return   # a ground station, not the flight controller
            self.mode  = mavutil.mode_string_v10(msg)
            self.armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            self.booted = msg.system_status not in (mavutil.mavlink.MAV_STATE_UNINIT,
                                                    mavutil.mavlink.MAV_STATE_BOOT)
            if self.expected_mode and self.mode != self.expected_mode:
                raise PilotTakeover(self.mode)
        elif kind == "LOCAL_POSITION_NED":
            self.position = (msg.x, msg.y, msg.z)


def horizontal_distance(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def demo(vehicle, alt_m=DEMO_ALT_M, forward_m=DEMO_FORWARD_M):
    """Take off, move forward and land. Lands on any failure except a pilot takeover."""
    vehicle.set_mode(MISSION_MODE)
    vehicle.arm()
    try:
        vehicle.takeoff(alt_m)
        vehicle.move(forward_m)
    except PilotTakeover:
        raise
    except Exception:
        vehicle.land()
        raise
    vehicle.land()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simulator demo flight")
    parser.add_argument("--connect", default=DEFAULT_CONNECT,
                        help=f"MAVLink address (default: {DEFAULT_CONNECT})")
    parser.add_argument("--alt", type=float, default=DEMO_ALT_M, help="takeoff height, m")
    parser.add_argument("--forward", type=float, default=DEMO_FORWARD_M, help="distance, m")
    args = parser.parse_args(argv)

    if not is_simulator(args.connect):
        sys.exit(f"Refusing {args.connect}: only a simulator on this computer is allowed.")

    vehicle = Vehicle.connect(args.connect)
    try:
        demo(vehicle, args.alt, args.forward)
    except PilotTakeover as e:
        sys.exit(f"Mode changed to {e} by the pilot or a failsafe. Mission stopped.")
    except FailsafeOff as e:
        sys.exit(f"Not arming: {e}")
    except FlightTimeout as e:
        sys.exit(f"Timed out: {e}")
    print("Demo flight complete.")
