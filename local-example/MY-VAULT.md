# My Vault

> This file is your personal layer on top of the generic tooling. The `/triage`
> slash command loads it as the source of truth for routing rules and personal
> context. Edit freely — the copy at `local/MY-VAULT.md` is gitignored.
>
> Conventions:
> - **Personal context** — anything Claude should know about you to route
>   inbox items well (where you live, ongoing commitments, communities, etc.).
> - **Established routing conventions** — rules for where specific categories
>   of inbox items go. Add as you go; `/triage` can also propose additions
>   during the codify-learnings step at the end of each pass.
> - **Tag taxonomy** — custom tags you use that extend the generic defaults
>   (`#p1`/`#p2`/`#p3`, `#next`, `#waiting`, `#project/<slug>`).
>
> Example content for each section is in HTML comments below — they show in
> your editor but `/triage` ignores them. Replace each commented block with
> your own real content as you go.

## Personal context

<!--
A few sentences about you — geographic context, communities, ongoing
commitments, anything that helps Claude make better routing decisions.

Examples (delete and replace with your own):

- Based in <city>.
- Active community: <name> (weekly meetup, accountability group).
- Major ongoing project lives at `Projects/<name>.md`.
-->

## Established routing conventions

<!--
Rules for where specific kinds of inbox items go. Treat these as the default
route — `/triage` will use them without re-asking. You can still confirm
*within* the file (e.g. which H2 section).

Example shape (delete and replace with your own):

- **Shopping items** (groceries, household consumables) → `vault/Shopping.md`,
  under `## Groceries` (food) or `## Home` (household). Items can be deleted
  as bought or `[x]`-ed; `sweep-done.py` harvests checked items into the
  monthly archive.
- **Books / reading material** → `vault/Resources/Books.md`, under `## To read`.
  `★` prefix = read and recommend.
- **Films / TV** → `vault/Resources/Films & TV.md`. Films under `## To watch`;
  TV under `## TV`. Parenthesize the source of the rec.
- **Recipes** → `vault/Resources/Recipes.md`, grouped by cooking method
  (`## Instant Pot`, `## Stovetop / oven`, etc.). If a recipe has a URL, list
  the title + URL — don't duplicate the ingredient list.
- **People** (someone's name) → `vault/Resources/People.md` (or split by
  geography if it helps you).

Add more as your vault grows. The point of this file is to keep
`commands/triage.md` generic and your specific routing rules in one
editable place.
-->

## Tag taxonomy (overrides/extends the defaults)

<!--
Custom tags you use that aren't in the generic taxonomy.

Examples (delete and replace with your own):

- `#someday/<bucket>` — optional sub-bucketing of someday-maybe items.
- `#waiting/<who>` — extend `#waiting` with the person blocking the task.
-->
