"""YouTube関連のデータ取得(公式Data API v3)

YOUTUBE_API_KEY 環境変数が必要。Google Cloud Consoleで
YouTube Data API v3 を有効化しAPIキーを発行すると取得できる。
無料枠は1日1万ユニット、search1回=100ユニット(1日あたり約100回まで)。
"""
import os
from datetime import datetime, timezone, timedelta
import requests

TIMEOUT = 10
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def has_credentials() -> bool:
    return bool(os.environ.get("YOUTUBE_API_KEY"))


def search_video_count(game_name: str, days: int = 7) -> int:
    """直近days日間に投稿された関連動画のおおよその件数(totalResults)"""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY が設定されていません")

    published_after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    resp = requests.get(
        SEARCH_URL,
        params={
            "part": "snippet",
            "q": game_name,
            "type": "video",
            "order": "date",
            "publishedAfter": published_after,
            "maxResults": 1,
            "key": api_key,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("pageInfo", {}).get("totalResults", 0)
