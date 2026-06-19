# 專案交接紀錄

## 2026-06-20 TWSE 歷史 PE 區間

- 新增 `api/app/services/pe_history.py`，第一版僅支援 TWSE 上市股票；使用 TWSE `BWIBBU_d` 每日本益比資料，取最近 36 個已完成月份的月末 PE，並在無可用值時往前最多回溯 10 天。
- parser 過濾 `--`、空值、0、負數、非數字與非有限值；輸出 min / p25 / median / p75 / max / validSampleCount，分位數採線性插值。
- 成功取得後寫入 `api/.cache/pe_history/<symbol>.json`（Git 已忽略）；TWSE 網路、JSON 或無可用樣本時會優先讀取上次成功 cache，API 以 `cacheStatus` 揭露 live / cache / missing。
- `target_price.py` 在 `epsBasis=TTM` 且歷史 PE 有效樣本至少 12 筆時，使用 p25 / median / p75 作為 Bear / Base / Bull PE；否則只在 currentPE 可用時降級為 0.90x / 1.00x / 1.10x。單季 EPS 即使有完整歷史 PE 也不產生估值區間。
- Next.js「基本面 / 估值」tab 已顯示歷史 PE 五數摘要、樣本數、來源、cache 狀態與資料限制；系統產生的文案改稱「規則式估值區間」或「歷史 PE 估值參考」。
- 2330 真實 smoke test：歷史 PE 36 筆，min=14.04、p25=19.84、median=23.82、p75=26.88、max=32.23；但 FinMind EPS basis 仍為 `SINGLE_QUARTER`，因此 `targetPrice.valuationMethod=INSUFFICIENT_DATA`，沒有產生規則式估值區間。
- 驗證：FastAPI unittest 37/37、TypeScript 與 Next.js production build 通過。本次沒有修改部署設定、secrets、環境變數或套件版本，也尚未 commit、push 或部署。

## 2026-06-19 Target Price 與個人工具第一版（隔離分支）

- 工作分支：`codex/target-price-personal-tool-v1`；隔離 worktree：`.worktrees/codex-target-price-personal-tool-v1`。尚未 merge、push 或部署 production。
- FastAPI 新增獨立規則式 PE Multiple engine 與 top-level `targetPrice` 契約；只接受 forward、TTM 或可驗證近四季 EPS。外部 PE 才做獨立一致性檢查，推導 PE confidence 上限較低。
- 目標價成功時使用 `basePERatio = currentPE`、`bearPERatio = currentPE * 0.90`、`bullPERatio = currentPE * 1.10`；價格輸出為整數、upside 1 位、PE 1 至 2 位。
- Target Price Engine 不參與既有 Agent 評分。報告改為「結論、依據、風險、資料限制」，並揭露缺少歷史 PE、同業 PE、DCF 與法人一致性預估。
- Next.js 個股頁新增目標價摘要與估值 panel、「辯論室」及「決策筆記」tabs；筆記只存在瀏覽器 localStorage，不送後端。
- 2330 真實資料 smoke test：rating=`Buy / 看多`，EPS basis=`SINGLE_QUARTER`，PE source=`EXTERNAL`，target price=`INSUFFICIENT_DATA`；limitations 明確說明單季 EPS 不得直接產生正式 12M 目標價。
- 0000 資料不足 smoke test：rating=`Neutral / 中性`，target price=`INSUFFICIENT_DATA`，沒有目標價數字。
- 驗證：FastAPI unittest 28/28、TypeScript、Next.js production build 通過；Browser DOM/互動驗證通過摘要、基本面 fallback、辯論室與決策筆記保存/恢復，console 無錯誤。Browser screenshot 因 CDP timeout 未取得，行動 viewport override 未實際套用。

## 2026-06-19 Production End-to-End 驗收完成

- Vercel `multi-agent-tw-stock-dashboard-next` 於 17:36 完成 Ready production deployment，正式 URL 為 `https://multi-agent-tw-stock-dashboard-next.vercel.app`。
- 股票頁 bundle 由 `page-4238a3a731d4ebaf.js` 更新為 `page-0d0c11fd5317020c.js`，編譯的 API origin 已是 `https://multi-agent-stock-api.onrender.com`。
- 2330 正式頁面：籌碼總體為「最近可得官方資料」，官方資料缺口為 0；法人日期 2026-06-17，融資融券日期 2026-06-18。
- 8299 正式頁面：籌碼總體為「最近可得官方資料」，官方資料缺口為 0；法人與融資融券日期均為 2026-06-18。
- 原「官方資料缺失 / 日期未提供」問題已在正式資料流中解決；本次無需修改 repo 程式碼。

## 2026-06-19 Render Production Redeploy 驗證

