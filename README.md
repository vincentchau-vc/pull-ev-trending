# pull-ev-trending

Remote trending feed for [PullEV](https://github.com/vincentchau-vc) (iOS blind-pull EV calculator).

## Feed

- App / CDN: https://cdn.jsdelivr.net/gh/vincentchau-vc/pull-ev-trending@main/trending.json
- Raw (may lag): https://raw.githubusercontent.com/vincentchau-vc/pull-ev-trending/main/trending.json
- Source: [SNKRDUNK hottest Pokemon singles](https://snkrdunk.com/search?keywords=Pokemon+Card+Game+%E3%83%88%E3%83%AC%E3%82%AB+%28%E3%82%B7%E3%83%B3%E3%82%B0%E3%83%AB%E3%82%AB%E3%83%BC%E3%83%89%29&searchCategoryIds=6%2F33&brandIds=pokemon&sort=hottest&page=1)

## Schema notes

- `updatedAt` — UTC ISO-8601. Bumped **only when ranked content changes**.
- App compares remote `updatedAt` to local cache and refreshes when they differ (not once-per-day).

## Refresh locally

```bash
python3 scripts/refresh_trending.py
# python3 scripts/refresh_trending.py --force   # rewrite even if unchanged
# python3 scripts/refresh_trending.py --dry-run
```

Optional overlays for apparel → TCGdex id: edit `apparel-map.json`.
