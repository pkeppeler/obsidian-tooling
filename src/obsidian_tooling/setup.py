"""Bootstrap a forked checkout of obsidian-tooling for a new user.

Run from the repo root:

    uv run scripts/setup.py

What it does (idempotent — safe to re-run):

- Prompts for the path to your Obsidian vault (or pass `--vault <path>`).
  Enter `local-example/vault` at the prompt to point at the bundled
  skeleton, for trying things out.
- Creates `local/` (gitignored) and seeds `vault-config.toml` and
  `MY-VAULT.md` from the committed `local-example/` templates. The
  `vault-config.toml` is rewritten with the path you gave.
- Creates the `local/vault` symlink pointing at your chosen vault.
- Symlinks each `commands/*.md` into `~/.claude/commands/` so slash
  commands like `/triage` work in Claude Code.

Existing files are skipped unless `--force` is given.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import cast

__all__ = ["link_target", "main", "setup"]

DEFAULT_COMMANDS_INSTALL_DIR = Path.home() / ".claude" / "commands"
TEMPLATE_DIR_NAME = "local-example"
LOCAL_DIR_NAME = "local"
EXAMPLE_VAULT_RELPATH = "local-example/vault"
_PROMPT_ABORT_ERRORS: tuple[type[BaseException], ...] = (EOFError, KeyboardInterrupt)


def _default_repo_root() -> Path:
    """Resolve to <repo>/ when this module sits at src/obsidian_tooling/setup.py."""
    return Path(__file__).resolve().parent.parent.parent


def link_target(target: Path, link_parent: Path, repo_root: Path) -> Path:
    """Choose the best symlink target: relative when both live under `repo_root`, else absolute."""
    abs_target = target.resolve()
    if abs_target.is_relative_to(repo_root):
        return Path(os.path.relpath(abs_target, link_parent.resolve()))
    return abs_target


def _seed_file(
    src: Path,
    dst: Path,
    *,
    force: bool,
    actions: list[str],
    repo_root: Path,
) -> None:
    rel = dst.relative_to(repo_root).as_posix()
    if dst.exists():
        if not force:
            actions.append(f"skip {rel} (already exists; --force to overwrite)")
            return
        # --force overwriting: flag if the destination diverged from the template,
        # so the user can tell whether their customizations just got clobbered.
        if dst.read_bytes() != src.read_bytes():
            actions.append(f"OVERWRITE {rel} (was customized; previous content lost)")
        else:
            actions.append(f"overwrite {rel} (matched template; no content lost)")
        shutil.copy2(src, dst)
        return
    shutil.copy2(src, dst)
    actions.append(f"write {rel}")


def _link_vault(
    vault_link: Path,
    vault_path: Path,
    *,
    repo_root: Path,
    force: bool,
    actions: list[str],
) -> None:
    rel = vault_link.relative_to(repo_root).as_posix()

    # In-repo vault: user wants the vault to BE at local/vault itself (no symlink).
    # Detect by absolute-path equality so a fresh checkout doesn't follow a stale link.
    if vault_path.resolve() == vault_link.resolve():
        if vault_link.is_symlink():
            if not force:
                actions.append(
                    f"skip {rel} (existing symlink; --force to replace with empty directory)"
                )
                return
            vault_link.unlink()
        if vault_link.is_dir():
            actions.append(f"skip {rel}/ (already an in-repo directory)")
            return
        vault_link.mkdir(parents=True)
        actions.append(f"create {rel}/ (empty directory; open it in Obsidian to populate)")
        return

    target = link_target(vault_path, vault_link.parent, repo_root)
    desired_abs = (vault_link.parent / target).resolve()
    if vault_link.is_symlink():
        current_abs = (vault_link.parent / vault_link.readlink()).resolve()
        if current_abs == desired_abs:
            actions.append(f"skip {rel} (already points at {desired_abs})")
            return
        if not force:
            actions.append(
                f"skip {rel} (points at {current_abs}; "
                f"--force to repoint to {desired_abs})"
            )
            return
        vault_link.unlink()
    elif vault_link.exists():
        if not force:
            actions.append(f"skip {rel} (exists as non-symlink; --force to replace)")
            return
        if vault_link.is_dir():
            shutil.rmtree(vault_link)
        else:
            vault_link.unlink()
    vault_link.symlink_to(target)
    actions.append(f"link {rel} -> {target}")


def _seed_vault_skeleton(
    vault_link: Path,
    example_vault: Path,
    *,
    repo_root: Path,
    actions: list[str],
) -> None:
    """Populate an empty vault with the bundled skeleton (Inbox, Dashboard, etc.).

    Runs only when the vault is empty or contains nothing but `.obsidian/` (an
    existing Obsidian config without notes). Never overwrites user content.
    """
    if not vault_link.exists():
        return
    try:
        actual_vault = vault_link.resolve(strict=True)
    except (OSError, RuntimeError):
        return  # dangling symlink or other resolution failure
    if not actual_vault.is_dir():
        return
    # Don't seed the example into itself if a user pointed --vault directly at it.
    if actual_vault == example_vault.resolve():
        return
    user_content = [p for p in actual_vault.iterdir() if p.name != ".obsidian"]
    if user_content:
        return
    for src in example_vault.iterdir():
        if src.name == ".obsidian":
            continue
        dst = actual_vault / src.name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    rel = vault_link.relative_to(repo_root).as_posix()
    actions.append(f"seed {rel}/ with skeleton from {EXAMPLE_VAULT_RELPATH}/")


def _install_slash_commands(
    commands_dir: Path,
    install_dir: Path,
    *,
    force: bool,
    actions: list[str],
) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    for cmd in sorted(commands_dir.glob("*.md")):
        dst = install_dir / cmd.name
        target = cmd.resolve()
        if dst.is_symlink():
            current = dst.readlink().resolve()
            if current == target:
                actions.append(f"skip {dst} (already linked to {target})")
                continue
            if not force:
                actions.append(
                    f"skip {dst} (points at {current}; "
                    f"--force to relink to {target})"
                )
                continue
            dst.unlink()
        elif dst.exists():
            if not force:
                actions.append(f"skip {dst} (exists as non-symlink; --force to replace)")
                continue
            dst.unlink()
        dst.symlink_to(target)
        actions.append(f"link {dst} -> {target}")


def setup(
    vault_path: Path,
    *,
    repo_root: Path,
    commands_install_dir: Path,
    force: bool = False,
    force_link: bool = False,
) -> list[str]:
    """Seed `local/` from `local-example/` and install slash commands.

    `force` overwrites everything: seed files, vault symlink, command links.
    `force_link` only forces symlink repointing (vault + commands); seed
    files in `local/` are left alone. This is the safe knob for "I just
    moved my vault and need to repoint local/vault without risking my
    customized local/MY-VAULT.md."

    Returns a list of human-readable action descriptions for the final summary.
    """
    template_dir = repo_root / TEMPLATE_DIR_NAME
    local_dir = repo_root / LOCAL_DIR_NAME
    example_vault = repo_root / TEMPLATE_DIR_NAME / "vault"
    local_dir.mkdir(exist_ok=True)
    actions: list[str] = []
    force_symlinks = force or force_link

    # If the user pointed --vault at the tracked example, redirect to local/vault
    # (an in-repo gitignored copy) so /triage doesn't mutate tracked files.
    if vault_path.exists() and vault_path.resolve() == example_vault.resolve():
        vault_path = local_dir / "vault"
        actions.append(
            f"redirect {EXAMPLE_VAULT_RELPATH} -> local/vault "
            "(demo runs in a gitignored copy; tracked example stays clean)"
        )

    for name in ("vault-config.toml", "MY-VAULT.md"):
        _seed_file(
            template_dir / name,
            local_dir / name,
            force=force,
            actions=actions,
            repo_root=repo_root,
        )
    _link_vault(
        local_dir / "vault",
        vault_path,
        repo_root=repo_root,
        force=force_symlinks,
        actions=actions,
    )
    _seed_vault_skeleton(
        local_dir / "vault",
        example_vault,
        repo_root=repo_root,
        actions=actions,
    )
    _install_slash_commands(
        repo_root / "commands",
        commands_install_dir,
        force=force_symlinks,
        actions=actions,
    )
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap a forked checkout of obsidian-tooling for a new user.",
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="Path to your Obsidian vault. If omitted, you'll be prompted.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing local/ files and repoint existing symlinks.",
    )
    parser.add_argument(
        "--force-link",
        action="store_true",
        help=(
            "Repoint existing symlinks (vault + slash commands) without "
            "touching local/ seed files. Use this when you've moved your "
            "vault and want to re-link without risking your customized "
            "local/MY-VAULT.md or local/vault-config.toml."
        ),
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Don't prompt for missing values; fail instead.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override the repo root (default: derived from this script's location).",
    )
    parser.add_argument(
        "--commands-install-dir",
        type=Path,
        default=None,
        help=f"Where to symlink slash commands (default: {DEFAULT_COMMANDS_INSTALL_DIR}).",
    )
    args = parser.parse_args(argv)
    force = cast(bool, args.force)
    force_link = cast(bool, args.force_link)
    non_interactive = cast(bool, args.non_interactive)
    vault_path = cast("Path | None", args.vault)
    repo_root_override = cast("Path | None", args.repo_root)
    commands_install_dir_override = cast("Path | None", args.commands_install_dir)

    repo_root = (repo_root_override or _default_repo_root()).resolve()
    commands_install_dir = commands_install_dir_override or DEFAULT_COMMANDS_INSTALL_DIR

    if vault_path is None:
        if non_interactive:
            print("error: --vault is required in --non-interactive mode", file=sys.stderr)
            return 2
        prompt = (
            "Where's your Obsidian vault?\n"
            "  Enter a path (absolute, ~-prefixed, or repo-relative to obsidian-tooling/).\n"
            "  To try the bundled example, enter: local-example/vault\n"
            "> "
        )
        while True:
            try:
                response = input(prompt).strip()
            except _PROMPT_ABORT_ERRORS:
                print("\naborted.", file=sys.stderr)
                return 130
            if response:
                vault_path = Path(response).expanduser()
                break
            print("Please enter a path (or Ctrl+C to abort).", file=sys.stderr)

    if not vault_path.is_absolute():
        vault_path = (repo_root / vault_path).resolve()
    else:
        vault_path = vault_path.expanduser().resolve()

    if not vault_path.exists():
        print(
            f"warning: vault path {vault_path} does not exist yet. "
            "The symlink will be created anyway.",
            file=sys.stderr,
        )

    actions = setup(
        vault_path,
        repo_root=repo_root,
        commands_install_dir=commands_install_dir,
        force=force,
        force_link=force_link,
    )

    print("\nSetup complete:")
    for action in actions:
        print(f"  - {action}")
    print(
        "\nNext steps:"
        "\n  1. Edit local/MY-VAULT.md with your personal context and routing rules."
        "\n  2. Edit local/vault-config.toml if you want to customize sweep sources"
        "\n     or enable the Calendar MCP integration."
        "\n  3. Open your vault in Obsidian and install two community plugins"
        "\n     (Settings -> Community plugins -> Browse): 'Tasks' and 'Dataview'."
        "\n     The dashboard and sweep workflow depend on Tasks."
        "\n  4. If your vault is empty, copy the bundled skeleton into it:"
        "\n       cp -r local-example/vault/* local/vault/"
        "\n     (PowerShell: Copy-Item -Recurse local-example\\vault\\* local\\vault\\)"
        "\n  5. Run /triage in Claude Code to try the inbox-triage protocol."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
