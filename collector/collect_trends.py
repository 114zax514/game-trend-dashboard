"""Google Trendsの検索インタレスト指数を収集し、data/raw/に追記する"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timezone, timedelta
from sources import trends
from games_master import load_master
from raw_store import append_records

JST = timezone(timedelta(hours=9))


def main() -> None:
    games = load_master()
    game_names = [g["name"] for g in games]

    values = trends.fetch_trends_index(game_names)

    collected_at = datetime.now(JST).isoformat()
    records = []
    for game in games:
        value = values.get(game["name"])
        if value is None:
            continue
        records.append({
            "collected_at": collected_at,
            "source": "trends_index",
            "game_id": game["game_id"],
            "value": value,
        })
        print(f"{game['name']}: trends_index={value:.3f}")

    append_records(records)
    print(f"{len(records)}件のレコードを保存しました({len(games)}件中)")


if __name__ == "__main__":
    main()
