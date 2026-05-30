# 00 Dashboard

Reading-mode (⌘E) view of active work. The bands below surface every `#next`
task — the doable-now action for each project — sectioned by priority. Each
task shows its project inline via the backlink `(File > Heading)`, so there's
no per-project header clutter.

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

<!--
Optional sections you can add:

• A P3 band — copy the P2 block, swap #p2 → #p3. Worth it only if you use #p3.

• Context lists — for tasks only doable in a specific place/context (e.g.
  home or workshop maintenance). Give them their own section with a query
  like `path includes <File>` + `heading includes Tasks`, and DON'T tag them
  #next, so they stay out of the priority bands above.
-->
