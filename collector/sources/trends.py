"""Google Trends関連のデータ取得(pytrends、非公式)

1リクエスト最大5キーワードの制限とバッチ内相対値の制約(設計ドキュメント
2.1/4.1参照)に対応するため、毎バッチに共通のアンカーキーワードを含め、
アンカーの値を基準に全バッチを同一スケールにリスケーリングする
(rescaled = キーワード値 / アンカー値)。

Googleの反スクレイピング対策により単発でも429が返ることがあるため、
リトライ・バッチ間隔を設けて緩和する(それでも失敗する場合は諦めてスキップし
全体を止めない)。
"""
import time
from pytrends.request import TrendReq

ANCHOR_KEYWORD = "Minecraft"
BATCH_SIZE = 4  # + アンカー1件で5キーワード/リクエスト
BATCH_INTERVAL_SECONDS = 5


def fetch_trends_index(game_names: list[str], geo: str = "JP") -> dict[str, float]:
    """ゲーム名 -> アンカー基準にリスケーリングされたTrends指数(相対値)"""
    pytrends = TrendReq(hl="ja-JP", tz=540, retries=3, backoff_factor=2)
    results: dict[str, float] = {}

    unique_names = list(dict.fromkeys(game_names))
    for i in range(0, len(unique_names), BATCH_SIZE):
        batch = unique_names[i:i + BATCH_SIZE]
        keywords = batch + [ANCHOR_KEYWORD]

        try:
            pytrends.build_payload(keywords, timeframe="now 7-d", geo=geo)
            df = pytrends.interest_over_time()
        except Exception as e:
            print(f"[trends] 取得失敗のためスキップ: {batch} ({e})")
            time.sleep(BATCH_INTERVAL_SECONDS)
            continue

        if df.empty or ANCHOR_KEYWORD not in df:
            time.sleep(BATCH_INTERVAL_SECONDS)
            continue

        anchor_value = df[ANCHOR_KEYWORD].mean()
        if anchor_value == 0:
            time.sleep(BATCH_INTERVAL_SECONDS)
            continue

        for name in batch:
            if name in df:
                results[name] = df[name].mean() / anchor_value

        time.sleep(BATCH_INTERVAL_SECONDS)

    return results
