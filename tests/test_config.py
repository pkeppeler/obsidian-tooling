"""Tests for the vault-config loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from obsidian_tooling.config import (
    DEFAULT_CONFIG_PATH,
    EXAMPLE_CONFIG_PATH,
    VaultConfig,
    load_config,
)


def test_defaults_match_documented_shape() -> None:
    config = VaultConfig()
    assert config.vault.path == Path("local/vault")
    assert config.vault.inbox == "00 Inbox.md"
    assert config.sweep.sources == ("Next Actions.md",)
    assert config.sweep.archive_dir == "Archive"
    assert config.integrations.calendar_tool == ""


def test_load_config_reads_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "vault-config.toml"
    config_path.write_text(
        "[vault]\n"
        'path = "/some/vault"\n'
        'inbox = "Inbox.md"\n'
        "\n"
        "[sweep]\n"
        'sources = ["Next Actions.md", "Shopping.md"]\n'
        'archive_dir = "Done"\n'
        "\n"
        "[integrations]\n"
        'calendar_tool = "mcp__example__create_event"\n',
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.vault.path == Path("/some/vault")
    assert config.vault.inbox == "Inbox.md"
    assert config.sweep.sources == ("Next Actions.md", "Shopping.md")
    assert config.sweep.archive_dir == "Done"
    assert config.integrations.calendar_tool == "mcp__example__create_event"


def test_load_config_uses_defaults_for_missing_sections(tmp_path: Path) -> None:
    config_path = tmp_path / "vault-config.toml"
    config_path.write_text('[vault]\npath = "/v"\n', encoding="utf-8")
    config = load_config(config_path)
    assert config.vault.path == Path("/v")
    assert config.sweep.sources == ("Next Actions.md",)
    assert config.integrations.calendar_tool == ""


def test_load_config_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="vault config not found"):
        load_config(tmp_path / "nope.toml")


def test_load_config_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "vault-config.toml"
    config_path.write_text('[vault]\npath = "/v"\nbogus_field = "x"\n', encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(config_path)


def test_example_config_loads_cleanly() -> None:
    """The committed example TOML must always parse to a valid VaultConfig."""
    config = load_config(EXAMPLE_CONFIG_PATH)
    assert config.sweep.sources  # non-empty default


def test_default_path_constant_matches_documented_location() -> None:
    assert Path("local/vault-config.toml") == DEFAULT_CONFIG_PATH
