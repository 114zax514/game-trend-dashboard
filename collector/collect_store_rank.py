"""App Store/Google Playの売上ランキング順位を収集し、data/raw/に追記する

順位は「大きいほど良い」という他指標との統一表現に合わせるため、
value = TOP_N + 1 - rank に変換して保存する(1位が最高値になる)。
両ストアに掲載されているゲームは、良い方(値が大きい方)を採用する。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timezone, timedelta
from sources import app_store, google_play
from games_master import load_master
from raw_store import append_records

JST = timezone(timedelta(hours=9))
TOP_N = 30


def main() -> None:
    games = load_master()
    collected_at = datetime.now(JST).isoformat()

    ios_ranks = {item["ios_app_id"]: item["rank"] for item in app_store.discover_top_grossing(limit=TOP_N)}
    android_ranks = {
        item["android_package"]: item["rank"] for item in google_play.discover_top_grossing(limit=TOP_N)
    }

    records = []
    for game in games:
        platforms = game["platforms"]
        values = []
        if platforms.get("ios_app_id") in ios_ranks:
            values.append(TOP_N + 1 - ios_ranks[platforms["ios_app_id"]])
        if platforms.get("android_package") in android_ranks:
            values.append(TOP_N + 1 - android_ranks[platforms["android_package"]])
        if not values:
            continue

        value = max(values)
        records.append({
            "collected_at": collected_at,
            "source": "store_rank",
            "game_id": game["game_id"],
            "value": value,
        })
        print(f"{game['name']}: store_rank={value}")

    append_records(records)
    print(f"{len(records)}件のレコードを保存しました")


if __name__ == "__main__":
    main()
