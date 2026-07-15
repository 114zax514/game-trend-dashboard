import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // data/ (収集・スコアリング結果)をそのまま静的配信する。
  // ビルド時も同様にdist配下へコピーされるため、GitHub Pagesデプロイ時も追加の手順は不要。
  publicDir: '../data',
})
