# pull-ev-trending

Remote trending feed for PullEV.

## Feed

- Raw: https://raw.githubusercontent.com/vincentchau-vc/pull-ev-trending/main/trending.json
- Groups (pick one in app):
  - **Pokémon** — SNKRDUNK singles · hottest
  - **One Piece** — SNKRDUNK singles · popular
- ~**300** cards per brand (app shows 30 per page by slicing this JSON)
- Display names are English

## Schema notes

- `updatedAt` — UTC ISO-8601. Bumped **only when ranked content changes**.
- App compares remote `updatedAt` to local cache and refreshes when they differ.

## Refresh locally

```bash
# Scrape + write trending.json only
python3 scripts/refresh_trending.py

# Daily automation: scrape, commit, and push so raw.githubusercontent.com updates
python3 scripts/refresh_trending.py --commit-push
```
