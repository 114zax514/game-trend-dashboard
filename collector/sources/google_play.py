"""Google Play関連のデータ取得

google-play-scraper(Python)はトップチャート取得APIを提供していないため、
トップセールス(ゲーム)コレクションページに埋め込まれたパッケージ名を
正規表現で抽出し、詳細(タイトル・無料/有料)は google-play-scraper の
個別アプリ取得(app())で補う。
"""
import re
import time
import requests
import google_play_scraper as gp

HEADERS = {"User-Agent": "Mozilla/5.0 (game-trend-dashboard personal project)"}
TIMEOUT = 15
_PACKAGE_RE = re.compile(r'"((?:com|net|jp|org|io)\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)"')
COLLECTION_URL = "https://play.google.com/store/apps/collection/topselling_grossing_games"


def discover_top_grossing(country: str = "jp", lang: str = "ja", limit: int = 25) -> list[dict]:
    """ゲームの売上ランキング上位を順位付きで取得(パッケージ名のみ、詳細は別途取得)"""
    resp = requests.get(
        COLLECTION_URL, params={"hl": lang, "gl": country}, headers=HEADERS, timeout=TIMEOUT
    )
    resp.raise_for_status()
    packages = _PACKAGE_RE.findall(resp.text)
    seen = []
    for pkg in packages:
        if pkg not in seen:
            seen.append(pkg)
    return [{"android_package": pkg, "rank": i + 1} for i, pkg in enumerate(seen[:limit])]


def get_app_details(package: str, country: str = "jp", lang: str = "ja") -> dict | None:
    try:
        info = gp.app(package, lang=lang, country=country)
    except Exception:
        return None
    return {"name": info.get("title"), "is_free": info.get("free", True)}


def polite_sleep(seconds: float = 1.0) -> None:
    time.sleep(seconds)