- `https://multi-agent-stock-api.onrender.com/api/health` 回傳 status=`ok`、service=`multi-agent-stock-api`、version=`0.1.0`。
- 2330：institutional=`latest_available` / `2026-06-17` / `TWSE 三大法人買賣超日報`，margin=`latest_available` / `2026-06-18` / `TWSE 融資融券餘額`，overallStatus=`latest_available`，dataGaps=0。
- 8299：institutional=`latest_available` / `2026-06-18` / `TPEx 三大法人買賣明細`，margin=`latest_available` / `2026-06-18` / `TPEx 融資融券餘額`，overallStatus=`latest_available`，dataGaps=0。
- Render production 已部署新版 FastAPI，無需修改 repo 程式碼。
- 下一步是將 Vercel `multi-agent-tw-stock-dashboard-next` Production 的 `NEXT_PUBLIC_API_BASE_URL` 設為 `https://multi-agent-stock-api.onrender.com`，重新部署後進行正式網頁驗收。

## 2026-06-19 Production Backend 定位

- Render production FastAPI 服務名稱是 `multi-agent-stock-api`，origin 是 `https://multi-agent-stock-api.onrender.com`；另有 `multi-agent-stock-api-staging`。
- 兩個服務 `/api/health` 皆回傳 200、service=`multi-agent-stock-api`、version=`0.1.0`。
- Production `/api/analyze` 的 2330 / 8299 response 完全沒有 top-level `chipData`；staging 虽有 `chipData`，但缺少 `status` / `dataDate` / `overallStatus`。兩者均非 `f593ffc` 的新版 FastAPI。
- Render Dashboard 需要登入，本次未嘗試登入或觸發 redeploy。使用者需在 `multi-agent-stock-api` 確認 branch=`main`、root directory=`api`，然後執行 Deploy latest commit。
- `NEXT_PUBLIC_API_BASE_URL` 必須設為 backend origin `https://multi-agent-stock-api.onrender.com`，不可包含 `/api/analyze`，因為 `next-dashboard/lib/api.ts` 會自行附加 `/api/analyze` 與 `/api/health`。
- Vercel production alias 於 2026-06-19 17:01 有新 Ready deployment，但股票頁仍引用原 bundle hash，API base 未改；這次 redeploy 尚未修復資料流。

## 2026-06-19 新版 Production 驗證

- `main` 已在 `f593ffc` 整合籌碼修正；`multi-agent-tw-stock-dashboard-next` 已將該 commit 部署為 Ready production，正式驗收 URL 應使用 `https://multi-agent-tw-stock-dashboard-next.vercel.app`。
- 舊 `multi-agent-tw-stock-dashboard-live` 仍停在 `c78f149`，不用於本輪驗收。
- 新版前端公開 bundle 顯示 `/api/analyze` 實際指向 `https://multi-agent-stock-api-staging.onrender.com/api/analyze`。
- 該 staging backend 的 2330 / 8299 response 均缺少 institutional / margin `status`、`dataDate` 與 top-level `overallStatus`，確認仍為舊版 FastAPI。
- 新版 UI mapping 有正確顯示資料狀態、日期與總體 badge；目前 2330 / 8299 顯示「官方資料缺失」是因 backend 契約未升級，不是 repo 內前端 mapping 錯誤。
- 下一步需在部署平台部署新版 FastAPI，再將 `multi-agent-tw-stock-dashboard-next` Production 的 `NEXT_PUBLIC_API_BASE_URL` 改為該正式 backend origin。本次未修改程式碼或平台設定。

## 2026-06-19 受控自動修復排查

- 目前分支為 `fix/chip-data-latest-available`，HEAD `24efce8`，工作區乾淨且已與同名 remote branch 同步；`main` / `origin/main` 仍為 `c78f149`。
- 正式前端 `https://multi-agent-tw-stock-dashboard-live.vercel.app` 的當前 production 部署建立於 2026-06-14 14:44:45，與 `c78f149` 的提交時間及已編譯 UI 內容一致，未包含 6/18 籌碼修正。
- 正式前端的實際 request URL 為 `https://multi-agent-stock-api-staging.onrender.com/api/analyze`。該 backend 仍是舊版：2330 `chipData.margin` 沒有 `status` / `dataDate`，`overallStatus` 也未回傳，並以 `JSONDecodeError` 回傳 margin 資料缺口。
- 本機分支 E2E 對 2330 與 8299 均回傳 `overallStatus=latest_available`、margin `status=latest_available`、`dataDate=2026-06-18`、`dataGaps=0`。
- Fresh 驗證：FastAPI unittest 14/14 通過、TypeScript 通過、`npm run dev` 首頁 HTTP 200、`git diff --check` 通過。
- 本次沒有修改前後端程式碼、secrets、`.env` 或部署設定，也沒有 merge / push。需由使用者確認 production branch 與部署流程後才能處理。

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
