"""Tests for the setup bootstrap.

Each test builds a fake repo under `tmp_path` mirroring the real layout
(committed `local-example/` + `commands/`), then calls into `setup()` or
`main()` with explicit `repo_root` / `commands_install_dir` so the test
never touches `~/.claude/commands/` or the real `local/`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from obsidian_tooling.setup import (
    link_target,
    main,
    setup,
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Fake repo with local-example/ + commands/ that setup() can consume."""
    template = tmp_path / "local-example"
    template.mkdir()
    (template / "vault-config.toml").write_text(
        '[vault]\npath = "./local/vault"\ninbox = "00 Inbox.md"\n'
        "\n"
        '[sweep]\nsources = ["Next Actions.md"]\narchive_dir = "Archive"\n',
        encoding="utf-8",
    )
    (template / "MY-VAULT.md").write_text("# My Vault\n\n(template body)\n", encoding="utf-8")
    (template / "vault").mkdir()
    (template / "vault" / "00 Inbox.md").write_text("# 00 Inbox\n", encoding="utf-8")

    commands = tmp_path / "commands"
    commands.mkdir()
    (commands / "triage.md").write_text("---\ndescription: x\n---\nbody\n", encoding="utf-8")

    # Pre-create an external vault directory that tests can target when they
    # want to exercise the external-symlink branch (separate from the example).
    (tmp_path / "external-vault").mkdir()

    return tmp_path


def test_link_target_chooses_relative_for_in_repo_paths(tmp_path: Path) -> None:
    link_parent = tmp_path / "local"
    link_parent.mkdir()
    target = tmp_path / "local-example" / "vault"
    target.mkdir(parents=True)
    result = link_target(target, link_parent, tmp_path)
    assert result == Path("../local-example/vault")


def test_link_target_chooses_absolute_for_out_of_repo_paths(tmp_path: Path) -> None:
    link_parent = tmp_path / "local"
    link_parent.mkdir()
    outside = tmp_path.parent / "elsewhere"
    result = link_target(outside, link_parent, tmp_path)
    assert result.is_absolute()
    assert result == outside.resolve()


def test_setup_seeds_local_and_links_vault(repo: Path) -> None:
    """External-vault path: setup writes seed files and symlinks local/vault."""
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    actions = setup(
        external,
        repo_root=repo,
        commands_install_dir=install,
    )

    local = repo / "local"
    assert (local / "vault-config.toml").exists()
    assert (local / "MY-VAULT.md").exists()
    assert (local / "vault").is_symlink()
    assert (local / "vault").resolve() == external.resolve()

    # vault-config.toml is copied verbatim — the symlink does the routing.
    config = (local / "vault-config.toml").read_text(encoding="utf-8")
    assert 'path = "./local/vault"' in config

    # Slash command was symlinked into the install dir
    assert (install / "triage.md").is_symlink()
    assert (install / "triage.md").resolve() == (repo / "commands" / "triage.md").resolve()

    assert any("write local/vault-config.toml" in a for a in actions)
    assert any("link local/vault" in a for a in actions)


def test_setup_is_idempotent(repo: Path) -> None:
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    first = setup(external, repo_root=repo, commands_install_dir=install)
    second = setup(external, repo_root=repo, commands_install_dir=install)

    # First run writes everything; second run skips because targets exist.
    assert sum("write " in a for a in first) == 2  # vault-config.toml + MY-VAULT.md
    assert all("skip" in a or "link" not in a for a in second if "vault" in a)
    assert sum("skip" in a for a in second) >= 3  # config, MY-VAULT, vault symlink


def test_setup_force_overwrites_existing_files(repo: Path) -> None:
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    setup(external, repo_root=repo, commands_install_dir=install)

    # User-edited content gets overwritten under --force.
    (repo / "local" / "MY-VAULT.md").write_text("# edited\n", encoding="utf-8")
    setup(external, repo_root=repo, commands_install_dir=install, force=True)
    assert "# edited" not in (repo / "local" / "MY-VAULT.md").read_text(encoding="utf-8")


