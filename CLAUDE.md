# Obsidian + GTD tooling — rules of engagement

This repo is the **orchestration layer** for a personal Obsidian vault used as
a GTD / PKM system. The vault itself lives outside the repo (typically synced
via Obsidian Sync, Syncthing, or any external mechanism). Claude operates on
both: tooling here, content there.

The repo ships an opinionated default vault shape + triage protocol, but the
specifics — paths, sweep sources, routing rules, personal context — are
externalized so the same shared tooling works for many users.

## Two config surfaces

Customization happens in two files inside `local/` (gitignored):

| File | Format | Contains |
|---|---|---|
| `local/vault-config.toml` | TOML | Mechanical config: vault path, inbox filename, files swept by `sweep-done.py`, archive directory, optional Calendar MCP tool name. Read by Python scripts. |
| `local/MY-VAULT.md` | Markdown | Prose layer: personal context, "established routing conventions," tag-taxonomy extensions, vault-shape notes. Read by `/triage` and any other vault-aware Claude workflow. |

The committed `local-example/` shows the shape of both. New users copy
`local-example/` into `local/` (via `scripts/setup.py` once it lands) and
edit. Existing users update `local/MY-VAULT.md` over time — the
codify-learnings step at the end of `/triage` proposes additions whenever a
new routing rule emerges.

## Repo layout

```
~/git/obsidian-tooling/
├── CLAUDE.md                   ← you are here (generic rules for Claude)
├── README.md                   ← install + quickstart for new users
├── LICENSE                     ← MIT
├── commands/                   ← Claude Code slash commands (symlink into ~/.claude/commands/)
│   └── triage.md               ← /triage — generic protocol; reads local/MY-VAULT.md
├── src/obsidian_tooling/       ← Python package (logic lives here, scripts/ are shims)
│   ├── config.py               ← TOML loader + pydantic VaultConfig
│   ├── sweep_done.py           ← harvest [x] tasks from configured sources to Archive/Done <YYYY-MM>.md
│   └── py.typed
├── scripts/                    ← runnable shims
│   └── sweep-done.py
├── tests/                      ← pytest suite (uv run pytest)
├── local-example/              ← committed template — copy into local/
│   ├── vault-config.toml
│   ├── MY-VAULT.md
│   └── vault/                  ← skeleton vault for trying the tooling
├── local/                      ← GITIGNORED — your stuff (config, vault symlink, working files)
│   ├── vault-config.toml       ← (your copy)
│   ├── MY-VAULT.md             ← (your copy)
│   └── vault → /path/to/yours  ← symlink to your real vault
├── pyproject.toml, uv.lock
└── .github/workflows/ci.yml    ← lint/typecheck/test, SHA-pinned, parallel jobs
```

Anything under `local/` is yours — config, personal notes, one-shot scripts,
in-progress migration content, scratch. The single gitignore rule is
`/local/`. When something matures into reusable tooling, promote it out:
script to `scripts/`, routing pattern to a PR against `commands/triage.md`,
doc to `README.md` or `CLAUDE.md`.

## Vault shape (defaults)

The shipping convention — your `local/MY-VAULT.md` can document deviations:

```
vault/
├── 00 Inbox.md         ← flat-bullet capture (phone, desktop, Claude all dump here)
├── 00 Dashboard.md     ← read-only surface: P1 / P2 / Everything else (all #next), Waiting
├── Projects.md         ← GTD Projects List: one ## H2 heading per active project
├── Next Actions.md     ← flat list of orphan single-action tasks
├── Someday Maybe.md    ← flat someday/maybe list
├── Projects/           ← appears once a project earns its own file
├── Areas/              ← ongoing responsibilities (running notes, accountability, etc.)
├── Resources/          ← reference material (lists, ideas, lookup info)
│   └── Notes/          ← literature/source notes — talks, sermons, books
├── Journal/            ← reflective entries
└── Archive/            ← completed / abandoned / dormant items
```

PARA-ish (Projects / Areas / Resources / Archive) plus two GTD list-files
(`Projects.md`, `Someday Maybe.md`) and two surface-files (`00 Inbox.md`,
`00 Dashboard.md`). The `00` prefix sorts surface-files to the top in the
file explorer.

### Projects-as-headings, not bold bullets

Each active project in `Projects.md` is an **`## H2 heading`** with a flat
task list below. **Not** a bold bullet with nested sub-task bullets.

Reason: the dashboard's Tasks queries show each task's **backlink**, which
renders as `(File > Heading)` — so the nearest preceding H2 heading becomes
the project label shown inline next to each task (no `[[wikilink]]`
duplication, no `#project/<slug>` clutter). The H2 also keeps the source
file readable as a flat per-project task list.

Shape:

