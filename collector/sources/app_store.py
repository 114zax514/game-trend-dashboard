"""App Store関連のデータ取得(Appleの公式RSS、認証不要)

v2の rss.marketingtools.apple.com はtop-grossingチャートを廃止済みのため、
ジャンル絞り込みに対応した旧来のiTunes RSS(itunes.apple.com)を使用する。
"""
import requests

HEADERS = {"User-Agent": "game-trend-dashboard (personal project)"}
TIMEOUT = 10
GAMES_GENRE_ID = 6014


def discover_top_grossing(country: str = "jp", limit: int = 25) -> list[dict]:
    """ゲームカテゴリの売上ランキング上位を順位付きで取得"""
    url = f"https://itunes.apple.com/{country}/rss/topgrossingapplications/limit={limit}/genre={GAMES_GENRE_ID}/json"
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    entries = resp.json().get("feed", {}).get("entry", [])

    results = []
    for rank, entry in enumerate(entries, start=1):
        app_id = entry.get("id", {}).get("attributes", {}).get("im:id")
        name = entry.get("im:name", {}).get("label")
        if app_id and name:
            results.append({"ios_app_id": app_id, "name": name, "rank": rank})
    return results
