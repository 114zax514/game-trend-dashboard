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


def make_game_id(name: str, appid: int) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in name)
    slug = "-".join(filter(None, slug.split("-")))
    return slug or f"steam-{appid}"
