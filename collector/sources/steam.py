"""Steam関連のデータ取得(すべて認証不要の公開エンドポイント)"""
import re
import time
import requests

HEADERS = {"User-Agent": "game-trend-dashboard (personal project)"}
TIMEOUT = 10
_APPID_RE = re.compile(r'data-ds-appid="(\d+)"')


def discover_top_sellers(cc: str = "jp", lang: str = "japanese", count: int = 30) -> list[dict]:
    """人気/売上ランキング上位を取得

    featuredcategories APIのtop_sellersは販促中のDLC等が混じり精度が低いため、
    ストア検索(filter=topsellers)の実際の並び順をパースする。
    """
    url = "https://store.steampowered.com/search/results/"
    resp = requests.get(
        url,
        params={
            "query": "",
            "start": 0,
            "count": count,
            "sort_by": "_ASC",
            "filter": "topsellers",
            "infinite": 1,
            "cc": cc,
            "l": lang,
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    html = resp.json().get("results_html", "")
    appids = _APPID_RE.findall(html)
    # 同一appidが複数箇所に出現する場合があるため順序を保ったまま重複除去
    seen = set()
    ordered = []
    for appid in appids:
        if appid not in seen:
            seen.add(appid)
            ordered.append(int(appid))
    return [{"appid": appid, "name": ""} for appid in ordered]


def get_app_details(appid: int, cc: str = "jp", lang: str = "japanese") -> dict | None:
    """アプリ詳細(name, is_free等)を取得"""
    url = "https://store.steampowered.com/api/appdetails"
    resp = requests.get(
        url, params={"appids": appid, "cc": cc, "l": lang}, headers=HEADERS, timeout=TIMEOUT
    )
    resp.raise_for_status()
    payload = resp.json().get(str(appid))
    if not payload or not payload.get("success"):
        return None
    data = payload["data"]
    return {"name": data.get("name"), "is_free": data.get("is_free", False)}


def get_concurrent_players(appid: int) -> int | None:
    """現在の同時接続数を取得"""
    url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    resp = requests.get(url, params={"appid": appid, "format": "json"}, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    response = resp.json().get("response", {})
    if response.get("result") != 1:
        return None
    return response.get("player_count")


def polite_sleep(seconds: float = 1.0) -> None:
    """Steam非公式利用のマナーとしてリクエスト間隔を空ける"""
    time.sleep(seconds)
