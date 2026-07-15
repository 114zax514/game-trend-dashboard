"""Twitch関連のデータ取得(公式Helix API)

TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET 環境変数が必要。
https://dev.twitch.tv/console/apps でアプリ登録すると取得できる。
"""
import os
import time
import requests

TIMEOUT = 10
_token_cache = {"value": None, "expires_at": 0}


def has_credentials() -> bool:
    return bool(os.environ.get("TWITCH_CLIENT_ID")) and bool(os.environ.get("TWITCH_CLIENT_SECRET"))


def _get_client_credentials() -> tuple[str, str]:
    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET が設定されていません")
    return client_id, client_secret


def get_access_token() -> str:
    """App Access Tokenを取得(有効期限内はキャッシュを再利用)"""
    if _token_cache["value"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["value"]

    client_id, client_secret = _get_client_credentials()
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["value"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"]
    return _token_cache["value"]


def _headers() -> dict:
    client_id, _ = _get_client_credentials()
    return {"Client-Id": client_id, "Authorization": f"Bearer {get_access_token()}"}


def find_game_id(name: str) -> str | None:
    """ゲーム名からTwitchのgame_idを検索"""
    resp = requests.get(
        "https://api.twitch.tv/helix/games",
        params={"name": name},
        headers=_headers(),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return data[0]["id"] if data else None


def get_viewer_stats(game_id: str) -> dict:
    """指定ゲームの現在の視聴者数合計・配信者数(最大100配信まで集計)"""
    resp = requests.get(
        "https://api.twitch.tv/helix/streams",
        params={"game_id": game_id, "first": 100},
        headers=_headers(),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    streams = resp.json().get("data", [])
    return {
        "viewers": sum(s.get("viewer_count", 0) for s in streams),
        "streamers": len(streams),
    }


def polite_sleep(seconds: float = 0.5) -> None:
    time.sleep(seconds)
