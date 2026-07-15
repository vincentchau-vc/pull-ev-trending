# Agent notes for daily trending refresh

When regenerating `trending.json`:

1. Keep `version` at `1` unless schema changes.
2. Set `updatedAt` to current UTC ISO-8601.
3. Prefer Japanese/blind-pull relevant hits: recent SV sets, 151, classic alts still common in pools.
4. Every `cardID` must be a valid TCGdex-style id the PullEV app already understands.
5. Do **not** scrape SNKRDUNK HTML. Use public knowledge, existing list evolution, and obvious new-set chase cards only.
6. Keep roughly 10–25 cards total across a few groups; drop stale fillers when adding newer hits.
7. Validate JSON before commit. Commit only `trending.json` (and README if needed) with message like `chore: refresh trending.json`.
8. Push to `main`.