```markdown
## Plant a Garden

Set up a small raised-bed vegetable garden by midsummer.

- [ ] pick a sunny spot in the yard #next #p1
- [ ] order seeds #p2
```

A `Projects/<Name>.md` file appears only when a project grows past ~10
tasks or accumulates reference material; then the H2 becomes the file's H1
and a `[[wikilink]]` stays behind in `Projects.md`. Same model for
`Someday Maybe.md` ↔ `Someday Maybe/<Name>.md`.

`Resources/Notes/` is the home for **literature/source notes** — notes from
external content like talks, sermons, seminars, podcasts, books. Naming
convention: `<Title> (<source/year>).md`.

### Idea hoppers

Many `Resources/<X>.md` files end up working as **perpetual idea banks** —
e.g. a reading list, a watch list, a recipes file, a "things to do in
\<city\>" file. Ideas accumulate and never get "done." When an idea earns
action, it spawns a task in `Projects.md` or `Next Actions.md` (or a
calendar event); the idea bullet itself stays in the hopper for future
reuse. List your specific hoppers in `local/MY-VAULT.md` under
"Established routing conventions" so `/triage` routes new ideas to the
right file.

## GTD workflow

**Capture → Triage → Dashboard.**

- **Capture** — anything goes into `00 Inbox.md` as a flat bullet. Phone,
  desktop, Claude. No structure required — triaged later.
- **Triage** — invoke `/triage`; the protocol lives in
  `commands/triage.md`. The command reads `local/MY-VAULT.md` for routing
  rules and personal context, and ends every pass with
  `uv run scripts/sweep-done.py`. Don't restate triage details here —
  edit them in `commands/triage.md` instead.
- **Tasks** live inside their project bullet, project file, or
  `Next Actions.md` (never in `00 Dashboard.md`). Tasks plugin queries
  them vault-wide.
- **Dashboard** (`00 Dashboard.md`) renders Tasks-plugin codeblocks in
  reading mode (⌘E). The dashboard surfaces only `#next` tasks (the
  doable-now action for each project), sectioned by priority. Queries show
  the **backlink** so each task's project renders inline as
  `(File > Heading)` — no `group by heading` header-per-project clutter —
  and use `hide toolbar` + `hide edit button` to stay clean.
  1. **🔺 P1 — do first** — `#next` + `#p1`
  2. **🔼 P2 — next up** — `#next` + `#p2`
  3. **➡️ Everything else** — `#next` with no priority tag
  4. **⏸ Waiting on** — `#waiting`

  Add a **P3** band only if you use `#p3` (otherwise those tasks fall into
  "Everything else"). **Context lists** (GTD *contexts*) are optional extra
  sections for actions gated by *where / how* you can do them rather than by
  priority — `@home`, `@errands`, `@calls`, a specific place or tool.
  Surface each via a `path`/`heading` query (when the tasks cluster in one
  file, like a place-file's `## Tasks`) or a context tag (when they're
  scattered). Context tasks are **not** tagged `#next` — the context section,
  not the priority bands, is where they live. `/triage` proposes a new
  context bucket when it notices a cluster of context-bound actions that
  would be more actionable grouped this way. There is deliberately **no
  standalone "All P1" block**:
  the P1 band already shows every `#next #p1`, so a separate `#p1` query just
  duplicates it.

### Storage vs. surfacing

Where a task is *stored* and where you *decide what to do* are separate
concerns — Obsidian lets you have both:

- **Store** tasks with their project/area (an H2 in `Projects.md`, or a
  project/area file like `Projects/Pocono House.md`), next to their
  reference material and history — what makes weekly review easy.
- **Surface** them on `00 Dashboard.md`, whose Tasks queries re-aggregate
  from wherever they live into one execution view, organized by priority
  (the bands) and context (context lists).

Paper GTD says don't file next actions by project/area — on paper, filing
is the only retrieval, so you'd never see "all my calls" at once. The query
layer removes that constraint, so **bucketing tasks into their project/area
file is good, not an anti-pattern.**

