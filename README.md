# obsidian-tooling

A Claude Code-driven GTD scaffold for Obsidian vaults. Opinionated defaults
you can fork and customize: a `/triage` slash command for processing your
inbox, a `sweep-done` script for task archival, and a clean
separation between generic tooling (shared) and personal customization
(`local/`, gitignored).

The vault itself lives outside this repo (synced via Obsidian Sync,
Syncthing, or any other mechanism). This repo is the orchestration layer.
Read [CLAUDE.md](CLAUDE.md) for the conventions Claude follows when
operating on your vault.

## What's in the box

| Surface | What it does |
|---|---|
| `/triage` | Inbox-triage protocol. Reads `local/MY-VAULT.md` for your personal routing rules; proposes a destination + tags for each item, batches obvious ones, asks on ambiguous ones, and ends every pass with `sweep-done.py`. |
| `uv run scripts/sweep-done.py` | Harvests `- [x]` items from configured sweep sources (e.g. `Next Actions.md`, `Shopping.md`) into `vault/Archive/Done <YYYY-MM>.md`. Idempotent; project history is not touched. `--dry-run` to preview. |
| `uv run scripts/setup.py` | One-time bootstrap. Seeds `local/` from `local-example/`, creates the `vault/` symlink, installs slash commands into `~/.claude/commands/`. Re-runnable. |
| `local/vault-config.toml` | Mechanical config: vault path, sweep sources, archive directory, optional Calendar MCP tool name. |
| `local/MY-VAULT.md` | Prose layer: your personal context, "established routing conventions," tag-taxonomy extensions. `/triage` reads this as the source of truth for routing decisions. |

## Prerequisites

