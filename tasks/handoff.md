# 專案交接紀錄

## 本次初始化日期

2026-06-18（Asia/Taipei）

## 目前可確認的專案狀態

- Repo 根目錄包含 Streamlit legacy 應用、FastAPI 後端與 Next.js 前端。
- 目前 Git 分支：`fix/chip-data-latest-available`。
- 分支 HEAD 與 `main` / `origin/main` 目前都在 `c78f149`，目前籌碼修正尚未 commit。
- 工作區有多個已修改與未追蹤檔案，集中在 FastAPI 籌碼資料、評分、報告、Next.js 籌碼 UI 與後端測試。
- 根目錄 Render 設定啟動 Streamlit `app.py`；`api/render.yaml` 另定義 FastAPI Render 服務。
- Next.js 透過 `NEXT_PUBLIC_API_BASE_URL` 呼叫 FastAPI，本機預設為 `http://127.0.0.1:8000`。
- 實際線上部署、域名、環境變數與健康狀態：**待確認**。

## 最近工作進度

### Repo 可確認

- 最近已提交歷史包含 Next.js 研究報告 tabs UI 與圖表佈局調整。
- 目前未提交工作正在統一 FastAPI / Next.js 籌碼資料來源：
  - TWSE / TPEx 官方三大法人與融資融券作為 `chipData`。
  - institutional 與 margin 分別回傳 `current` / `latest_available` / `missing`、`dataDate` 與 `source`。
  - `build_context()`、籌碼 Agent、催化評分與報告改讀官方 `chipData`。
  - FastAPI 不再主動請求 `TaiwanStockInstitutionalInvestorsBuySell` 與 `TaiwanStockMarginPurchaseShortSale`。
  - 已新增 11 項後端回歸測試。
- 已進行 2330（TWSE）與 8299（TPEx）真實官方 API smoke test。
- 已修正 TWSE `代號` 欄位解析、融資風險扣分狀態權重、`chipData.overallStatus` 後端契約與前端顯示，並修正 mock 籌碼來源文案。
- 後端 14 項 unittest、18 個 Python 檔 AST、Next.js TypeScript 與 `git diff --check` 均通過。
- 2330 smoke test：institutional=`current`、margin=`latest_available`、overallStatus=`latest_available`；8299 結果相同，兩者的官方籌碼資料均無 data gap。
- 本次沒有 commit。

### 待使用者補充

- 上一個正式工作階段的驗收標準、預計上線時間與負責人：**待使用者補充**。
- Streamlit legacy 是否繼續維護，或會被 FastAPI / Next.js 取代：**待使用者補充**。
- 目前哪一個 Render / Vercel 環境屬於正式、預覽或已停用：**待使用者補充**。

## 目前阻礙

1. README / DEPLOYMENT / PRODUCT_PLAN / AGENTS 與 FastAPI / Next.js 新版資料流存在描述差異，正式修訂前需先確認產品主線。

## 風險

- **資料正確性**：官方 API 欄位或公布時點變化可能造成誤判 `missing`。
- **評分一致性**：時效權重未完整套用到所有籌碼相關分數。
- **雙軌應用**：根目錄 Streamlit 仍使用 FinMind 籌碼，FastAPI / Next.js 分支則改用官方籌碼，不同入口可能得到不同結果。
- **部署不確定**：repo 有多組部署設定，但沒有在本次初始化中驗證線上環境。
- **未提交變更**：新視窗不得假設工作區可以清除或重做，必須先讀 diff 與測試。
- **機密資料**：FinMind token 只能存在 Secrets、環境變數或本機 `.env`，不得寫入文件、log 或回覆。

## 下一步建議

1. 不要先 commit；先重讀目前 diff 與 `api/tests/test_chip_data_flow.py`。
2. 以 TDD 修正 TWSE `代號` 欄位解析，並確認不破壞 TPEx 路徑。
3. 與使用者確認 `overallStatus` 合併規則，再修改 API 契約與 UI。
4. 修正融資風險扣分的時效權重，補上對應失敗測試。
5. 重跑 `unittest`、Python 語法檢查、TypeScript 檢查、2330 / 8299 smoke test 與 `git diff --check`。
6. 完成 review 並與使用者確認範圍後，才決定是否更新正式文件、提交或部署。

## 新 Codex 聊天視窗應先讀的檔案

1. `AGENTS.md`
2. `tasks/current.md`
3. `tasks/handoff.md`
4. `git status --short --branch` 與目前完整 diff
5. `README.md`、`DEPLOYMENT.md`、`render.yaml`、`api/render.yaml`
6. `api/app/services/analysis.py`
7. `api/app/services/institutional_data.py`
8. `api/app/services/margin_data.py`
9. `api/app/services/chip_data_status.py`
10. `api/app/services/agents.py`
11. `api/app/services/reports.py`
12. `api/app/services/market_data.py`
13. `api/app/models.py`
14. `api/tests/test_chip_data_flow.py`
15. `next-dashboard/lib/types.ts`
16. `next-dashboard/components/stocks/stock-analysis-client.tsx`

新視窗應先複述目前分支、工作區變更、已知阻礙與預計修改範圍，再開始編輯。
