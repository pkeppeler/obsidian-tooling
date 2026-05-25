"""Sweep checked `[x]` tasks from configured vault sources into `Archive/Done <YYYY-MM>.md`.

Scope is limited to the files listed in `[sweep].sources` in
`local/vault-config.toml` (see `local-example/vault-config.toml` for the
schema). These are "context-list" files like `Next Actions.md` or
`Shopping.md` — orphan items with no surrounding context worth preserving in
place. Project files, area files, and other vault notes are untouched —
completed tasks in those are project history.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import cast

from obsidian_tooling.config import DEFAULT_CONFIG_PATH, load_config

__all__ = [
    "archive_filename",
    "build_archive_block",
    "main",
    "partition_lines",
    "sweep",
]

CHECKED_PATTERN = re.compile(r"^\s*-\s+\[x\]\s+.*$")


def partition_lines(content: str) -> tuple[list[str], list[str]]:
    """Split `content` into (kept, checked) lines.

    `checked` are `- [x] ...` lines that get harvested.
    `kept` is everything else, in original order, preserved verbatim.
    """
    kept: list[str] = []
    checked: list[str] = []
    for line in content.splitlines():
        if CHECKED_PATTERN.match(line):
            checked.append(line)
        else:
            kept.append(line)
    return kept, checked


def archive_filename(today: date) -> str:
    return f"Done {today.strftime('%Y-%m')}.md"


def build_archive_block(checked: list[str], source_filename: str) -> str:
    """Format harvested lines as a `## From: <source_filename>` section."""
    header = f"## From: {source_filename}"
    return "\n".join([header, *checked]) + "\n"


def _join_lines(lines: list[str], trailing_newline: bool) -> str:
    body = "\n".join(lines)
    if trailing_newline and not body.endswith("\n"):
        body += "\n"
    return body


def sweep(
    vault: Path,
    today: date,
    *,
    dry_run: bool,
    sources: Iterable[str],
    archive_dir: str = "Archive",
) -> int:
    """Sweep every file in `sources` under `vault`. Returns total tasks swept."""
    archive_path = vault / archive_dir / archive_filename(today)
    blocks: list[tuple[str, list[str]]] = []
    pending_writes: list[tuple[Path, str]] = []

    for source_name in sources:
        source = vault / source_name
        if not source.exists():
            continue
        content = source.read_text(encoding="utf-8")
        kept, checked = partition_lines(content)
        if not checked:
            continue
        blocks.append((source_name, checked))
        pending_writes.append((source, _join_lines(kept, content.endswith("\n"))))

    total = sum(len(checked) for _, checked in blocks)
    if total == 0:
        print("0 tasks to sweep.")
        return 0

    rel = archive_path.relative_to(vault)

    if dry_run:
        print(f"[dry-run] Would sweep {total} task(s) to {rel}:")
        for source_name, checked in blocks:
            print(f"  ## From: {source_name}")
            for line in checked:
                print(f"    {line}")
        return total

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    appended = "\n".join(build_archive_block(checked, name) for name, checked in blocks)
    if archive_path.exists():
        existing = archive_path.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            existing += "\n"
        archive_path.write_text(existing + "\n" + appended, encoding="utf-8")
    else:
        archive_path.write_text(appended, encoding="utf-8")

    for source_path, new_content in pending_writes:
        source_path.write_text(new_content, encoding="utf-8")

    parts = [f"{len(checked)} from {name}" for name, checked in blocks]
    print(f"Swept {total} task(s) ({', '.join(parts)}) to {rel}.")
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be swept without modifying any files.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to vault config (default: {DEFAULT_CONFIG_PATH}).",
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="Override the vault path from config.",
    )
    args = parser.parse_args(argv)
    dry_run = cast(bool, args.dry_run)
    config_path = cast(Path, args.config)
    vault_override = cast("Path | None", args.vault)

    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    vault = (vault_override if vault_override is not None else config.vault.path).resolve()
    if not vault.is_dir():
        print(f"Vault directory not found: {vault}", file=sys.stderr)
        return 2

    sweep(
        vault,
        date.today(),
        dry_run=dry_run,
        sources=config.sweep.sources,
        archive_dir=config.sweep.archive_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
