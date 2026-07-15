# Agent notes for daily trending refresh

When regenerating `trending.json`:

1. Keep `version` at `1` unless schema changes.
2. **Always** set `updatedAt` to the current UTC time in ISO-8601 (e.g. `2026-07-15T04:30:00Z`), even if the card list is unchanged.
3. Prefer Japanese/blind-pull relevant hits: recent SV sets, 151, classic alts still common in pools.
4. Every `cardID` must be a valid TCGdex-style id the PullEV app already understands.
5. Do **not** scrape SNKRDUNK HTML. Use public knowledge, existing list evolution, and obvious new-set chase cards only.
6. Keep roughly 10–25 cards total across a few groups; drop stale fillers when adding newer hits.
7. Validate JSON before commit.
8. **Always commit and push** `trending.json` to `main` after updating `updatedAt`.
   - Message example: `chore: refresh trending.json`
   - Do **not** skip the commit just because the card list looks the same.
9. If you cannot push, fail the run clearly (do not report success).