def test_setup_force_warns_loudly_when_overwriting_customized_files(repo: Path) -> None:
    """OVERWRITE (uppercase) in the action lets the user spot what they just lost."""
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    setup(external, repo_root=repo, commands_install_dir=install)

    (repo / "local" / "MY-VAULT.md").write_text("# heavily customized\n", encoding="utf-8")
    actions = setup(external, repo_root=repo, commands_install_dir=install, force=True)
    assert any("OVERWRITE local/MY-VAULT.md" in a and "previous content lost" in a for a in actions)
    # The unmodified vault-config.toml should use the quieter lowercase variant.
    assert any("overwrite local/vault-config.toml" in a and "no content lost" in a for a in actions)


def test_setup_force_link_repoints_symlink_without_touching_seed_files(repo: Path) -> None:
    """--force-link is the safe knob for 'just repoint my vault symlink'."""
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    other_vault = repo / "other-vault"
    other_vault.mkdir()

    setup(external, repo_root=repo, commands_install_dir=install)
    (repo / "local" / "MY-VAULT.md").write_text("# customized\n", encoding="utf-8")

    actions = setup(
        other_vault,
        repo_root=repo,
        commands_install_dir=install,
        force_link=True,
    )

    # Symlink moved.
    assert (repo / "local" / "vault").resolve() == other_vault.resolve()
    # Seed file untouched.
    assert (repo / "local" / "MY-VAULT.md").read_text(encoding="utf-8") == "# customized\n"
    # The existing-but-skipped seed file is reflected in actions, not overwritten.
    assert any("skip local/MY-VAULT.md" in a for a in actions)
    # No action should start with an overwrite verb (skip messages can mention the word).
    assert not any(a.startswith(("OVERWRITE ", "overwrite ", "write local/"))
                   for a in actions)


def test_setup_repoints_existing_symlink_with_force(repo: Path) -> None:
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    other_vault = repo / "other-vault"
    other_vault.mkdir()

    setup(external, repo_root=repo, commands_install_dir=install)
    assert (repo / "local" / "vault").resolve() == external.resolve()

    actions = setup(
        other_vault,
        repo_root=repo,
        commands_install_dir=install,
        force=True,
    )
    assert (repo / "local" / "vault").resolve() == other_vault.resolve()
    assert any("link local/vault" in a for a in actions)


def test_setup_redirects_local_example_vault_to_in_repo(repo: Path) -> None:
    """Pointing --vault at the tracked example redirects to local/vault (in-repo, gitignored)."""
    install = repo / ".claude" / "commands"
    actions = setup(
        repo / "local-example" / "vault",
        repo_root=repo,
        commands_install_dir=install,
    )

    # local/vault is an in-repo directory, NOT a symlink to local-example/vault.
    vault = repo / "local" / "vault"
    assert vault.is_dir()
    assert not vault.is_symlink()
    # Skeleton was copied across so the demo has working content from the start.
    assert (vault / "00 Inbox.md").exists()
    # The tracked example was not modified.
    assert (repo / "local-example" / "vault" / "00 Inbox.md").read_text(encoding="utf-8") == (
        "# 00 Inbox\n"
    )
    assert any("redirect local-example/vault" in a for a in actions)
    assert any("seed local/vault/" in a for a in actions)


def test_setup_seeds_skeleton_into_empty_external_vault(repo: Path) -> None:
    """An empty external vault gets the bundled skeleton on first setup."""
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"  # empty fixture
    actions = setup(external, repo_root=repo, commands_install_dir=install)

    # Skeleton landed in the external vault, not in the symlink itself.
    assert (external / "00 Inbox.md").exists()
    assert any("seed local/vault/" in a for a in actions)


def test_setup_does_not_seed_vault_with_user_content(repo: Path) -> None:
    """If the vault already has notes, leave them alone — never overwrite."""
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    (external / "Existing Note.md").write_text("# do not touch\n", encoding="utf-8")

    actions = setup(external, repo_root=repo, commands_install_dir=install)

    assert (external / "Existing Note.md").read_text(encoding="utf-8") == "# do not touch\n"
    # Skeleton should NOT have been seeded.
    assert not (external / "00 Inbox.md").exists()
    assert not any("seed local/vault/" in a for a in actions)


