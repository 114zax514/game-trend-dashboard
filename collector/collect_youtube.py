"""YouTubeの関連動画数を収集し、data/raw/に追記する

無料クォータ(1日1万ユニット、検索1回=100ユニット)の制約上、
1日に処理できるのは概ね90件程度が上限。games_masterがそれを超えて
増え続けた場合は一部のゲームが対象外になる(8節の未決事項を参照)。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timezone, timedelta
from sources import youtube
from games_master import load_master
from raw_store import append_records

JST = timezone(timedelta(hours=9))
DAILY_QUOTA_LIMIT = 90


def main() -> None:
    if not youtube.has_credentials():
        print("[youtube] YOUTUBE_API_KEY が未設定のためスキップします")
        return

    games = load_master()
    if len(games) > DAILY_QUOTA_LIMIT:
        print(
            f"[youtube] 警告: 追跡ゲーム数({len(games)})がクォータ上限({DAILY_QUOTA_LIMIT})を"
            f"超えているため、一部のゲームは本日対象外になります"
        )
    target_games = games[:DAILY_QUOTA_LIMIT]

    collected_at = datetime.now(JST).isoformat()
    records = []
    for game in target_games:
        try:
            count = youtube.search_video_count(game["name"])
        except Exception as e:
            print(f"[youtube] 取得失敗: {game['name']} ({e})")
            continue

        records.append({
            "collected_at": collected_at,
            "source": "youtube_video_count",
            "game_id": game["game_id"],
            "value": count,
        })
        print(f"{game['name']}: youtube_video_count={count}")

    append_records(records)
    print(f"{len(records)}件のレコードを保存しました")


if __name__ == "__main__":
    main()
