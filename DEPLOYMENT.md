# Render 部署指南

本文件說明「多 Agent 台股智慧分析儀表板」如何在本機與 Render 部署。系統使用 Streamlit、yfinance、FinMind、python-dotenv 與規則式多 Agent 分析，不使用 OpenAI API、不建立登入、不提供真實交易功能，也不宣稱資料完全即時。

## 1. 本機執行方式

請先安裝 Python 依賴：

```bash
pip install -r requirements.txt
```

啟動 Streamlit：

```bash
python -m streamlit run app.py
```

本機可使用 `.env` 設定 FinMind token：

```bash
FINMIND_TOKEN=your_finmind_token_here
```

`.env` 僅供本機開發使用，不得提交到 GitHub。

## 2. Render 部署方式

在 Render 建立新的 Web Service：

1. 連接 GitHub repository。
2. 選擇本專案根目錄。
3. Runtime 選擇 Python。
4. Build Command 設定為：

```bash
pip install -r requirements.txt
```

5. Start Command 設定為：

```bash
python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

6. 在 Render 的 Environment Variables 設定：

```text
FINMIND_TOKEN=your_finmind_token_here
```

請注意：FinMind token 由系統管理者在 Render 後台設定，不由一般使用者輸入。

本專案也提供 `render.yaml`，Render 可用 Blueprint 方式讀取以下設定：

- Service Name：`multi-agent-tw-stock-dashboard`
- Runtime：Python
- Build Command：`pip install -r requirements.txt`
- Start Command：`python -m streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Environment Variable：`FINMIND_TOKEN`，由 Render 後台手動設定，不同步到 GitHub。

## 3. FinMind Token 安全

系統的 token 讀取順序如下：

1. Streamlit Secrets：`st.secrets["FINMIND_TOKEN"]`
2. 環境變數：`FINMIND_TOKEN`
3. `.env`
4. 若沒有 token，嘗試公開限制模式

Render 部署時主要使用環境變數 `FINMIND_TOKEN`。

前端只會顯示以下狀態：

- `FinMind token 已由系統環境設定`
- `未偵測到 FinMind token，將嘗試公開限制模式`

前端不得顯示 token 內容，log、README、PRODUCT_PLAN、AGENTS、DEPLOYMENT、GitHub 與 Markdown 報告也不得寫入真實 token。

## 4. GitHub 提交前檢查

請確認以下檔案不得提交：

- `.env`
- `.env.*`
- `.streamlit/secrets.toml`
- `__pycache__/`
- `*.pyc`
- `.venv/`
- `venv/`

`.env.example` 可以提交，內容只能使用範例值：

```bash
FINMIND_TOKEN=your_finmind_token_here
```

## 5. 資料與免責聲明

- yfinance 與 FinMind 資料可能延遲、缺漏或因權限限制而無法取得。
- 若 FinMind token 不存在，系統會嘗試公開限制模式，但部分資料可能無法完整顯示。
- 投資分析結果僅供學術研究與投資參考，不構成任何買賣建議。
- 投資人仍應自行評估風險並承擔投資結果。

## 6. 部署後驗證

部署完成後請檢查：

1. 首頁可正常載入。
2. Sidebar 沒有 token 輸入欄位。
3. Token 狀態只顯示安全提示，不顯示 token 內容。
4. 輸入台股代碼後可更新資料。
5. yfinance 或 FinMind 失敗時，畫面顯示友善降級提示。
6. 最終研究報告包含資料來源與免責聲明。
