# Agent notes for SNKRDUNK hottest → trending.json

When regenerating `trending.json`:

1. Prefer running the scraper:
   ```bash
   python3 scripts/refresh_trending.py
   ```
   Use `--force` only when you must bump `updatedAt` without a rank change.

2. Keep `version` at `1` unless the schema changes.

3. **Only update the file when ranked content changes.** The script already does this:
   - If the ordered `cardID` list is unchanged → leave the file alone (do not bump `updatedAt`, do not commit).
   - If ranks / cards change → rewrite `trending.json` and set `updatedAt` to current UTC ISO-8601.

4. Source of truth for ranks:
   SNKRDUNK search (Pokemon · トレカ シングル · `sort=hottest`):
   https://snkrdunk.com/search?keywords=Pokemon+Card+Game+%E3%83%88%E3%83%AC%E3%82%AB+%28%E3%82%B7%E3%83%B3%E3%82%B0%E3%83%AB%E3%82%AB%E3%83%BC%E3%83%89%29&searchCategoryIds=6%2F33&brandIds=pokemon&sort=hottest&page=1

5. Each card should include `cardID`, `nameTW`, `nameHK`, `tag` (`#1`…), `apparelId`, and `imageURL` when available.
   - Known apparel IDs map via `apparel-map.json` (and script seed) to TCGdex-style IDs.
   - Unknown cards use `snkrdunk-{apparelId}`; the app prices via `apparelId`.

6. Validate JSON before commit.

7. If content changed: **commit and push** to `main`.
   - Message example: `chore: refresh trending from SNKRDUNK hottest`
   - If unchanged: exit successfully with no commit.

8. If you cannot push after a content change, fail the run clearly.
