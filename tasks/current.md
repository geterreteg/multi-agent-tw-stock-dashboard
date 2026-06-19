# 目前專案狀態

## 專案目標

建立可執行的多 Agent 台股智慧分析儀表板。使用者輸入台股代號後，系統整合股價、基本面與籌碼資料，由規則式 Agent 產生技術面、基本面、籌碼面、風險面與總結決策，並輸出包含資料來源、資料限制與免責聲明的 Markdown 報告。

本專案用於財金資訊系統課程與學術研究展示，不使用 OpenAI API、不提供登入、不提供真實交易，也不宣稱資料完全即時。

## 目前架構

專案目前同時存在三條應用路徑：

1. **Streamlit legacy 應用**：根目錄 `app.py`，搭配根目錄 `requirements.txt` 與 `render.yaml`。
2. **FastAPI 後端**：`api/main.py` 提供 `/api/health` 與 `/api/analyze`，分析、Agent、報告與資料服務集中在 `api/app/`。
3. **Next.js 前端**：`next-dashboard/` 使用 Next.js 15、React 19、TypeScript、Tailwind CSS 與 Recharts，透過 `NEXT_PUBLIC_API_BASE_URL` 呼叫 FastAPI。

README、DEPLOYMENT 與 PRODUCT_PLAN 主要描述 Streamlit 架構；FastAPI / Next.js 是 repo 中已存在的新版架構。未來以哪一條作為單一正式產品主線，**待使用者確認**。

## 主要資料夾與用途

- `api/app/routers/`：FastAPI 路由，包含健康檢查、分析與可選的 debug 端點。
- `api/app/services/`：市場資料、法人、融資融券、分析 context、Agent 評分與 Markdown 報告。
- `api/tests/`：FastAPI 資料流程回歸測試；目前工作區含籌碼資料狀態與 fallback 測試。
- `next-dashboard/app/`：Next.js 頁面與路由，包含首頁、個股分析與尚未完整實作的預留頁面。
- `next-dashboard/components/`：搜尋、個股分析、圖表、狀態卡與共用 UI 元件。
- `next-dashboard/lib/`：FastAPI client、TypeScript 資料型別、格式化與共用工具。
- `reports/`：報告範例。
- `data/`：目錄存在，但正式基本面與外資資料不得依賴 CSV。
- `tasks/`：當前狀態與跨聊天視窗交接文件。
- `plans/`：L 級任務或重大專案決策的計畫文件。

## 目前部署狀態

- 根目錄 `render.yaml` 定義 Streamlit Render Web Service，啟動指令為 `python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0`。
- `api/render.yaml` 定義 FastAPI Render Web Service，啟動指令為 `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`。
- 新版正式前端為 `https://multi-agent-tw-stock-dashboard-next.vercel.app`，production deployment 對應 `f593ffc` 且狀態為 Ready。舊 `https://multi-agent-tw-stock-dashboard-live.vercel.app` 仍為 `c78f149` 舊版，不用於新版籌碼驗收。
- Render FastAPI production 服務為 `multi-agent-stock-api`，origin 為 `https://multi-agent-stock-api.onrender.com`。2026-06-19 redeploy 後 `/api/health` 為 200 / `0.1.0`；2330 與 8299 皆已回傳完整新版 `chipData`、`overallStatus=latest_available`且 `dataGaps=0`。
- `multi-agent-tw-stock-dashboard-next` 於 2026-06-19 17:36 完成 Ready production deployment，新 bundle 已編譯 `https://multi-agent-stock-api.onrender.com`。2330 / 8299 正式頁面皆已顯示「最近可得官方資料」，官方資料缺口為 0。

## 資料來源與外部服務限制

- Streamlit legacy：股價使用 yfinance，基本面與籌碼使用 FinMind。
- FastAPI 現行程式：股價優先使用 TWSE / TPEx 官方日 K，可降級使用 yfinance；基本面使用 FinMind。
- `main` 已於 `f593ffc` 整合 `fix/chip-data-latest-available`，FastAPI 籌碼分析已統一為 TWSE / TPEx 官方 `chipData`，FinMind 的兩個籌碼 dataset 已從 FastAPI 主動請求清單移出。
- FinMind token 不得由一般使用者輸入，不得顯示、列印、寫入報告或提交到 Git。
- 無 FinMind token 時會嘗試公開限制模式，資料完整度可能下降。
- yfinance 不是 Yahoo Finance 官方 API。
- TWSE、TPEx、FinMind 與 yfinance 的資料都可能延遲、缺漏、限流、改變欄位格式或因網路而不可用。

