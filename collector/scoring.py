"""正規化(パーセンタイル順位)・水準/勢いスコア・二層スコアの算出

設計ドキュメント4節に対応。指標が欠損しているゲームは加重平均の対象から
自然に除外(残りの指標で重みを再配分)し、勢いスコアは過去28日分のデータが
揃うまではNone(算出不可)として扱う。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from games_master import load_master

JST = timezone(timedelta(hours=9))
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
SCORES_DIR = Path(__file__).parent.parent / "data" / "scores"

MOMENTUM_RECENT_DAYS = 7
MOMENTUM_BASE_DAYS = 28
LOAD_WINDOW_DAYS = 90

CATEGORY_CORE_WEIGHTS = {
    "premium": {"steam_concurrent": 0.6, "steam_review_pace": 0.4},
    "f2p": {"store_rank": 0.7, "store_review_pace": 0.3},
}
ATTENTION_WEIGHTS = {
    "trends_index": 0.25,
    "twitch_viewers": 0.25,
    "youtube_video_count": 0.25,
    "reddit_post_count": 0.25,
}


def load_raw_records(days: int = LOAD_WINDOW_DAYS) -> list[dict]:
    today = datetime.now(JST).date()
    records = []
    for i in range(days):
        date = today - timedelta(days=i)
        path = RAW_DIR / f"{date.isoformat()}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                records.extend(json.load(f))
    return records


def daily_aggregate(records: list[dict]) -> dict[tuple[str, str, str], float]:
    """(date, source, game_id) -> 日次平均値"""
    buckets = defaultdict(list)
    for r in records:
        date = r["collected_at"][:10]
        buckets[(date, r["source"], r["game_id"])].append(r["value"])
    return {key: sum(vals) / len(vals) for key, vals in buckets.items()}


def percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    """game_id -> value を game_id -> パーセンタイル順位(0-100)に変換"""
    if not values:
        return {}
    ordered = sorted(values, key=lambda g: values[g])
    n = len(ordered)
    if n == 1:
        return {ordered[0]: 100.0}
    return {game_id: round(100 * i / (n - 1), 1) for i, game_id in enumerate(ordered)}


def weighted_combine(per_metric_scores: dict[str, dict[str, float]], weights: dict[str, float]) -> dict[str, float]:
    """指標ごとのパーセンタイル群を重み付き合成。欠損指標は保有指標のみで重み再配分"""
    game_ids = {gid for scores in per_metric_scores.values() for gid in scores}
    combined = {}
    for game_id in game_ids:
        available = [(m, per_metric_scores[m][game_id]) for m in weights if game_id in per_metric_scores.get(m, {})]
        if not available:
            continue
        total_weight = sum(weights[m] for m, _ in available)
        combined[game_id] = round(sum(weights[m] * v for m, v in available) / total_weight, 1)
    return combined


def compute_level(daily: dict, dates: list[str], weights: dict[str, float]) -> dict[str, float]:
    latest_date = dates[-1]
    per_metric = {}
    for source in weights:
        values = {gid: v for (d, src, gid), v in daily.items() if d == latest_date and src == source}
        if values:
            per_metric[source] = percentile_ranks(values)
    return weighted_combine(per_metric, weights)


def compute_momentum(daily: dict, dates: list[str], weights: dict[str, float]) -> dict[str, float] | None:
    if len(dates) < MOMENTUM_BASE_DAYS:
        return None

    recent_dates = set(dates[-MOMENTUM_RECENT_DAYS:])
    base_dates = set(dates[-MOMENTUM_BASE_DAYS:])

    per_metric_ratio_ranks = {}
    for source in weights:
        recent = defaultdict(list)
        base = defaultdict(list)
        for (d, src, gid), v in daily.items():
            if src != source:
                continue
            if d in recent_dates:
                recent[gid].append(v)
            if d in base_dates:
                base[gid].append(v)

        ratios = {}
        for gid, base_vals in base.items():
            base_avg = sum(base_vals) / len(base_vals)
            recent_vals = recent.get(gid)
            if not recent_vals or base_avg == 0:
                continue
            ratios[gid] = (sum(recent_vals) / len(recent_vals)) / base_avg

        if ratios:
            per_metric_ratio_ranks[source] = percentile_ranks(ratios)

    return weighted_combine(per_metric_ratio_ranks, weights)


def latest_values_by_source(daily: dict, dates: list[str]) -> dict[str, dict[str, float]]:
    """game_id -> {source: 最新値} (platforms_breakdown用)"""
    latest_date = dates[-1]
    breakdown = defaultdict(dict)
    for (d, src, gid), v in daily.items():
        if d == latest_date:
            breakdown[gid][src] = v
    return breakdown


def main() -> None:
    games = load_master()
    records = load_raw_records()
    if not records:
        print("生データが見つかりません。先に収集スクリプトを実行してください。")
        return

    daily = daily_aggregate(records)
    dates = sorted({d for d, _, _ in daily})
    print(f"対象日数: {len(dates)}日分 ({dates[0]} 〜 {dates[-1]})")

    breakdown = latest_values_by_source(daily, dates)

    output_games = []
    for game in games:
        category = game["category"]
        core_weights = CATEGORY_CORE_WEIGHTS.get(category, {})

        core_level = compute_level(daily, dates, core_weights).get(game["game_id"])
        core_momentum_all = compute_momentum(daily, dates, core_weights)
        core_momentum = core_momentum_all.get(game["game_id"]) if core_momentum_all is not None else None

        attention_level = compute_level(daily, dates, ATTENTION_WEIGHTS).get(game["game_id"])
        attention_momentum_all = compute_momentum(daily, dates, ATTENTION_WEIGHTS)
        attention_momentum = attention_momentum_all.get(game["game_id"]) if attention_momentum_all is not None else None

        output_games.append({
            "game_id": game["game_id"],
            "name": game["name"],
            "category": category,
            "needs_review": game.get("needs_review", False),
            "category_core": {"level": core_level, "momentum": core_momentum},
            "attention": {"level": attention_level, "momentum": attention_momentum},
            "platforms_breakdown": breakdown.get(game["game_id"], {}),
        })

    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "updated_at": datetime.now(JST).isoformat(),
        "games": output_games,
    }
    with open(SCORES_DIR / "latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"data/scores/latest.json を更新しました({len(output_games)}ゲーム)")


if __name__ == "__main__":
    main()
