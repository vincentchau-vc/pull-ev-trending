# Pull EV Trending Cards

Public feed of curated Pokémon TCG blind-pull hit cards for the **PullEV** iOS app.

## App URL

```
https://raw.githubusercontent.com/vincentchau-vc/pull-ev-trending/main/trending.json
```

## Schema

- `version` — integer schema version
- `updatedAt` — ISO-8601 UTC timestamp of last regeneration
- `groups[]` — pack groups with `id`, `title`, `subtitle`, `cards[]`
- `cards[]` — `cardID` (TCGdex), `nameTW`, `nameHK`, optional `tag`

## Notes

- This is a **curated / regenerated daily** list for convenience, not a scraped SNKRDUNK live ranking.
- Automation runs around **06:00 Asia/Hong_Kong**.
