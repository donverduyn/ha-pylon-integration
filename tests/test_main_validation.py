"""Unit tests for main()'s startup config validation (docker/main.py).

Every check here runs and exits(1) before any socket/MQTT connection is
attempted, so these are safe to exercise directly without mocking I/O.
"""

import main
import pytest


def test_invalid_connection_type_exits_before_connecting(monkeypatch, caplog) -> None:
    """A typo like CONNECTION_TYPE=tpc must fail validation up front rather
    than silently falling through to the serial branch (every check in the
    codebase is `if CONNECTION_TYPE == "tcp": ... else: # serial`), which
    would produce misleading serial-port errors for what was meant to be a
    TCP connection."""
    import logging

    monkeypatch.setattr(main, "MQTT_BROKER", "localhost")
    monkeypatch.setattr(main, "CONNECTION_TYPE", "tpc")

    with caplog.at_level(logging.ERROR, logger="pylon2mqtt"):
        with pytest.raises(SystemExit) as exc_info:
            main.main()

    assert exc_info.value.code == 1
    assert "CONNECTION_TYPE must be" in caplog.text


def test_valid_connection_types_pass_this_check(monkeypatch, caplog) -> None:
    """"tcp" must not be rejected by the new guard itself — the SystemExit(1)
    it still hits next (TCP_HOST is left empty) must come from the
    *existing* TCP_HOST check, not a false-positive CONNECTION_TYPE
    rejection."""
    import logging

    monkeypatch.setattr(main, "MQTT_BROKER", "localhost")
    monkeypatch.setattr(main, "CONNECTION_TYPE", "tcp")
    monkeypatch.setattr(main, "TCP_HOST", "")

    with caplog.at_level(logging.ERROR, logger="pylon2mqtt"):
        with pytest.raises(SystemExit) as exc_info:
            main.main()

    assert exc_info.value.code == 1
    assert "TCP_HOST is required" in caplog.text
    assert "CONNECTION_TYPE must be" not in caplog.text
