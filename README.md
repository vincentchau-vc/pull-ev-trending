# pull-ev-trending

Remote trending feed for PullEV.

## Feed

- Raw: https://raw.githubusercontent.com/vincentchau-vc/pull-ev-trending/main/trending.json
- Groups (pick one in app):
  - **Pokémon** — SNKRDUNK singles · hottest
  - **One Piece** — SNKRDUNK singles · popular
- Display names are English

## Schema notes

- `updatedAt` — UTC ISO-8601. Bumped **only when ranked content changes**.
- App compares remote `updatedAt` to local cache and refreshes when they differ.

## Refresh locally

```bash
python3 scripts/refresh_trending.py
```
