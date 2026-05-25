---
description: Triage the Obsidian vault inbox. Proposes a destination + tags for each item; batches obvious ones, pauses on ambiguous ones. Ends with a sweep-done sweep.
---

Triage the Obsidian vault's `00 Inbox.md`. Move each captured item to its
right home, surface ambiguous items for confirmation, and end with a
`sweep-done` sweep so completed items in the configured sweep sources get
archived in the same pass.

**Target vault:** resolved from `local/vault-config.toml`'s `[vault].path`
(typically `./local/vault`, which is a symlink to the user's real vault).
If `$ARGUMENTS` is a path, use that instead. If neither resolves, stop and
tell the user — don't guess. The full project conventions live in
`CLAUDE.md`; read it before triaging.

## Step 0 — Load the personal overlay

**Read `local/MY-VAULT.md` if it exists** before classifying anything. That
file is the user-specific overlay on top of this generic protocol — it
contains personal context, "established routing conventions," tag-taxonomy
extensions, and vault-shape notes. Treat its routing rules as the default
route (no need to re-ask which file each category belongs to). If
`local/MY-VAULT.md` doesn't exist, fall back to the generic destinations in
Step 2 and ask the user where each item should go.

Also read `local/vault-config.toml`:
- `[sweep].sources` — the files that Step 7 will sweep.
- `[integrations].calendar_tool` — the MCP tool name for calendar events.
  If empty or unset, **skip the Calendar branch entirely** (don't offer it
  as a destination option).

## Step 1 — Read the inbox

Read `vault/00 Inbox.md`. Distinguish the template/header block (HTML
comment at the top, plus the `# 00 Inbox` heading) from the captured items
below it. The template is sacred — never reformat it; only triage items
out of the section beneath it.

If the inbox is empty (no items below the template), skip ahead to Step 7
(`sweep-done.py`) and report that there was nothing to triage.

**Pre-pass: archive already-checked items.** Before classifying anything,
scan the captured items for `- [x] …` lines. These are tasks the user
finished pre-triage — they don't need a destination, they need to be filed.
Append them to `vault/Archive/Done <YYYY-MM>.md` under a
`## From: 00 Inbox.md` header (same convention as `sweep-done.py`'s
`## From: Next Actions.md` block), then remove them from `00 Inbox.md`.
Preserve the inbox template verbatim. Surface the count in the final
report.

## Step 1.5 — Discover current vault structure

Before proposing destinations, discover the current vault state so
proposals match what's actually there rather than any stale baked-in list:

```bash
find vault -maxdepth 3 -type f -name "*.md" -not -path "*/Archive/*" -not -path "*/.obsidian/*" | sort
```

If `local/MY-VAULT.md` names specific reference files (e.g. a people-roster
file with event tags), also discover the file's currently-used tags:

```bash
grep -ohE '#[a-z][a-z/-]*' "vault/<that file>" | sort -u
```

Use these as the source of truth for destinations and tag choices. If the
user picks a new tag value or proposes a new destination, that's fine — it
becomes part of the vault going forward. **Do not** rely on a hardcoded
list of files or tags; always re-discover at the start of each triage
pass.

## Step 1.6 — Archive done projects (pre-pass)

Scan `Projects.md`'s H2 headings and every file under `Projects/` for
project headings (or whole project files) that are clearly finished, and
surface them as a batched archive proposal before triaging inbox items.

### Scan scope

For each H2 heading in `Projects.md` and each file under `Projects/`,
collect:

- The list of `- [x]` completed tasks beneath it (with `✅ YYYY-MM-DD`
  completion stamps where present).
- The list of `- [ ]` incomplete tasks beneath it.
- Any date-like text in the heading or its first paragraph.

### Candidate criteria (all must hold)

1. The heading has at least one `- [x]` task underneath.
2. The heading has zero `- [ ]` unchecked tasks underneath.
3. At least one of:
   - **A date in the heading or body has passed.** Recognize common
     patterns: ISO `YYYY-MM-DD`, `<Month> <DD>` or `<Month> <DD>–<DD>`,
     named holidays with year (`Memorial Day Weekend YYYY`,
     `Labor Day YYYY`, `Christmas YYYY`, etc.), seasonal markers
     (`(Summer YYYY)`, `(Fall YYYY)`, `Q3 YYYY`).
   - **All `✅ YYYY-MM-DD` completion stamps are more than 4 weeks old**
     (and no more recent activity in the heading body).
   - **Explicit done marker**: `(done)`, `(archived)`, `status: done` in
     frontmatter, or similar.

If *every* H2 heading in a file passes the candidate check, suggest
archiving the **whole file** rather than each heading individually.

### Surface to user (batched)

Collect all candidates from the scan into **one batched
`AskUserQuestion`** listing every candidate. For each, offer three
actions:

- **Archive** — move to the candidate's destination (see below).
- **Skip** — leave in place; don't ask again this pass.
- **Defer** — leave in place; surface again on the next triage pass.

If the scan finds no candidates, skip silently to Step 2.

### Destinations

Default destination: append to `vault/<archive_dir>/Done <YYYY-MM>.md`
under a `## From: <source-file> — <heading>` block (mirrors the
`sweep-done.py` convention, with `— <heading>` appended).

If `local/MY-VAULT.md` has a "Project archival" section, apply any
matching per-vault destination overrides before presenting the batched
prompt — show the actual destination each candidate will land at in the
prompt so the user can sanity-check it.

### Execute on approval

For each "Archive":

- **Heading-level**: cut the heading and everything under it up to the
  next `## ` or EOF, append to the destination under the
  `## From: <source-file> — <heading>` block, then remove from the
  source file.
- **File-level**: move `Projects/<name>.md` to the destination
  (`Archive/<name>.md` or as per-vault overrides specify). If a
  `[[wikilink]]` to it exists in `Projects.md` or `00 Dashboard.md`,
  leave the link alone — broken wikilinks are easy to clean up later
  and harder to re-establish if accidentally removed.

Surface the per-candidate result in Step 8's final report.

## Step 2 — Classify each item

For each captured item, propose:

### Destination — one of:

- **Task under an existing `## Heading` in `Projects.md`** — when the item
  is clearly an action belonging to a project already listed there. Append
  it as a flat `- [ ] …` line directly under the project's heading. **Don't
  use nested bullets** — every active task in `Projects.md` is a top-level
  bullet under its project's H2 so that Tasks-plugin's `group by heading`
  picks up the project name as the group label.
- **New `## Heading` project in `Projects.md`** — when the item is a
  multi-step outcome that isn't represented yet. Add the project as an
  `## H2 heading`, optionally followed by a one-line description, then the
  initial task list below it. Not a bold bullet — headings are what
  `group by heading` reads.
- **New bullet in `Next Actions.md`** — when the item is a single,
  standalone action with no multi-step structure (e.g. "renew passport",
  "call mom about grandma's birthday").
- **`Areas/<X>.md`** — when the item belongs to an ongoing area of
  responsibility (recurring social structures, accountability, community
  group notes, etc.).
- **`Resources/<X>.md`** — when the item is reference material (lookup
  info, lists, ideas, reading material). If `local/MY-VAULT.md` has an
  established routing convention for this category, use it.
- **Source note** (sermon, talk, seminar, book, podcast) →
  `Resources/Notes/<Title> (<source/year>).md`. Confirm the filename with
  the user before creating.
- **`Someday Maybe.md` bullet** — when the item is a non-committed idea.
- **New `Someday Maybe/<X>.md` file** — only for heavyweight someday items
  that earn their own file. Don't promote casually.
- **Calendar event** — *only if* `[integrations].calendar_tool` is
  configured in `local/vault-config.toml`. Use that MCP tool. See "Calendar
  reminders" below.
- **Drop** — when the item isn't worth keeping (stale, no longer relevant,
  etc.). Surface it; don't drop silently.

