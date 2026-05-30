# 00 Dashboard

Reading-mode (⌘E) view of active work. The bands below surface every `#next`
task — the doable-now action for each project — sectioned by priority. Each
task shows its project inline via the backlink `(File > Heading)`, so there's
no per-project header clutter. Optional P3 and context-list sections are
described in `CLAUDE.md`.

## 🔺 P1 — do first

```tasks
not done
tags include #next
tags include #p1
sort by description
hide edit button
hide toolbar
```

## 🔼 P2 — next up

```tasks
not done
tags include #next
tags include #p2
sort by description
hide edit button
hide toolbar
```

## ➡️ Everything else

```tasks
not done
tags include #next
tags do not include #p1
tags do not include #p2
tags do not include #p3
sort by description
hide edit button
hide toolbar
```

## ⏸ Waiting on

```tasks
not done
tags include #waiting
sort by description
hide edit button
hide toolbar
```