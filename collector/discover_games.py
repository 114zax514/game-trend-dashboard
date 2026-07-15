"""各ストアの人気ランキング上位から新規ゲームをgames_master.ymlに自動追加する

3.3節: Steam(買い切り中心) + App Store/Google Play Top Grossing(F2P中心)を
発見元とし、名前の完全一致でプラットフォーム間の突合を試みる(自動下書き)。
一致しない/確証が持てないものはneeds_review=trueのまま残す。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sources import steam, app_store, google_play
from games_master import (
    load_master, save_master, find_by_steam_appid, find_by_platform_id,
    find_by_name, make_game_id, is_plausible_game_name,
)

TOP_N = 30
NON_BASE_GAME_MARKERS = [
    "アップグレードキット", "DLC", "サウンドトラック", "Soundtrack",
    "シーズンパス", "Season Pass", "Artbook", "アートブック",
]

NEW_PLATFORMS_TEMPLATE = {
    "steam_appid": None,
    "twitch_game_id": None,
    "ios_app_id": None,
    "android_package": None,
}


def discover_steam(games: list[dict]) -> int:
    added = 0
    for item in steam.discover_top_sellers()[:TOP_N]:
        appid = item["appid"]
        if find_by_steam_appid(games, appid):
            continue

        steam.polite_sleep()
        details = steam.get_app_details(appid)
        if not details:
            print(f"[steam] appdetails取得失敗のためスキップ: appid={appid}")
            continue

        name = details["name"] or item["name"]
        if not is_plausible_game_name(name):
            print(f"[steam] 不正なタイトルと判定しスキップ: {name!r} (appid={appid})")
            continue
        if any(marker in name for marker in NON_BASE_GAME_MARKERS):
            print(f"[steam] DLC等と判定しスキップ: {name} (appid={appid})")
            continue

        existing = find_by_name(games, name)
        if existing:
            existing["platforms"]["steam_appid"] = appid
            print(f"[steam] 既存ゲームにID紐付け: {name} (appid={appid})")
            continue

        category = "f2p" if details["is_free"] else "premium"
        platforms = dict(NEW_PLATFORMS_TEMPLATE, steam_appid=appid)
        games.append({
            "game_id": make_game_id(name, appid),
            "name": name,
            "category": category,
            "needs_review": True,
            "platforms": platforms,
        })
        added += 1
        print(f"[steam] 追加: {name} (appid={appid}, category={category})")
    return added


def discover_ios(games: list[dict]) -> int:
    added = 0
    for item in app_store.discover_top_grossing(limit=TOP_N):
        app_id = item["ios_app_id"]
        name = item["name"]
        if find_by_platform_id(games, "ios_app_id", app_id):
            continue
        if not is_plausible_game_name(name):
            print(f"[ios] 不正なタイトルと判定しスキップ: {name!r} (app_id={app_id})")
            continue

        existing = find_by_name(games, name)
        if existing:
            existing["platforms"]["ios_app_id"] = app_id
            print(f"[ios] 既存ゲームにID紐付け: {name} (app_id={app_id})")
            continue

        platforms = dict(NEW_PLATFORMS_TEMPLATE, ios_app_id=app_id)
        games.append({
            "game_id": make_game_id(name, app_id),
            "name": name,
            "category": "f2p",
            "needs_review": True,
            "platforms": platforms,
        })
        added += 1
        print(f"[ios] 追加: {name} (app_id={app_id}, category=f2p)")
    return added


def discover_android(games: list[dict]) -> int:
    added = 0
    for item in google_play.discover_top_grossing(limit=TOP_N):
        package = item["android_package"]
        if find_by_platform_id(games, "android_package", package):
            continue

        google_play.polite_sleep()
        details = google_play.get_app_details(package)
        if not details or not details["name"]:
            print(f"[android] 詳細取得失敗のためスキップ: package={package}")
            continue

        name = details["name"]
        if not is_plausible_game_name(name):
            print(f"[android] 不正なタイトルと判定しスキップ: {name!r} (package={package})")
            continue

        existing = find_by_name(games, name)
        if existing:
            existing["platforms"]["android_package"] = package
            print(f"[android] 既存ゲームにID紐付け: {name} (package={package})")
            continue

        category = "f2p" if details["is_free"] else "premium"
        platforms = dict(NEW_PLATFORMS_TEMPLATE, android_package=package)
        games.append({
            "game_id": make_game_id(name, package),
            "name": name,
            "category": category,
            "needs_review": True,
            "platforms": platforms,
        })
        added += 1
        print(f"[android] 追加: {name} (package={package}, category={category})")
    return added


def main() -> None:
    games = load_master()

    steam_added = discover_steam(games)
    ios_added = discover_ios(games)
    android_added = discover_android(games)

    save_master(games)
    total_added = steam_added + ios_added + android_added
    print(
        f"新規追加: 合計{total_added}件(steam={steam_added}, ios={ios_added}, "
        f"android={android_added}) / games_master合計: {len(games)}件"
    )


if __name__ == "__main__":
    main()
