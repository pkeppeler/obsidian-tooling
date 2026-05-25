"""Read `local/vault-config.toml` and expose typed config to scripts + commands.

The committed `local-example/vault-config.toml` documents the schema. Users
copy it into `local/vault-config.toml` (gitignored) via `scripts/setup.py` or
by hand, then edit. Scripts in this repo call `load_config()` to get a typed
`VaultConfig`.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "EXAMPLE_CONFIG_PATH",
    "IntegrationsSection",
    "SweepSection",
    "VaultConfig",
    "VaultSection",
    "load_config",
]

DEFAULT_CONFIG_PATH = Path("local/vault-config.toml")
EXAMPLE_CONFIG_PATH = Path("local-example/vault-config.toml")


class VaultSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: Path = Field(default=Path("local/vault"))
    inbox: str = "00 Inbox.md"


class SweepSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: tuple[str, ...] = ("Next Actions.md",)
    archive_dir: str = "Archive"


class IntegrationsSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar_tool: str = ""


class VaultConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vault: VaultSection = Field(default_factory=VaultSection)
    sweep: SweepSection = Field(default_factory=SweepSection)
    integrations: IntegrationsSection = Field(default_factory=IntegrationsSection)


def load_config(path: Path | None = None) -> VaultConfig:
    """Load and validate vault config from `path` (default: ./local/vault-config.toml).

    Raises FileNotFoundError with a setup hint if no config exists at the
    target path. Pydantic raises ValidationError on schema mismatches.
    """
    config_path = path if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise FileNotFoundError(
            f"vault config not found at {config_path}. "
            f"Copy {EXAMPLE_CONFIG_PATH} to {DEFAULT_CONFIG_PATH} and edit, "
            f"or run `uv run scripts/setup.py`."
        )
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    return VaultConfig.model_validate(data)
