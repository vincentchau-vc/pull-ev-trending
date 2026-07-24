#!/usr/bin/env python3
"""Scrape SNKRDUNK popular singles (Pokémon + One Piece) → trending.json.

Only rewrites the file (and bumps updatedAt) when the ranked card lists change.
Card display names are English. App lets the user pick one brand at a time.

With --commit-push: after a content write, git add / commit / push to the
default branch so raw.githubusercontent.com picks up the new trending.json.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "trending.json"
MAP_PATH = ROOT / "apparel-map.json"

# Cards per brand in the published feed (app pages these locally in chunks of ~30).
TARGET_LIMIT = 300
# SNKRDUNK search HTML typically yields ~30 apparel hits per page.
PAGE_SIZE_HINT = 30

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


def search_url(params: dict, page: int = 1) -> str:
    query = dict(params)
    query["page"] = str(page)
    return "https://snkrdunk.com/search?" + urllib.parse.urlencode(query)


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


def parse_search_html(raw: str) -> list[tuple[int, str]]:
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
    return list(zip(ids, names))


def scrape_search_page(params: dict, page: int) -> list[tuple[int, str]]:
    url = search_url(params, page=page)
    raw = http_get(url).decode("utf-8", "ignore")
    return parse_search_html(raw)


def scrape_search_paginated(params: dict, limit: int = TARGET_LIMIT) -> list[tuple[int, str]]:
    """Walk SNKRDUNK search pages until `limit` unique apparels or results exhaust."""
    pairs: list[tuple[int, str]] = []
    seen: set[int] = set()
    page = 1
    while len(pairs) < limit:
        page_pairs = scrape_search_page(params, page)
        if not page_pairs:
            break

        new_on_page = 0
        for apparel_id, name in page_pairs:
            if apparel_id in seen:
                continue
            seen.add(apparel_id)
            pairs.append((apparel_id, name))
            new_on_page += 1
            if len(pairs) >= limit:
                break

        # No progress or a short final page → stop.
        if new_on_page == 0 or len(page_pairs) < max(5, PAGE_SIZE_HINT // 2):
            break

        page += 1
        time.sleep(0.25)

    if len(pairs) < 5:
        raise RuntimeError(
            f"scrape returned too few items ({len(pairs)}) for {search_url(params, page=1)}"
        )
    return pairs[:limit]


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


def build_group(feed: dict, apparel_map: dict[int, str], limit: int = TARGET_LIMIT) -> dict:
    pairs = scrape_search_paginated(feed["params"], limit=limit)
    print(f"  {feed['id']}: scraped {len(pairs)} ranked hits (target {limit})")
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


def build_payload(force: bool = False, limit: int = TARGET_LIMIT) -> tuple[dict, bool]:
    apparel_map = load_apparel_map()
    groups = [build_group(feed, apparel_map, limit=limit) for feed in FEEDS]

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
            feed["id"]: search_url(feed["params"], page=1) for feed in FEEDS
        },
        "groups": groups,
    }
    return payload, changed


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def commit_and_push() -> None:
    """Stage trending.json, commit if needed, and push to the tracked remote branch.

    Fails the run if push cannot update GitHub (raw.githubusercontent.com otherwise stays stale).
    Does not force-push or change git config.
    """
    status = run_git(["status", "--porcelain", "--", "trending.json"])
    if status.returncode != 0:
        raise RuntimeError(f"git status failed: {status.stderr.strip()}")

    if status.stdout.strip():
        add = run_git(["add", "--", "trending.json"])
        if add.returncode != 0:
            raise RuntimeError(f"git add failed: {add.stderr.strip()}")

        commit = run_git(
            [
                "commit",
                "-m",
                "chore: refresh trending from SNKRDUNK",
            ]
        )
        if commit.returncode != 0:
            raise RuntimeError(f"git commit failed: {commit.stderr.strip() or commit.stdout.strip()}")
        print("Committed trending.json")
    else:
        print("trending.json already staged/committed — pushing if needed")

    # Resolve upstream; fall back to origin + current branch.
    branch_proc = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch_proc.returncode != 0:
        raise RuntimeError(f"git rev-parse failed: {branch_proc.stderr.strip()}")
    branch = branch_proc.stdout.strip() or "main"

    # Integrate remote first so a stale local clone does not reject the push
    # (commit-only without push leaves raw.githubusercontent.com unchanged).
    fetch = run_git(["fetch", "origin", branch])
    if fetch.returncode != 0:
        print(f"warning: git fetch failed: {fetch.stderr.strip() or fetch.stdout.strip()}")

    rebase = run_git(["rebase", f"origin/{branch}"])
    if rebase.returncode != 0:
        run_git(["rebase", "--abort"])
        raise RuntimeError(
            "git rebase onto origin failed — resolve divergence manually, then "
            f"re-run with --commit-push.\n{rebase.stderr.strip() or rebase.stdout.strip()}"
        )

    upstream_proc = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if upstream_proc.returncode == 0 and upstream_proc.stdout.strip():
        push = run_git(["push"])
    else:
        push = run_git(["push", "-u", "origin", branch])

    if push.returncode != 0:
        raise RuntimeError(
            "git push failed — trending.json will NOT update on raw.githubusercontent.com. "
            f"Fix credentials/permissions and re-run with --commit-push.\n{push.stderr.strip() or push.stdout.strip()}"
        )
    print(f"Pushed to origin ({branch}) — raw feed should update shortly")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Rewrite even if ranks are unchanged")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--limit",
        type=int,
        default=TARGET_LIMIT,
        help=f"Cards per brand (default {TARGET_LIMIT})",
    )
    parser.add_argument(
        "--commit-push",
        action="store_true",
        help="After writing trending.json, git commit and push so GitHub raw updates",
    )
    args = parser.parse_args()

    payload, changed = build_payload(force=args.force, limit=max(1, args.limit))
    counts = {g["id"]: len(g["cards"]) for g in payload["groups"]}
    print(f"groups={counts} changed={changed} updatedAt={payload['updatedAt']}")

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:2500])
        return 0

    wrote = False
    if not changed and not args.force:
        print("No content change — leaving trending.json untouched")
    else:
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {OUT}")
        wrote = True

    if args.commit_push:
        if wrote or args.force:
            try:
                commit_and_push()
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                return 1
        else:
            print("No content change — skip commit/push")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
