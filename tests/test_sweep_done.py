"""Tests for the multi-source sweep.

Sweep scope is the files explicitly passed in via the `sources` parameter
(driven by `local/vault-config.toml` in normal use). Tests pass sources
inline so they don't depend on a config file. Every test asserts that other
files (`Projects.md`, areas, etc.) are byte-identical before and after.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from obsidian_tooling.sweep_done import (
    archive_filename,
    build_archive_block,
    main,
    partition_lines,
    sweep,
)

TODAY = date(2026, 5, 15)
ARCHIVE_REL = "Archive/Done 2026-05.md"
DEFAULT_SOURCES = ("Next Actions.md", "Shopping.md")


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """A minimal vault with Next Actions.md, Shopping.md, and a sentinel Projects.md."""
    (tmp_path / "Next Actions.md").write_text(
        "# Next Actions\n"
        "\n"
        "- [ ] open task #next\n"
        "- [x] renew passport #next ✅ 2026-05-15\n"
        "  - [x] indented sub-task\n"
        "- not a task, just a bullet\n",
        encoding="utf-8",
    )
    (tmp_path / "Shopping.md").write_text(
        "# Shopping\n"
        "\n"
        "## Groceries\n"
        "\n"
        "- [ ] bananas\n"
        "- [x] eggs ✅ 2026-05-15\n"
        "\n"
        "## Household\n"
        "\n"
        "- [x] sponges ✅ 2026-05-15\n"
        "- [ ] shoe rack\n",
        encoding="utf-8",
    )
    (tmp_path / "Projects.md").write_text(
        "# Projects\n"
        "\n"
        "- **Plant a Garden**\n"
        "    - [x] pick sunny spot ✅ 2026-05-14\n"
        "    - [ ] order seeds\n",
        encoding="utf-8",
    )
    return tmp_path


def write_config(vault: Path, sources: tuple[str, ...] = DEFAULT_SOURCES) -> Path:
    """Write a vault-config.toml in `vault`'s parent and return its path."""
    config_path = vault.parent / "vault-config.toml"
    sources_toml = ", ".join(f'"{s}"' for s in sources)
    config_path.write_text(
        f'[vault]\npath = "{vault}"\n\n[sweep]\nsources = [{sources_toml}]\n',
        encoding="utf-8",
    )
    return config_path


def test_partition_lines_separates_checked_from_kept() -> None:
    content = (
        "# Header\n- [ ] unchecked\n- [x] checked one\n  - [x] indented checked\n- regular bullet\n"
    )
    kept, checked = partition_lines(content)
    assert kept == ["# Header", "- [ ] unchecked", "- regular bullet"]
    assert checked == ["- [x] checked one", "  - [x] indented checked"]


def test_archive_filename_uses_year_month() -> None:
    assert archive_filename(date(2026, 5, 15)) == "Done 2026-05.md"
    assert archive_filename(date(2026, 12, 1)) == "Done 2026-12.md"


def test_build_archive_block_has_source_header() -> None:
    block = build_archive_block(["- [x] one", "- [x] two"], "Next Actions.md")
    assert block == "## From: Next Actions.md\n- [x] one\n- [x] two\n"


def test_build_archive_block_uses_supplied_source_name() -> None:
    block = build_archive_block(["- [x] eggs"], "Shopping.md")
    assert block == "## From: Shopping.md\n- [x] eggs\n"


def test_sweep_removes_checked_from_next_actions_and_archives(vault: Path) -> None:
    swept = sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)

    # 2 from Next Actions (renew passport + indented sub) + 2 from Shopping (eggs + sponges)
    assert swept == 4

    next_actions = (vault / "Next Actions.md").read_text(encoding="utf-8")
    assert "[x]" not in next_actions
    assert "- [ ] open task #next" in next_actions
    assert "- not a task, just a bullet" in next_actions

    archive = (vault / ARCHIVE_REL).read_text(encoding="utf-8")
    assert "## From: Next Actions.md\n" in archive
    assert "- [x] renew passport #next ✅ 2026-05-15" in archive
    assert "  - [x] indented sub-task" in archive


def test_sweep_harvests_shopping_md_and_preserves_section_headings(vault: Path) -> None:
    sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)

    shopping = (vault / "Shopping.md").read_text(encoding="utf-8")
    assert "[x]" not in shopping
    assert "## Groceries" in shopping
    assert "## Household" in shopping
    assert "- [ ] bananas" in shopping
    assert "- [ ] shoe rack" in shopping

    archive = (vault / ARCHIVE_REL).read_text(encoding="utf-8")
    assert "## From: Shopping.md\n" in archive
    assert "- [x] eggs ✅ 2026-05-15" in archive
    assert "- [x] sponges ✅ 2026-05-15" in archive


def test_sweep_writes_separate_from_blocks_per_source(vault: Path) -> None:
    sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)
    archive = (vault / ARCHIVE_REL).read_text(encoding="utf-8")
    next_idx = archive.index("## From: Next Actions.md")
    shop_idx = archive.index("## From: Shopping.md")
    assert next_idx < shop_idx