## UI / UX 方向

- 台灣使用者可見文字維持繁體中文。
- Next.js 主線採用產品化的台股研究儀表板，首頁提供股票搜尋，個股頁分開技術、基本面、籌碼與風險、總結等資訊層級。
- UI 應顯示資料來源、實際資料日期、降級狀態、空狀態、錯誤狀態與免責聲明。
- 不得將靜態示範文字當成真實市場結論，不得編造數據、分數或投資結果。
- 不做無關頁面重設；UI 修改前需先給出簡短產品設計計畫。

## 目前已知限制

- 目前 `main` 已包含 `f593ffc` 與後續文件提交。Render production FastAPI 與 Vercel Production API base 皆已升級，2330 / 8299 正式資料流驗收通過。
- TWSE 融資 parser 已支援 `代號` / `股票代號` / `證券代號`；2330 真實官方 API smoke test 已確認 margin 不再誤判為 `missing`。
- `chipData.overallStatus` 已由後端依 institutional / margin 狀態合併為 `current` / `latest_available` / `partial` / `missing`，前端直接顯示該欄位。
- 風險控管的融資壓力扣分已套用 `current=1.0` / `latest_available=0.75` / `missing=0.0` 狀態權重。
- `app.py` 仍是使用 FinMind 籌碼的獨立 legacy 流程，而根目錄 Render 設定仍會啟動此 Streamlit 應用。
- FastAPI `main.py` 的 description 仍稱為 mock backend，但 `/api/analyze` 已呼叫實際分析服務。
- README、DEPLOYMENT、PRODUCT_PLAN、AGENTS 內的資料源描述以 Streamlit / FinMind 籌碼為主，與分支中 FastAPI 官方籌碼方向存在差異。
- 部分 Next.js 頁面是 placeholder，實際產品範圍與優先順序**待確認**。

## 常用開發與驗證指令

### Streamlit legacy

```powershell
pip install -r requirements.txt
python -m streamlit run app.py
```

### FastAPI

```powershell
Set-Location api
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
python -m unittest discover -s tests -p "test_*.py" -v
```

### Next.js

```powershell
Set-Location next-dashboard
npm.cmd ci
npm.cmd run dev
npm.cmd exec tsc -- --noEmit --incremental false
npm.cmd run build
```

`npm.cmd run lint` 雖定義在 `package.json`，但 Next.js 15 環境下是否可直接執行，**待確認**。不要在未確認必要性時啟動長時間開發伺服器或全專案建置。

## 目前待辦

1. `codex/target-price-personal-tool-v1` 已完成第一版規則式 Target Price Engine、研究報告語氣、辯論室與 localStorage 決策筆記；尚未 merge、push 或部署 production。
2. 目前 FinMind 財報一般 EPS 欄位只能保守辨識為單季 EPS。2330 實測因此回傳 `INSUFFICIENT_DATA`，未產生無法追溯的 12M 目標價。
3. 未來若要提高估值覆蓋率，需加入可驗證的 forward / TTM EPS，或能明確區分單季與累計口徑的近四季 EPS；歷史 PE、同業 PE、DCF 與法人一致性預估仍未納入。
4. 確認 Streamlit legacy、FastAPI 與 Next.js 何者是未來正式主線，以及是否要讓 `app.py` 也改用官方籌碼資料。
5. 以正式文件規則更新 README、DEPLOYMENT、PRODUCT_PLAN 與必要的專案規則。

## 不能亂改的地方

- 不得提交 `.env`、token、API key、密碼、Secrets 或私有設定。
- 未經明確要求，不修改 `render.yaml`、`api/render.yaml`、Vercel 設定、環境變數、CORS、CI/CD 或套件版本。
- 不得要求一般使用者在前端輸入 FinMind token，不得暴露 token 內容。
- 不使用 CSV 當作正式基本面或外資買賣超來源。
- 投資評分、資料狀態、日期 fallback、資料來源與報告免責聲明屬正確性關鍵邏輯，修改前需追蹤完整資料流並使用測試驗證。
- 不要為了一個頁面或單一資料問題重構無關檔案、頁面、API、部署或設計系統。
- `targetPrice` 只作為規則式估值參考，不得單獨加入 Agent 分數或主導最終評級；`INSUFFICIENT_DATA` 不得硬補目標價。
- 不能批量刪除檔案或目錄；需刪除時只能一次處理一個明確檔案。
- 正式文件修訂需遵守 `AGENTS.md` 的保留原文與變更標記規則。
