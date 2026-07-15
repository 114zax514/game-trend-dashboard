"""生データ(data/raw/YYYY-MM-DD.json)の読み書きヘルパー"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"


def append_records(records: list[dict]) -> None:
    """本日分のファイルにレコードを追記する"""
    if not records:
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(JST).strftime("%Y-%m-%d")
    path = RAW_DIR / f"{today}.json"

    existing = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)

    existing.extend(records)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
