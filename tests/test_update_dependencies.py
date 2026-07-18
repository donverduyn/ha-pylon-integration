"""Focused tests for dependency version-policy helpers and generated values."""

from collections import OrderedDict
from pathlib import Path

import pytest

from scripts import update_dependencies

_ROOT = Path(__file__).parent.parent
_MOVED_NPM_FEATURES = (
    "ghcr.io/devcontainers-extra/features/claude-code:2",
    "ghcr.io/devcontainers-extra/features/opencode:1",
    "ghcr.io/devcontainers/features/copilot-cli:1",
)


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("0.144.1", "0.x"),
        ("7.4.5", "7.x"),
        ("11.10.0", "11.x"),
        ("12.0.0-beta.1", "12.x"),
        ("12.0.0+build.2", "12.x"),
    ],
)
def test_npm_major_range_allows_minor_and_patch_releases(version, expected):
    assert update_dependencies.npm_major_range(version) == expected


def test_npm_major_range_rejects_non_concrete_versions():
    with pytest.raises(SystemExit, match="not a valid npm version"):
        update_dependencies.npm_major_range("0.x")


def test_generated_npm_ranges_match_their_devcontainer_consumers():
    values = update_dependencies.read_env(_ROOT / ".devcontainer" / "tool-versions.env")

    assert (
        frozenset(update_dependencies.NPM_VERSION_PINS)
        == update_dependencies.NPM_MAJOR_RANGE_KEYS
    )

    assert {key: values[key] for key in update_dependencies.NPM_MAJOR_RANGE_KEYS} == {
        "CLAUDE_CODE_VERSION": "2.x",
        "CODEX_VERSION": "0.x",
        "COPILOT_CLI_VERSION": "1.x",
        "KILO_VERSION": "7.x",
        "OPENCODE_VERSION": "1.x",
        "PNPM_VERSION": "11.x",
    }

    devcontainer = (_ROOT / ".devcontainer" / "devcontainer.json").read_text()
    assert '"pnpmVersion": "11.x"' in devcontainer

    lock = (_ROOT / ".devcontainer" / "devcontainer-lock.json").read_text()
    for feature in _MOVED_NPM_FEATURES:
        assert feature not in update_dependencies.FEATURE_OPTION_REFS
        assert feature not in devcontainer
        assert feature not in lock

    post_create = (_ROOT / ".devcontainer" / "postCreate.sh").read_text()
    assert '"@anthropic-ai/claude-code@$CLAUDE_CODE_VERSION"' in post_create
    assert '"@openai/codex@$CODEX_VERSION"' in post_create
    assert '"@github/copilot@$COPILOT_CLI_VERSION"' in post_create
    assert '"@kilocode/cli@$KILO_VERSION"' in post_create
    assert '"opencode-ai@$OPENCODE_VERSION"' in post_create


def test_refresh_tool_versions_ranges_every_npm_package(monkeypatch):
    npm_versions = {
        "@anthropic-ai/claude-code": "2.1.205",
        "@openai/codex": "0.200.3",
        "@github/copilot": "1.2.3",
        "@kilocode/cli": "7.9.1",
        "opencode-ai": "1.18.0",
        "pnpm": "11.12.0",
    }
    monkeypatch.setattr(
        update_dependencies, "latest_npm_version", npm_versions.__getitem__
    )
    monkeypatch.setattr(update_dependencies, "GITHUB_RELEASE_PINS", OrderedDict())
    monkeypatch.setattr(update_dependencies, "GITHUB_BINARY_PINS", OrderedDict())

    def _latest_node_version(_major: int) -> str:
        return "22.23.1"

    monkeypatch.setattr(
        update_dependencies, "latest_node_version", _latest_node_version
    )
    monkeypatch.setattr(
        update_dependencies, "latest_docker_cli_version", lambda: "29.6.1"
    )
    monkeypatch.setattr(update_dependencies, "latest_uv_version", lambda: "0.11.28")

    values = update_dependencies.refresh_tool_versions(
        OrderedDict([("NODE_VERSION", "22.23.1")])
    )

    assert values["CLAUDE_CODE_VERSION"] == "2.x"
    assert values["CODEX_VERSION"] == "0.x"
    assert values["COPILOT_CLI_VERSION"] == "1.x"
    assert values["KILO_VERSION"] == "7.x"
    assert values["OPENCODE_VERSION"] == "1.x"
    assert values["PNPM_VERSION"] == "11.x"
