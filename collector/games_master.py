"""ゲームマスタ(games_master.yml)の読み書きヘルパー"""
from pathlib import Path
import yaml

MASTER_PATH = Path(__file__).parent / "games_master.yml"


def load_master() -> list[dict]:
    if not MASTER_PATH.exists():
        return []
    with open(MASTER_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or []


def save_master(games: list[dict]) -> None:
    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(games, f, allow_unicode=True, sort_keys=False)


def find_by_steam_appid(games: list[dict], appid: int) -> dict | None:
    for g in games:
        if g.get("platforms", {}).get("steam_appid") == appid:
            return g
    return None


def find_by_platform_id(games: list[dict], key: str, value: str) -> dict | None:
    """platforms.{key} が value と一致するゲームを探す(ios_app_id/android_package用)"""
    for g in games:
        if g.get("platforms", {}).get(key) == value:
            return g
    return None


def normalize_name(name: str) -> str:
    """名前突合用の簡易正規化(空白除去・小文字化・全角/半角記号ゆらぎは非対応)"""
    return "".join(name.split()).casefold()


def find_by_name(games: list[dict], name: str) -> dict | None:
    """名前の完全一致(正規化後)でゲームを探す。表記ゆれは拾えないためneeds_review運用で補う"""
    target = normalize_name(name)
    for g in games:
        if normalize_name(g["name"]) == target:
            return g
    return None


def make_game_id(name: str, appid) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in name)
    slug = "-".join(filter(None, slug.split("-")))
    return slug or f"game-{appid}"
