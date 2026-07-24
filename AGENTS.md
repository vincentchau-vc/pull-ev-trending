# Agent notes for SNKRDUNK trending → trending.json

When regenerating `trending.json`:

1. Prefer running the scraper:
   ```bash
   python3 scripts/refresh_trending.py --commit-push
   ```
   Use `--force` only when you must bump `updatedAt` without a rank change.
   Omit `--commit-push` only for local dry experiments (`--dry-run`).

2. Keep `version` at `1` unless the schema changes.

3. **Only update the file when ranked content changes.** The script already does this:
   - If ordered `cardID` lists are unchanged → leave the file alone (do not bump `updatedAt`, do not commit).
   - If ranks / cards change → rewrite `trending.json` and set `updatedAt` to current UTC ISO-8601.

4. Build **two separate groups** (app shows one brand at a time; user picks):
   - `snkrdunk-pokemon` — Pokémon singles · `sort=hottest`
   - `snkrdunk-onepiece` — One Piece singles · `sort=popular`
   Titles / subtitles / card display names must be **English**.
   Each group targets **300** cards (paginate SNKRDUNK search pages until filled or exhausted).

5. Each card should include `cardID`, `nameTW`, `nameHK` (both EN short names), `tag` (`#1`…), `apparelId`, and `imageURL` when available.
   - Known apparel IDs map via `apparel-map.json` (and script seed) to TCGdex-style IDs (Pokémon).
   - Unknown cards use `snkrdunk-{apparelId}`; the app prices via `apparelId`.

6. Validate JSON before commit.

7. If content changed: **commit AND push** to `main` (required — commit-only leaves `raw.githubusercontent.com` stale).
   - Prefer: `python3 scripts/refresh_trending.py --commit-push`
   - Message example: `chore: refresh trending from SNKRDUNK`
   - If unchanged: exit successfully with no commit.

8. If you cannot push after a content change, fail the run clearly.