def test_setup_seeds_vault_with_only_obsidian_config(repo: Path) -> None:
    """An .obsidian/ directory alone is treated as 'infrastructure, not content'."""
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    (external / ".obsidian").mkdir()
    (external / ".obsidian" / "hotkeys.json").write_text("{}\n", encoding="utf-8")

    setup(external, repo_root=repo, commands_install_dir=install)

    # .obsidian preserved.
    assert (external / ".obsidian" / "hotkeys.json").exists()
    # Skeleton still seeded.
    assert (external / "00 Inbox.md").exists()


def test_setup_in_repo_vault_creates_directory_not_symlink(tmp_path: Path) -> None:
    """User entering `local/vault` directly gets an in-repo vault directory."""
    # Build a minimal repo fixture
    template = tmp_path / "local-example"
    template.mkdir()
    (template / "vault-config.toml").write_text(
        '[vault]\npath = "./local/vault"\n', encoding="utf-8"
    )
    (template / "MY-VAULT.md").write_text("# My Vault\n", encoding="utf-8")
    (template / "vault").mkdir()
    (tmp_path / "commands").mkdir()

    actions = setup(
        tmp_path / "local" / "vault",
        repo_root=tmp_path,
        commands_install_dir=tmp_path / ".claude" / "commands",
    )
    vault_link = tmp_path / "local" / "vault"
    assert vault_link.is_dir()
    assert not vault_link.is_symlink()
    assert any("create local/vault/" in a for a in actions)


def test_setup_in_repo_vault_idempotent(tmp_path: Path) -> None:
    template = tmp_path / "local-example"
    template.mkdir()
    (template / "vault-config.toml").write_text(
        '[vault]\npath = "./local/vault"\n', encoding="utf-8"
    )
    (template / "MY-VAULT.md").write_text("# My Vault\n", encoding="utf-8")
    (template / "vault").mkdir()
    (tmp_path / "commands").mkdir()

    setup(
        tmp_path / "local" / "vault",
        repo_root=tmp_path,
        commands_install_dir=tmp_path / ".claude" / "commands",
    )
    # Add a file to the in-repo vault to confirm second run doesn't wipe it
    (tmp_path / "local" / "vault" / "00 Inbox.md").write_text("# Inbox\n", encoding="utf-8")

    actions = setup(
        tmp_path / "local" / "vault",
        repo_root=tmp_path,
        commands_install_dir=tmp_path / ".claude" / "commands",
    )
    assert (tmp_path / "local" / "vault" / "00 Inbox.md").exists()
    assert any("already an in-repo directory" in a for a in actions)


def test_setup_skips_existing_symlink_without_force(repo: Path) -> None:
    install = repo / ".claude" / "commands"
    external = repo / "external-vault"
    other_vault = repo / "other-vault"
    other_vault.mkdir()

    setup(external, repo_root=repo, commands_install_dir=install)
    actions = setup(other_vault, repo_root=repo, commands_install_dir=install)
    # Symlink unchanged
    assert (repo / "local" / "vault").resolve() == external.resolve()
    assert any("--force to repoint" in a for a in actions)


def test_main_fails_in_non_interactive_without_vault(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "--non-interactive",
            "--repo-root",
            str(repo),
            "--commands-install-dir",
            str(repo / ".claude" / "commands"),
        ]
    )
    assert rc == 2
    assert "--vault is required" in capsys.readouterr().err


def test_main_runs_end_to_end_with_vault_flag(repo: Path) -> None:
    rc = main(
        [
            "--vault",
            str(repo / "external-vault"),
            "--non-interactive",
            "--repo-root",
            str(repo),
            "--commands-install-dir",
            str(repo / ".claude" / "commands"),
        ]
    )
    assert rc == 0
    assert (repo / "local" / "vault-config.toml").exists()
    assert (repo / "local" / "vault").is_symlink()
    assert (repo / ".claude" / "commands" / "triage.md").is_symlink()
