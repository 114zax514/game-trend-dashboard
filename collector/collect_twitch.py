"""Twitchの視聴者数・配信者数を収集し、data/raw/に追記する

games_master.ymlにtwitch_game_idが無いゲームは、ゲーム名で検索して
埋める(自動下書き)。TWITCH_CLIENT_ID/TWITCH_CLIENT_SECRETが必要。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timezone, timedelta
from sources import twitch
from games_master import load_master, save_master
from raw_store import append_records

JST = timezone(timedelta(hours=9))


def fill_missing_twitch_ids(games: list[dict]) -> int:
    filled = 0
    for game in games:
        if game["platforms"].get("twitch_game_id"):
            continue
        twitch.polite_sleep()
        try:
            game_id = twitch.find_game_id(game["name"])
        except Exception as e:
            print(f"[twitch] game_id検索失敗: {game['name']} ({e})")
            continue
        if game_id:
            game["platforms"]["twitch_game_id"] = game_id
            filled += 1
            print(f"[twitch] game_id紐付け: {game['name']} -> {game_id}")
    return filled


def main() -> None:
    if not twitch.has_credentials():
        print("[twitch] TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET が未設定のためスキップします")
        return

    games = load_master()

    filled = fill_missing_twitch_ids(games)
    if filled:
        save_master(games)

    collected_at = datetime.now(JST).isoformat()
    records = []
    for game in games:
        game_id = game["platforms"].get("twitch_game_id")
        if not game_id:
            continue

        twitch.polite_sleep()
        try:
            stats = twitch.get_viewer_stats(game_id)
        except Exception as e:
            print(f"[twitch] 取得失敗: {game['name']} ({e})")
            continue

        records.append({
            "collected_at": collected_at,
            "source": "twitch_viewers",
            "game_id": game["game_id"],
            "value": stats["viewers"],
        })
        records.append({
            "collected_at": collected_at,
            "source": "twitch_streamers",
            "game_id": game["game_id"],
            "value": stats["streamers"],
        })
        print(f"{game['name']}: 視聴者={stats['viewers']}, 配信者={stats['streamers']}")

    append_records(records)
    print(f"{len(records)}件のレコードを保存しました")


if __name__ == "__main__":
    main()