def test_sweep_preserves_completion_annotation(vault: Path) -> None:
    sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)
    archive = (vault / ARCHIVE_REL).read_text(encoding="utf-8")
    assert "✅ 2026-05-15" in archive


def test_sweep_leaves_projects_md_byte_identical(vault: Path) -> None:
    before = (vault / "Projects.md").read_bytes()
    sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)
    after = (vault / "Projects.md").read_bytes()
    assert before == after


def test_dry_run_makes_no_filesystem_changes(vault: Path) -> None:
    next_before = (vault / "Next Actions.md").read_bytes()
    shop_before = (vault / "Shopping.md").read_bytes()
    proj_before = (vault / "Projects.md").read_bytes()

    swept = sweep(vault, TODAY, dry_run=True, sources=DEFAULT_SOURCES)

    assert swept == 4
    assert (vault / "Next Actions.md").read_bytes() == next_before
    assert (vault / "Shopping.md").read_bytes() == shop_before
    assert (vault / "Projects.md").read_bytes() == proj_before
    assert not (vault / ARCHIVE_REL).exists()


def test_sweep_is_idempotent(vault: Path) -> None:
    first = sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)
    second = sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)
    assert first == 4
    assert second == 0


def test_sweep_appends_to_existing_archive(vault: Path) -> None:
    archive_path = vault / ARCHIVE_REL
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text("## From: Next Actions.md\n- [x] earlier task\n", encoding="utf-8")

    sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES)

    archive = archive_path.read_text(encoding="utf-8")
    assert "- [x] earlier task" in archive
    assert "- [x] renew passport #next ✅ 2026-05-15" in archive
    assert "- [x] eggs ✅ 2026-05-15" in archive


def test_sweep_handles_no_source_files(tmp_path: Path) -> None:
    assert sweep(tmp_path, TODAY, dry_run=False, sources=DEFAULT_SOURCES) == 0


def test_sweep_handles_only_one_source_present(tmp_path: Path) -> None:
    (tmp_path / "Shopping.md").write_text(
        "## Groceries\n- [x] milk ✅ 2026-05-15\n- [ ] bread\n", encoding="utf-8"
    )
    assert sweep(tmp_path, TODAY, dry_run=False, sources=DEFAULT_SOURCES) == 1
    archive = (tmp_path / ARCHIVE_REL).read_text(encoding="utf-8")
    assert "## From: Shopping.md" in archive
    assert "## From: Next Actions.md" not in archive


def test_sweep_handles_empty_source_files(tmp_path: Path) -> None:
    (tmp_path / "Next Actions.md").write_text("# Next Actions\n\n", encoding="utf-8")
    (tmp_path / "Shopping.md").write_text("# Shopping\n\n", encoding="utf-8")
    assert sweep(tmp_path, TODAY, dry_run=False, sources=DEFAULT_SOURCES) == 0
    assert not (tmp_path / ARCHIVE_REL).exists()


def test_sweep_respects_custom_archive_dir(vault: Path) -> None:
    sweep(vault, TODAY, dry_run=False, sources=DEFAULT_SOURCES, archive_dir="Done")
    assert not (vault / ARCHIVE_REL).exists()
    assert (vault / "Done" / "Done 2026-05.md").exists()


def test_sweep_respects_custom_sources(vault: Path) -> None:
    # Only sweep Shopping.md; Next Actions.md must remain untouched.
    next_before = (vault / "Next Actions.md").read_bytes()
    sweep(vault, TODAY, dry_run=False, sources=("Shopping.md",))
    assert (vault / "Next Actions.md").read_bytes() == next_before
    archive = (vault / ARCHIVE_REL).read_text(encoding="utf-8")
    assert "## From: Shopping.md" in archive
    assert "## From: Next Actions.md" not in archive


def test_main_returns_zero_on_success(vault: Path) -> None:
    config_path = write_config(vault)
    assert main(["--config", str(config_path)]) == 0


def test_main_vault_flag_overrides_config(vault: Path, tmp_path: Path) -> None:
    # Config points at a bogus path; --vault overrides to the real fixture.
    bogus = tmp_path / "does-not-exist"
    config_path = tmp_path / "vault-config.toml"
    config_path.write_text(
        f'[vault]\npath = "{bogus}"\n\n[sweep]\nsources = ["Next Actions.md"]\n',
        encoding="utf-8",
    )
    assert main(["--config", str(config_path), "--vault", str(vault)]) == 0


def test_main_returns_nonzero_when_vault_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "vault-config.toml"
    missing = tmp_path / "nope"
    config_path.write_text(
        f'[vault]\npath = "{missing}"\n\n[sweep]\nsources = ["Next Actions.md"]\n',
        encoding="utf-8",
    )
    assert main(["--config", str(config_path)]) == 2


def test_main_returns_nonzero_when_config_missing(tmp_path: Path) -> None:
    assert main(["--config", str(tmp_path / "missing.toml")]) == 2