The rule that keeps it clean: **group by context with a tag or query, never
by physically moving tasks.** If a file's tasks are all one context
(everything under a place-file's `## Tasks` is "@ that place"), surface them
with a `path`/`heading` query. If the same context is scattered across
projects (e.g. calls in five files), tag them (`#@calls`) and let a query
gather them — don't yank them out of their projects. The dashboard, not the
files, is the execution view; if you're opening many files to decide what to
do, something should be surfaced on the dashboard instead.

### Tag taxonomy

- `#next` — the **single doable-now next action** for a project: its
  unblocked next physical step, *not* every task in it. When you complete
  it, move `#next` to the next step. This is the *filter* that decides what
  appears on the dashboard. Orphan single-actions in `Next Actions.md` each
  carry `#next` (each is inherently a next action).
- `#p1` / `#p2` / `#p3` — priority, the *sort within* the next-action list.
  Reserve `#p1` for genuinely hot / time-sensitive / this-week items;
  default most project lead actions to `#p2`. **If everything is `#p1`,
  nothing is.** Alphabetical = priority order, so `#p1` floats up first when
  sorting by tag.
- `#waiting` — blocked on someone else (GTD "waiting for" list).
- `#project/<slug>` — optional, for cross-cutting tasks or inbox-staged
  tasks not yet in a project file.
- Optional `📅 2026-MM-DD` only for Obsidian-only soft deadlines. **Hard
  dates go in Google Calendar**, not here.

Tag order doesn't matter. **Don't use Tasks-plugin emoji priorities**
(`🔺⏫🔼🔽⏬`) — tags do the same job and they're easier to type on phone.

Extensions and personal tags live in `local/MY-VAULT.md` under "Tag
taxonomy" — `/triage` reads both.

### Tasks-plugin syntax cheatsheet

```
- [ ] basic task
- [ ] task #next #p1                 (doable-now next action, high priority)
- [ ] task #next #p2                 (doable-now next action, medium priority)
- [ ] task #waiting                  (blocked on someone)
- [ ] task 📅 2026-05-20             (optional Obsidian-only soft due date)
- [ ] task 🔁 every week             (recurring)
- [x] task ✅ 2026-05-14             (Tasks plugin adds ✅ + date when checked)
```

### Done handling — what gets swept, what stays

Two-track rule:

- **`[x]` items in files listed in `[sweep].sources`** (in
  `local/vault-config.toml`) get harvested by `scripts/sweep-done.py` into
  `vault/Archive/Done <YYYY-MM>.md`, under a `## From: <source>` header per
  source. These are "context-list" files — orphan items with no surrounding
  context worth preserving in-place (e.g. `Next Actions.md`, `Shopping.md`).
- **`[x]` items in project files / area files / anywhere else** stay in
  place. They're part of that project's history (what was done, in what
  order, what informed the remaining work). The sweep never touches them.
- **Whole-project archival** stays manual: when a project finishes, move
  the project file (or its bullet) to `Archive/`. There's no auto-archival
  for projects.

The `/triage` command runs the sweep at the end of every triage pass — no
separate invocation needed in normal use. Run it manually with
`uv run scripts/sweep-done.py --dry-run` first to preview, then again
without the flag to apply.

## Slash commands

Custom Claude Code slash commands live in `commands/`. Each `.md` file
becomes a `/<name>` command once symlinked into `~/.claude/commands/`. See
`README.md` for the install loop. Current commands:

- `/triage` — inbox triage protocol (proposes destinations, batches obvious
  items, asks on ambiguous ones, ends with `sweep-done.py`). Reads
  `local/MY-VAULT.md` for routing rules and personal context.

## Plugin policy

**Expected community plugins:** `obsidian-tasks-plugin`, `dataview`. Both
are community plugins (not Obsidian core) — install from the Community
Plugins browser inside Obsidian before the dashboard and sweep workflow
will do anything useful. Other plugins are a per-user decision — document
any you install in `local/MY-VAULT.md` so Claude knows what's available.

- **Tasks** (`obsidian-tasks-plugin`) parses `- [ ] task #tag` lines into a
  task system: priority/next/waiting via tags, optional soft due dates
  (`📅 YYYY-MM-DD`), recurrence (`🔁 every week`), and an auto-stamped
  completion date (`✅ YYYY-MM-DD`) when a task is checked. The `00
  Dashboard.md` queries are Tasks codeblocks that show each task's backlink,
  which renders `(File > Heading)` inline so you see each task's project
  without per-task tags or wikilinks.
- **Dataview** is useful for "query bullets by tag/property within a single
  reference file" needs.
- **No daily notes** by default. Don't create a daily-notes file or
  recommend the daily-notes core plugin unless the user opts in.
- **Hard dates go in Google Calendar**, not Obsidian. If a Calendar MCP is
  configured (`[integrations].calendar_tool` in `vault-config.toml`),
  `/triage` will offer to create events for date-bound items.

## Rules for Claude in this repo

- **Never delete vault notes without asking.** Stale ≠ junk.
- **Search the vault before creating** a new note — avoid duplicates. The
  vault symlink is at `local/vault/`; you can `grep -r` or use `Read`/`Glob`.
- **Don't touch `.obsidian/workspace.json`** in normal operation — per-device
  UI state. (One-time resets during structural cleanups are fine.)
- **Internal links use `[[Note Name]]`** (Obsidian wikilink convention).
- **Keep vault files free of HTML usage-comments.** The conventions live
  here and in `local/MY-VAULT.md` — don't scatter `<!-- how to use this
  file -->` hints across the inbox, list files, or project files. They only
  show in edit mode, drift stale, and duplicate this doc. Don't add them
  during setup or triage; a visible one-line prose intro is fine where a file
  genuinely needs orienting.
- **Triage default**: H2 heading in `Projects.md` (multi-step), bullet in
  `Next Actions.md` (single action), or bullet in `Someday Maybe.md` — not
  a new file. Promote to its own file only when the project earns it.
- **When in doubt during triage, ask** — don't guess the destination.
  Reference content always gets a destination confirmation.
- **When promoting an item or creating a new file**, propose the
  destination + filename first; let the user confirm before moving.
- **Read `local/MY-VAULT.md`** at the start of any vault-aware task. It is
  the user-specific overlay on top of the generic rules in this file.

## Python Toolchain

- Python 3.14 (pinned via `requires-python = "==3.14.*"` in
  `pyproject.toml`; `uv` installs the latest 3.14.x automatically).
- `uv` for env + dependencies. Lockfile (`uv.lock`) is committed. **`uv`
  is the only prerequisite** for running the tooling — it provisions
  Python, the virtualenv, and all deps.
- `src/` layout with `hatchling` build backend.
- Runtime deps in `[project.dependencies]`, dev tools in
  `[dependency-groups].dev`.

Common commands (run from repo root):
- `uv sync --dev` — install everything
- `uv run pyright` — type check
- `uv run ruff check` / `uv run ruff format` — lint and format
- `uv run pytest` — tests with coverage
- `uv lock --check` — verify lockfile is current

## Type Safety

- **Pyright strict mode** (`typeCheckingMode = "strict"`). Zero errors
  required.
- **Pydantic at I/O boundaries** — config, external API responses, anything
  crossing a process or network boundary. Internal helpers can use
  `TypedDict`, dataclass, or plain dict where it fits.
- **`py.typed` marker** ships with the package so consumers honor types.
- **`__all__` on modules with a public API.** Declares what's exported and
  stops `json`/`httplib2`/etc. from showing up as auto-import candidates.
  Internal-only modules and tests don't need it.
- `# type: ignore[<specific-rule>]` only at third-party boundaries with
  missing stubs. Never blanket-ignore.

## Linting & Formatting

- **Ruff** handles linting, formatting, and import sorting
  (`[tool.ruff]` in `pyproject.toml`).
- Active rule families: pycodestyle, pyflakes, isort, pyupgrade, bugbear,
  simplify, comprehensions, bandit (security), and ruff's own rules. Tests
  get `S101` (asserts) waived.
- VS Code is configured to run `ruff format` on save and apply auto-fixes
  + organize imports.
- CI fails on `ruff check` errors or unformatted files.
- `# noqa: <specific-rule>` only at narrow, justified spots — same
  discipline as `# type: ignore[<rule>]`. No blanket ignores.

## Imports

- **Import from the defining module, not from re-exports.** If `pkg.foo`
  defines `Bar`, write `from pkg.foo import Bar` — not `from pkg import Bar`,
  even if `pkg/__init__.py` re-exports it.
  - Makes inter-module dependencies explicit and grep-able for refactors.
  - Avoids circular-import traps that re-exports can hide.
  - Pairs with `python.analysis.importFormat = "absolute"` in
    `.vscode/settings.json`.
- This applies to *first-party* code. Third-party packages with curated
  public APIs (e.g. `from pydantic import BaseModel`) follow their
  documented import path.

## Testing

- `uv run pytest` runs the suite with coverage enabled (`--cov` configured
  in `pyproject.toml`).
- Branch coverage is on. Lines like `if TYPE_CHECKING:` and
  `raise NotImplementedError` are excluded from the report.
- New behavior should land with tests covering it.

## CI

GitHub Actions runs three jobs in parallel on every PR and push to main:
`lint` (ruff), `typecheck` (pyright), and `test` (pytest with coverage).
All must pass to merge. The uv cache is enabled so reruns are fast.

## Supply Chain Security

- **Pin GitHub Actions by SHA, not tag.** Tags are mutable; SHAs are not.
  Format: `uses: actions/checkout@<40-char-sha> # v4.3.1`
- **Dependabot** opens weekly PRs for both GitHub Actions and Python deps.
  Minor/patch Python updates are grouped into a single PR; majors come
  individually.
- Never use `@main`, `@master`, or `@latest`.

## Editor

`.vscode/settings.json` is committed:
- Pylance strict type checking (matches CI)
- `python.analysis.importFormat = "absolute"` — imports resolve to the
  source module, not re-exports
- Ruff as default formatter, format-on-save, fix-all and organize-imports
  on save

## Code Style

- Comment only when the *why* is non-obvious (a hidden constraint, a
  workaround, surprising behavior). Default to no comments — well-named
  identifiers do the work.
- Ruff handles formatting and import sorting — don't hand-format.
