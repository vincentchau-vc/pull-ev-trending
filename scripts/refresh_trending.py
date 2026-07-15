#!/usr/bin/env python3
"""Scrape SNKRDUNK popular singles (Pokémon + One Piece) → trending.json.

Only rewrites the file (and bumps updatedAt) when the ranked card lists change.
Card display names are English. App lets the user pick one brand at a time.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "trending.json"
MAP_PATH = ROOT / "apparel-map.json"

FEEDS = [
    {
        "id": "pokemon",
        "title": "Pokémon",
        "subtitle": "Trading card singles · hottest",
        "params": {
            "keywords": "Pokemon Card Game トレカ (シングルカード)",
            "searchCategoryIds": "6/33",
            "brandIds": "pokemon",
            "sort": "hottest",
            "page": "1",
        },
    },
    {
        "id": "onepiece",
        "title": "One Piece",
        "subtitle": "Trading card singles · popular",
        "params": {
            "keywords": "ONE PIECE トレカ (シングルカード)",
            "searchCategoryIds": "6/33",
            "brandIds": "onepiece",
            "sort": "popular",
            "page": "1",
        },
    },
]

UA = {"User-Agent": "PullEV-trending-refresh/1.0 (+https://github.com/vincentchau-vc/pull-ev-trending)"}

# Seed: SNKRDUNK apparelId → TCGdex-style cardID (Pokémon only, from PullEV registry).
SEED_APPAREL_MAP = {
    408333: "sv08-219",
    418755: "sv08-238",
    395191: "sv08-057",
    408331: "sv08-203",
    413158: "sv08-223",
    128117: "sv03.5-199",
    127773: "sv03.5-006",
    128121: "sv03.5-205",
    128053: "sv03.5-151",
    162095: "sv04.5-349",
    722239: "mep-023",
    146897: "svp-085",
    93021: "swsh7-215",
    96559: "swsh11-212",
    96618: "swsh7-65",
    502958: "sv09-053",
    502961: "sv09-056",
}


def http_get(url: str, timeout: float = 30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def search_url(params: dict) -> str:
    return "https://snkrdunk.com/search?" + urllib.parse.urlencode(params)


def load_apparel_map() -> dict[int, str]:
    mapping = dict(SEED_APPAREL_MAP)
    if MAP_PATH.exists():
        data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        for key, value in data.items():
            try:
                mapping[int(key)] = str(value)
            except (TypeError, ValueError):
                continue
    return mapping


def scrape_search(url: str, limit: int = 30) -> list[tuple[int, str]]:
    raw = http_get(url).decode("utf-8", "ignore")
    names = [
        html_lib.unescape(n.strip())
        for n in re.findall(r'productName[^"]*"[^>]*>\s*([^<]+)\s*<', raw)
    ]
    ids: list[int] = []
    seen: set[int] = set()
    for match in re.findall(r"/apparels/(\d+)", raw):
        aid = int(match)
        if aid not in seen:
            seen.add(aid)
            ids.append(aid)

    pairs = list(zip(ids, names))[:limit]
    if len(pairs) < 5:
        raise RuntimeError(f"scrape returned too few items ({len(pairs)}) for {url}")
    return pairs


def fetch_apparel(apparel_id: int) -> dict:
    data = json.loads(http_get(f"https://snkrdunk.com/v1/apparels/{apparel_id}"))
    media = data.get("primaryMedia") or {}
    return {
        "nameEN": data.get("name") or "",
        "localizedName": data.get("localizedName") or "",
        "imageURL": media.get("imageUrl"),
        "productNumber": data.get("productNumber"),
    }


def resolve_card_id(apparel_id: int, apparel_map: dict[int, str]) -> str:
    if apparel_id in apparel_map:
        return apparel_map[apparel_id]
    return f"snkrdunk-{apparel_id}"


def short_english_name(en_name: str, fallback_jp: str) -> str:
    source = (en_name or fallback_jp or "").strip()
    source = re.sub(r"\s+", " ", source)
    m = re.match(r"^(.+?)\s*[\[（(]", source)
    if m:
        return m.group(1).strip()
    return source


def content_fingerprint(groups: list[dict]) -> list[list[str]]:
    return [[c.get("cardID", "") for c in g.get("cards", [])] for g in groups]


def build_group(feed: dict, apparel_map: dict[int, str], limit: int = 30) -> dict:
    url = search_url(feed["params"])
    pairs = scrape_search(url, limit=limit)
    cards: list[dict] = []
    for rank, (apparel_id, page_name) in enumerate(pairs, start=1):
        detail = fetch_apparel(apparel_id)
        en = short_english_name(detail["nameEN"], detail["localizedName"] or page_name)
        card_id = resolve_card_id(apparel_id, apparel_map)
        card = {
            "cardID": card_id,
            "nameTW": en,
            "nameHK": en,
            "tag": f"#{rank}",
            "apparelId": apparel_id,
        }
        if detail.get("imageURL"):
            card["imageURL"] = detail["imageURL"]
        cards.append(card)
        time.sleep(0.12)
    return {
        "id": f"snkrdunk-{feed['id']}",
        "title": feed["title"],
        "subtitle": feed["subtitle"],
        "cards": cards,
    }


def build_payload(force: bool = False) -> tuple[dict, bool]:
    apparel_map = load_apparel_map()
    groups = [build_group(feed, apparel_map, limit=30) for feed in FEEDS]

    previous = None
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = None

    changed = True
    if previous and not force:
        old_groups = previous.get("groups") or []
        changed = content_fingerprint(old_groups) != content_fingerprint(groups)

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not changed and previous and previous.get("updatedAt"):
        updated_at = previous["updatedAt"]

    payload = {
        "version": 1,
        "updatedAt": updated_at,
        "timezoneNote": "App refreshes whenever remote updatedAt differs from local cache (not once/day).",
        "source": "snkrdunk-pokemon-and-onepiece-singles",
        "sources": {
            feed["id"]: search_url(feed["params"]) for feed in FEEDS
        },
        "groups": groups,
    }
    return payload, changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Rewrite even if ranks are unchanged")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload, changed = build_payload(force=args.force)
    counts = {g["id"]: len(g["cards"]) for g in payload["groups"]}
    print(f"groups={counts} changed={changed} updatedAt={payload['updatedAt']}")

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:2500])
        return 0

    if not changed and not args.force:
        print("No content change — leaving trending.json untouched")
        return 0

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
