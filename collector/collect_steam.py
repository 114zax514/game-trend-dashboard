"""Steamの同時接続数を収集し、data/raw/に追記する"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timezone, timedelta
from sources import steam
from games_master import load_master
from raw_store import append_records

JST = timezone(timedelta(hours=9))


def main() -> None:
    games = load_master()
    steam_games = [g for g in games if g.get("platforms", {}).get("steam_appid")]

    records = []
    collected_at = datetime.now(JST).isoformat()
    for game in steam_games:
        appid = game["platforms"]["steam_appid"]
        steam.polite_sleep()
        count = steam.get_concurrent_players(appid)
        if count is None:
            print(f"取得失敗: {game['name']} (appid={appid})")
            continue
        records.append({
            "collected_at": collected_at,
            "source": "steam_concurrent",
            "game_id": game["game_id"],
            "value": count,
        })
        print(f"{game['name']}: {count}人")

    append_records(records)
    print(f"{len(records)}件のレコードを保存しました")


if __name__ == "__main__":
    main()
