import pytest
from pymavlink import mavutil

from droneload.flight import vehicle as fl

mav = mavutil.mavlink
MODES = mavutil.mode_mapping_acm


def heartbeat(mode, armed=False, status=mav.MAV_STATE_STANDBY,
              autopilot=mav.MAV_AUTOPILOT_ARDUPILOTMEGA):
    base = mav.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
    if armed:
        base |= mav.MAV_MODE_FLAG_SAFETY_ARMED
    custom = {v: k for k, v in MODES.items()}[mode]
    return mav.MAVLink_heartbeat_message(mav.MAV_TYPE_QUADROTOR, autopilot,
                                         base, custom, status, 3)


def position(north, east, down):
    return mav.MAVLink_local_position_ned_message(0, north, east, down, 0, 0, 0)


class FakeMaster:
    """Plays queued messages back, and records what was sent."""

    target_system = 1
    target_component = 1

    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []
        self.mav = self

    def recv_match(self, blocking, timeout):
        return self.messages.pop(0) if self.messages else None

    def set_mode(self, mode):
        self.sent.append(("mode", mode))

    def command_long_send(self, system, component, command, confirmation, *params):
        self.sent.append(("command", command, params))

    def set_position_target_local_ned_send(self, *args):
        self.sent.append(("position", args))


@pytest.fixture(autouse=True)
def short_timeouts(monkeypatch):
    for name in ("MODE_TIMEOUT_S", "ARM_TIMEOUT_S", "ARM_RETRY_S", "TAKEOFF_TIMEOUT_S",
                 "MOVE_TIMEOUT_S", "LAND_TIMEOUT_S", "BOOT_TIMEOUT_S"):
        monkeypatch.setattr(fl, name, 0.2)


def test_only_local_simulator_allowed():
    assert fl.is_simulator("tcp:127.0.0.1:5760")
    assert fl.is_simulator("udpin:localhost:14550")
    assert not fl.is_simulator("/dev/ttyACM0")
    assert not fl.is_simulator("tcp:192.168.1.10:5760")
    assert not fl.is_simulator("udpin:0.0.0.0:14550")


def test_main_refuses_real_drone():
    with pytest.raises(SystemExit, match="Refusing"):
        fl.main(["--connect", "/dev/ttyACM0"])


def test_waits_for_boot():
    v = fl.Vehicle(FakeMaster([heartbeat("STABILIZE", status=mav.MAV_STATE_BOOT),
                               heartbeat("STABILIZE")]))
    v.wait_booted()
    assert v.booted and not v.master.messages


def test_ground_station_heartbeat_ignored():
    v = fl.Vehicle(FakeMaster([]))
    v.expected_mode = "GUIDED"
    v._update(heartbeat("STABILIZE", autopilot=mav.MAV_AUTOPILOT_INVALID))
    assert v.mode is None


def test_mode_change_is_pilot_takeover():
    v = fl.Vehicle(FakeMaster([heartbeat("GUIDED", armed=True),
                               heartbeat("LOITER", armed=True)]))
    v.set_mode("GUIDED")
    with pytest.raises(fl.PilotTakeover, match="LOITER"):
        v.takeoff(1.0)


def test_takeoff_waits_for_height():
    v = fl.Vehicle(FakeMaster([position(0, 0, -0.5), position(0, 0, -0.95)]))
    v.takeoff(1.0)
    assert v.altitude() == pytest.approx(0.95)
    assert v.master.sent[0][1] == mav.MAV_CMD_NAV_TAKEOFF


def test_move_waits_for_distance():
    v = fl.Vehicle(FakeMaster([position(2, 3, -1), position(2.5, 3, -1),
                               position(3, 3, -1)]))
    v.move(1.0)
    assert v.position == (3, 3, -1)
    frame, mask, forward = v.master.sent[0][1][3:6]
    assert (frame, mask, forward) == (mav.MAV_FRAME_BODY_OFFSET_NED,
                                      fl.POSITION_ONLY_MASK, 1.0)


def test_demo_lands_after_timeout():
    master = FakeMaster([heartbeat("GUIDED"), heartbeat("GUIDED", armed=True)])
    with pytest.raises(fl.FlightTimeout):
        fl.demo(fl.Vehicle(master))
    assert ("mode", "LAND") in master.sent


def test_demo_does_not_land_after_takeover():
    master = FakeMaster([heartbeat("GUIDED"), heartbeat("GUIDED", armed=True),
                         heartbeat("LOITER", armed=True)])
    with pytest.raises(fl.PilotTakeover):
        fl.demo(fl.Vehicle(master))
    assert ("mode", "LAND") not in master.sent