Install commands below assume **macOS with [Homebrew](https://brew.sh)**.
For Linux or Windows, swap each `brew` line for your package manager's
equivalent (apt, dnf, winget, scoop, etc.) or follow each tool's docs
linked here.

### Install Homebrew first

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Required

- **[Claude Code](https://claude.com/claude-code)** — runs slash commands
  like `/triage`. Without it you can still run the Python scripts
  (`sweep-done.py` etc.) but lose the inbox-triage flow.
  ```bash
  curl -fsSL https://claude.ai/install.sh | bash
  ```

- **[uv](https://docs.astral.sh/uv/)** — provisions Python 3.14, the
  virtualenv, and all deps. Only mandatory build/runtime dependency.
  ```bash
  brew install uv
  ```

- **[Obsidian](https://obsidian.md)** — the vault editor.
  ```bash
  brew install --cask obsidian
  ```

- **Tasks + Dataview** Obsidian plugins — installed from inside Obsidian
  (Settings → Community plugins → Browse): **Tasks** (`obsidian-tasks-plugin`)
  and **Dataview**. The dashboard queries and the sweep workflow depend
  on them.

### Recommended

- **[VS Code](https://code.visualstudio.com)** — the repo ships
  `.vscode/settings.json` with ruff format-on-save, strict Pylance, and
  absolute imports. Any editor works for the Python side; VS Code +
  Claude Code extension is the smoothest end-to-end setup.
  ```bash
  brew install --cask visual-studio-code
  ```
  Then install the **Claude Code** extension from the VS Code
  Marketplace (search "Claude Code").

### Optional

- **[direnv](https://direnv.net)** — auto-activates the venv from
  `.envrc` when you `cd` into the repo. Hook into your shell per
  [direnv's docs](https://direnv.net/docs/hook.html) after installing.
  ```bash
  brew install direnv
  ```

- **Calendar MCP server** in Claude Code (e.g. the Claude.ai Google
  Calendar MCP). If configured in `vault-config.toml`, `/triage` will
  offer to create calendar events for date-bound inbox items. If not,
  the calendar branch is skipped.

## Choose where your vault lives

`scripts/setup.py` (next step) needs to know where your Obsidian vault is.
You have two options:

### Option A — Bring an existing vault

You already have a vault somewhere (with sync set up via Obsidian Sync,
Syncthing, iCloud, Dropbox, Google Drive, etc.). Your vault stays where it is;
`local/vault` becomes a symlink pointing at it.

→ At the setup prompt, enter the path to your existing vault, e.g.
`~/Documents/MyVault`.

### Option B — Start a brand-new vault inside this repo

You don't have a vault yet. The new vault lives at `local/vault/` inside
the repo (gitignored, so its content never lands in git). Add cross-device
sync later — Obsidian Sync, Syncthing, etc. — when you want to use the
vault from your phone or another machine.

→ At the setup prompt, enter `local/vault`. Setup creates the empty
directory; open it in Obsidian (File → Open vault → select
`local/vault/`) and Obsidian will initialize the vault structure.

### Just trying it out

→ Enter `local-example/vault` at the prompt to point at the bundled
skeleton vault. You can play with `/triage` against safe sample content
without touching your real notes.

## Quickstart

```bash
# Clone (or fork and clone your fork)
git clone https://github.com/<you>/obsidian-tooling.git
cd obsidian-tooling

# Install Python + deps via uv
uv sync --dev

# Bootstrap: prompts for your vault path (see "Choose where your vault lives" above).
# Creates local/, symlinks slash commands into ~/.claude/commands/.
uv run scripts/setup.py
```

After setup:

1. Open `local/MY-VAULT.md` and replace the template content with your own
   personal context and routing conventions.
2. In Claude Code, run `/triage` to test the protocol against your vault
   (or the example vault).
3. Commit nothing inside `local/` — it's gitignored. Promote learnings to
   the shared docs (`CLAUDE.md`, `commands/triage.md`) when they apply
   generically.

## Repo layout

```
obsidian-tooling/
├── CLAUDE.md                   ← rules Claude follows in this repo
├── README.md                   ← you are here
├── LICENSE                     ← MIT
├── commands/                   ← Claude Code slash commands (symlinked into ~/.claude/commands/)
│   └── triage.md
├── src/obsidian_tooling/       ← Python package (typed, strict, tested)
│   ├── config.py               ← TOML loader + Pydantic VaultConfig
│   ├── setup.py                ← bootstrap logic
│   └── sweep_done.py
├── scripts/                    ← thin shims that import from src/
│   ├── setup.py
│   └── sweep-done.py
├── tests/                      ← pytest, with coverage
├── local-example/              ← committed templates
│   ├── vault-config.toml
│   ├── MY-VAULT.md
│   └── vault/                  ← skeleton vault (Inbox, Dashboard, Projects, …)
├── local/                      ← GITIGNORED — your personal workspace
│   ├── vault-config.toml       (your copy, created by setup.py)
│   ├── MY-VAULT.md             (your copy)
│   ├── vault → /your/vault/    (symlink, created by setup.py)
│   └── ...                     (scratch scripts, in-progress notes — anything yours)
├── pyproject.toml, uv.lock
└── .github/workflows/ci.yml    ← lint + typecheck + test, SHA-pinned, parallel
```

## The `local/` workspace

`local/` is yours. Gitignored as a single `/local/` rule, no whitelist
exceptions. Everything you customize for your vault lives there:

- **`local/vault-config.toml`** — mechanical config (paths, sweep sources,
  calendar tool). Scripts read it.
- **`local/MY-VAULT.md`** — prose customization (personal context,
  routing conventions, tag extensions). `/triage` reads it.
- **`local/vault`** (symlink) — points at your real vault.
- **`local/scripts/`** — one-shot personal scripts (migration tools,
  ad-hoc utilities). These get the same lint + typecheck bar as shared
  tooling.
- **`local/notes/`, `local/_inbox/`, etc.** — anything else you want.

When something in `local/` matures into reusable tooling, promote it:
- Personal script → move to `scripts/` + add tests.
- Routing pattern that any user would benefit from → PR against
  `commands/triage.md` or `CLAUDE.md`.
- Personal note → into your vault (`local/vault/`).

The committed `local-example/` mirrors the shape exactly — read it to see
what `local/` looks like after setup.

## Customizing for your vault

Two files. Both gitignored.

### `local/vault-config.toml`

```toml
[vault]
path = "./local/vault"          # the symlink does the routing
inbox = "00 Inbox.md"

[sweep]
sources = ["Next Actions.md"]   # files sweep-done.py harvests [x] from
archive_dir = "Archive"

[integrations]
# calendar_tool = "mcp__claude_ai_Google_Calendar__create_event"
```

Edit `sources` to match your vault. Common additions: a `Shopping.md` for
phone-first context lists.

### `local/MY-VAULT.md`

Where you put:

- **Personal context** — where you live, communities, ongoing projects.
- **Established routing conventions** — e.g. "Books → `Resources/Books.md`
  under `## To read`. ★ = read & recommend." `/triage` uses these as the
  default route for each category, no re-asking.
- **Tag taxonomy extensions** — custom tags beyond the generic
  `#p1`/`#p2`/`#p3`/`#next`/`#waiting`.

`/triage`'s codify-learnings step at the end of each pass will propose
additions to this file whenever a new convention emerges, so it grows
organically.

## Development

```bash
uv sync --dev                   # install everything
uv run ruff check               # lint
uv run ruff format              # format
uv run pyright                  # strict type check
uv run pytest                   # tests + coverage
uv lock --check                 # verify lockfile is current
```

All four run in parallel on every PR and push to `main` via
`.github/workflows/ci.yml`. Personal Python in `local/` is type-checked
and linted at the same bar as shared tooling — the only exclude is
`local/vault` (the symlink target).

See [CLAUDE.md](CLAUDE.md) for the full convention set (type safety
discipline, ruff rule families, import style, etc.).

## Authoring a new slash command

1. Create `commands/<name>.md` with YAML frontmatter (`description:` shows
   in the slash-command picker).
2. Body is instructions to Claude. Use `$ARGUMENTS` if the command takes
   input.
3. Re-run `uv run scripts/setup.py` (idempotent) to install the symlink
   into `~/.claude/commands/`, or symlink by hand:
   `ln -sf "$PWD/commands/<name>.md" ~/.claude/commands/<name>.md`
4. Test by running `/<name>` in a Claude Code session.

> Note: `setup.py` symlinks each `commands/*.md` individually rather than
> symlinking the whole `commands/` directory — this way `~/.claude/commands/`
> can hold commands from multiple repos (like a separate `claude-commands`
> dotfile-style repo). After a `git pull` that adds new commands, re-run
> `uv run scripts/setup.py` to register the new files; existing symlinks
> are unchanged.

Write prompts like clear instructions to a careful colleague: state the
goal, list the steps, name the verification. Vague directives let Claude
fill gaps in ways you didn't intend.

## Authoring a new script

1. Logic goes in `src/obsidian_tooling/<name>.py` with type annotations
   (pyright strict catches gaps). Module docstring explains purpose.
2. Tests at `tests/test_<name>.py`, using `tmp_path` fixtures so they
   never touch the real vault.
3. Thin shim at `scripts/<name>.py`:

   ```python
   #!/usr/bin/env python3
   import sys
   from obsidian_tooling.<name> import main
   if __name__ == "__main__":
       sys.exit(main())
   ```
4. Local check loop:

   ```bash
   uv run ruff check && uv run ruff format --check && uv run pyright && uv run pytest
   ```
5. Document the script in the "What's in the box" table above.

## License

MIT — see [LICENSE](LICENSE).