### Established routing conventions

User-specific routing rules live in `local/MY-VAULT.md` under "Established
routing conventions" — categories with a known default destination (e.g.
"Books → `Resources/Books.md` under `## To read`"). Treat those as the
default route, no need to re-ask which file the category belongs to.
You may still ask about destination *within* the file if it's ambiguous —
e.g. which H2 section, which city heading.

If a category doesn't appear there, treat it as a fresh decision: propose
a destination and ask via `AskUserQuestion`. After the user picks, propose
codifying the rule in `local/MY-VAULT.md` (Step 7.5).

### Shape:

- Task (`- [ ]`) — actionable, has a "done" state
- Reference content (no checkbox) — passive information

### Tags (for tasks only):

Use the generic taxonomy from `CLAUDE.md` > Tag taxonomy
(`#p1`/`#p2`/`#p3`, `#next`, `#waiting`, `#project/<slug>`), plus any
extensions defined in `local/MY-VAULT.md` > "Tag taxonomy" — apply those
when the user's rules match.

Hard dates go to the calendar (if configured), not the vault. Don't add
`📅 YYYY-MM-DD` unless the user specifically asks for a soft
Obsidian-only date.

## Step 3 — Batching and confirmation policy

Different item categories get different confirmation treatment:

- **Action items with an unambiguous destination + shape** (e.g. a clear
  bullet that obviously belongs to an existing project, or a clear single
  action that obviously goes to `Next Actions.md`): batch them. Show the
  full proposed plan (destination + tags per item) in one message and ask
  for blanket approval.

- **Action items with ambiguous destinations** (e.g. project bullet vs.
  someday-maybe; new project vs. extending an existing one): use
  `AskUserQuestion` with the candidate destinations as options. Don't
  guess.

- **Reference content** (no action implied — recipes, ideas, lists,
  articles): **always confirm the destination via `AskUserQuestion`**,
  even if the destination seems obvious. Reference material accretes
  silently in the wrong file and the cost of asking is low. Options should
  include: a specific existing `Resources/<X>.md`, a specific existing
  `Areas/<X>.md`, "create new file `<proposed-name>.md`", or "drop".

