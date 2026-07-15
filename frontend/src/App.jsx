import { useEffect, useState } from 'react'
import './App.css'

const CATEGORY_LABEL = { premium: '買い切り', f2p: 'F2P' }

function sortKey(game) {
  if (game.attention.level != null) return game.attention.level
  if (game.category_core.level != null) return game.category_core.level
  return -1
}

function ScoreMeter({ value }) {
  if (value == null) return <span className="muted">—</span>
  return (
    <div className="meter" title={`${value}`}>
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${value}%` }} />
      </div>
      <span className="meter-value">{value.toFixed(1)}</span>
    </div>
  )
}

function Momentum({ value }) {
  if (value == null) return <span className="muted">—</span>
  return <span className="tabular">{value.toFixed(1)}</span>
}

function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}scores/latest.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
        return res.json()
      })
      .then(setData)
      .catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <main className="page">
        <p className="error">データの読み込みに失敗しました: {error}</p>
      </main>
    )
  }
  if (!data) {
    return (
      <main className="page">
        <p className="muted">読み込み中…</p>
      </main>
    )
  }

  const games = [...data.games].sort((a, b) => sortKey(b) - sortKey(a))

  return (
    <main className="page">
      <header className="page-header">
        <h1>ゲームトレンドダッシュボード</h1>
        <p className="muted">
          最終更新: {new Date(data.updated_at).toLocaleString('ja-JP')}
        </p>
      </header>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>順位</th>
              <th>ゲーム</th>
              <th>カテゴリ</th>
              <th>水準スコア</th>
              <th>勢いスコア</th>
              <th>横断注目度</th>
              <th className="num">Steam同接数</th>
            </tr>
          </thead>
          <tbody>
            {games.map((game, i) => (
              <tr key={game.game_id}>
                <td className="tabular muted">{i + 1}</td>
                <td>
                  {game.name}
                  {game.needs_review && (
                    <span className="badge badge-warning">
                      <span className="dot" /> 要確認
                    </span>
                  )}
                </td>
                <td>
                  <span className={`badge badge-cat badge-cat-${game.category}`}>
                    {CATEGORY_LABEL[game.category] ?? game.category}
                  </span>
                </td>
                <td>
                  <ScoreMeter value={game.category_core.level} />
                </td>
                <td>
                  <Momentum value={game.category_core.momentum} />
                </td>
                <td>
                  <ScoreMeter value={game.attention.level} />
                </td>
                <td className="num tabular">
                  {game.platforms_breakdown.steam_concurrent != null
                    ? Math.round(game.platforms_breakdown.steam_concurrent).toLocaleString('ja-JP')
                    : <span className="muted">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}

export default App
