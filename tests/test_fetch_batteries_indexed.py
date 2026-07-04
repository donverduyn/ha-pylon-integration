"""Unit tests for main._fetch_batteries_indexed — the 'pwr N' fallback path
used when the aggregate 'pwr' response doesn't look valid.
"""

import main
import pytest
from structs import PylontechSystem


class _FakeBms:
    """Duck-types BmsConnection.send_command against canned 'pwr N' blocks."""

    def __init__(self, responses: dict):
        self._responses = responses
        self.calls: list[str] = []

    def send_command(self, cmd: str) -> str:
        self.calls.append(cmd)
        bat_id = int(cmd.split()[1])
        return self._responses.get(bat_id, f"Power {bat_id} not found")


def _pwr_block(
    bat_id: int, *, voltage=51200, current=3806, temp=17000, soc=75, status="Charge"
) -> str:
    return (
        f"Power {bat_id}\r\n"
        f"Voltage         : {voltage}   mV\r\n"
        f"Current         : {current}    mA\r\n"
        f"Temperature     : {temp}   mC\r\n"
        f"Coulomb         : {soc}      %\r\n"
        f"Basic Status    : {status}\r\n"
        f"Volt Status     : Normal\r\n"
        f"Current Status  : Normal\r\n"
        f"Tmpr. Status    : Normal\r\n"
        f"Coul. Status    : Normal\r\n"
        f"Bat Events      : 0x0\r\n"
        f"Power Events    : 0x0\r\n"
        f"System Fault    : 0x0\r\n"
    )


def _new_system(**overrides) -> PylontechSystem:
    system = PylontechSystem(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    for key, value in overrides.items():
        setattr(system, key, value)
    return system


def test_stops_at_not_found(monkeypatch):
    monkeypatch.setattr(main, "MAX_BATTERIES", 16)
    bms = _FakeBms({1: _pwr_block(1), 2: _pwr_block(2)})
    system = _new_system()

    main._fetch_batteries_indexed(bms, system)

    assert [b.sys_id for b in system.batteries] == [1, 2]
    assert bms.calls == ["pwr 1", "pwr 2", "pwr 3"]


def test_skips_absent_slots_and_continues(monkeypatch):
    """An Absent slot in the middle of the range must be skipped, not treated
    as the end of the stack."""
    monkeypatch.setattr(main, "MAX_BATTERIES", 16)
    bms = _FakeBms(
        {
            1: _pwr_block(1),
            2: "Power 2\r\nBasic Status    : Absent\r\n",
            3: _pwr_block(3),
        }
    )
    system = _new_system()

    main._fetch_batteries_indexed(bms, system)

    assert [b.sys_id for b in system.batteries] == [1, 3]


def test_respects_max_batteries_cap(monkeypatch):
    monkeypatch.setattr(main, "MAX_BATTERIES", 3)
    bms = _FakeBms({i: _pwr_block(i) for i in range(1, 10)})
    system = _new_system()

    main._fetch_batteries_indexed(bms, system)

    assert len(system.batteries) == 3
    assert bms.calls == ["pwr 1", "pwr 2", "pwr 3"]


def test_aggregates_system_metrics(monkeypatch):
    monkeypatch.setattr(main, "MAX_BATTERIES", 16)
    bms = _FakeBms(
        {
            1: _pwr_block(1, voltage=51200, current=3000, soc=80),
            2: _pwr_block(2, voltage=51000, current=-1000, soc=70),
        }
    )
    system = _new_system()

    main._fetch_batteries_indexed(bms, system)

    assert system.voltage == pytest.approx((51.2 + 51.0) / 2, rel=1e-3)
    assert system.current == pytest.approx(3.0 - 1.0, rel=1e-3)
    assert system.soc == pytest.approx((80 + 70) / 2, rel=1e-3)
    assert system.power == pytest.approx(
        sum(b.power for b in system.batteries), rel=1e-3
    )


def test_no_batteries_zeroes_metrics(monkeypatch):
    """A prior poll's stale non-zero totals must not survive an empty result."""
    monkeypatch.setattr(main, "MAX_BATTERIES", 2)
    bms = _FakeBms({})  # every probe returns "not found"
    system = _new_system(voltage=51.0, current=20.0, soc=80.0, power=1020.0)

    main._fetch_batteries_indexed(bms, system)

    assert system.batteries == []
    assert system.voltage == 0.0
    assert system.current == 0.0
    assert system.soc == 0.0
    assert system.power == 0.0
