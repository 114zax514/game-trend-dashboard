"""Steam人気ランキング上位から新規ゲームをgames_master.ymlに自動追加する"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sources import steam
from games_master import load_master, save_master, find_by_steam_appid, make_game_id

TOP_N = 30
NON_BASE_GAME_MARKERS = [
    "アップグレードキット", "DLC", "サウンドトラック", "Soundtrack",
    "シーズンパス", "Season Pass", "Artbook", "アートブック",
]


def main() -> None:
    games = load_master()
    top_sellers = steam.discover_top_sellers()[:TOP_N]

    added = 0
    for item in top_sellers:
        appid = item["appid"]
        if find_by_steam_appid(games, appid):
            continue

        steam.polite_sleep()
        details = steam.get_app_details(appid)
        if not details:
            print(f"appdetails取得失敗のためスキップ: appid={appid}")
            continue

        name = details["name"] or item["name"]
        if any(marker in name for marker in NON_BASE_GAME_MARKERS):
            print(f"DLC等と判定しスキップ: {name} (appid={appid})")
            continue

        category = "f2p" if details["is_free"] else "premium"
        games.append({
            "game_id": make_game_id(name, appid),
            "name": name,
            "category": category,
            "needs_review": True,
            "platforms": {
                "steam_appid": appid,
                "twitch_game_id": None,
                "ios_app_id": None,
                "android_package": None,
            },
        })
        added += 1
        print(f"追加: {name} (appid={appid}, category={category})")

    save_master(games)
    print(f"新規追加: {added}件 / games_master合計: {len(games)}件")


if __name__ == "__main__":
    main()