- **Calendar candidates** (anything with a hard date or implied time):
  confirm date, time, title, location/notes, and reminders (see below)
  before creating the event. Skip this whole branch if no calendar tool is
  configured.

## Step 4 — Calendar reminders

(Skip this step entirely if `[integrations].calendar_tool` is unset in
`local/vault-config.toml`.)

When creating events via the configured calendar MCP tool, every event
gets a base set of two reminders, plus one extra tier based on the start
time-of-day so the user sees it the evening prior or earlier in the day:

| Event start time | Reminders (minutes before) | Why |
|---|---|---|
| Morning (< 12:00) | 30, 180, **660** (≈11 h) | The 11 h reminder lands the evening before, so the user sees it before bed. |
| Afternoon (12:00–16:59) | 30, 180 | The 3 h reminder already lands earlier the same day; no extra tier needed. |
| Evening (≥ 17:00) | 30, 180, **360** (6 h) | The 6 h reminder lands midday — well before evening commitments. |

If the event is all-day or the user only gave a date with no time, ask
which tier to apply before creating. Don't default silently.

## Step 5 — Execute on approval

For each approved item:

1. Append it to its destination file. Don't reformat the destination —
   append at the end, or under the most relevant existing header.
2. Remove it from `00 Inbox.md`. Preserve the inbox template/header
   verbatim.
3. Never delete vault files. Never reformat reference docs you're
   appending to.

If a new in-flight project emerges from triage, add a `[[wikilink]]` to
the in-flight list in `00 Dashboard.md` (under "🔥 In-flight projects").
Curate; don't append blindly.

## Step 6 — Open questions or deferred items

Items that couldn't be classified or that the user deferred stay in
`00 Inbox.md` with a brief inline note (one line, italicized) explaining
why they were left. The user can revisit on the next triage pass.

## Step 7 — Run `sweep-done.py`

After the inbox is processed, run the sweep at the repo root:

```bash
uv run scripts/sweep-done.py
```

Surface the script's summary output. This harvests any `- [x]` items from
the sweep sources configured in `local/vault-config.toml`'s
`[sweep].sources` into `vault/Archive/Done <YYYY-MM>.md`, one
`## From: <source>` block per source. Project files, areas, and resources
are not touched.

## Step 7.5 — Codify learnings

After sweep-done and before the final report, scan this pass for any
**policy / convention** decisions that aren't already documented.

- **Generic conventions** (a clarification of the protocol itself, a new
  shape rule, a new generalizable behavior) → propose an edit to
  `commands/triage.md`.
- **Vault-specific routing or personal conventions** (a new category → file
  mapping, a new tag, a new section convention) → propose an edit to
  `local/MY-VAULT.md`.

The goal is to convert one-time decisions into reusable rules so the next
pass doesn't re-litigate them.

**Qualifying examples — codify these:**

- A new routing rule ("X category → Y file under Z section") → MY-VAULT.md.
- A new convention the user established (a new tag, a section convention,
  a naming pattern, a special-case handling) → MY-VAULT.md.
- A clarification or extension of an existing routing rule (edge case not
  covered) → MY-VAULT.md.
- A new destination file or category not previously in the vault → add to
  "Established routing conventions" in MY-VAULT.md.
- A generalizable protocol change (something every user would want) →
  `commands/triage.md`.

**NOT qualifying — skip these:**

- One-off classification decisions (alphabetic placement, "this particular
  item goes here").
- Specific file names or tag values already discovered by Step 1.5.
- Ephemeral context for this triage session only.

Surface as **explicit proposed edits** — the user approves like any other
edit. Over time `local/MY-VAULT.md` becomes a lived-in policy document
rather than static instructions.

If there's nothing to codify, say "nothing new to codify this pass" in the
final report. Don't force it.

## Step 8 — Final report

End the session with a summary:

- N items triaged (with destinations)
- M items deferred (with reasons)
- K calendar events created (omit if calendar disabled)
- I `[x]` items archived from `00 Inbox.md` (pre-pass)
- L headings/files archived from project files (Step 1.6), or "no
  archive candidates this pass"
- J `[x]` items swept from sweep sources
- P codified learnings (with the rule(s) added, and where), or "nothing
  new to codify this pass"
- Files touched (list)

Don't commit. The user commits explicitly when they're ready.

---

## Rules of thumb

- **Default to in-place additions, not new files.** Promote to a file only
  when a project hits ~10 tasks or accumulates real reference material.
  (`Projects.md` projects are H2 headings, not files.)
- **The inbox is sacred capture.** Never reformat it; only triage out of
  it. `[x]` lines in the inbox are archived in a pre-pass, not classified.
- **Hard dates go to the configured calendar** (if any), with the
  tiered-reminder policy. If no calendar is configured, treat date-bound
  items the same as any other action.
- **Reference content always gets a destination confirmation** — never
  auto-route.
- **Always end a triage pass by running `sweep-done.py`.**
- **`local/MY-VAULT.md` is a lived-in policy document.** When the user
  establishes a new convention mid-pass, codify it there in Step 7.5 so
  the next pass starts smarter.
- **When in doubt, ask.**
