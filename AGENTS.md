# AGENTS.md

## 操作限制

禁止批量刪除文件或目錄。

不要使用：

- `del /s`
- `rd /s`
- `rmdir /s`
- `Remove-Item -Recurse`
- `rm -rf`

需要刪除文件時，只能一次刪除一個明確路徑的文件。

正確示範：

```powershell
Remove-Item "C:\path\to\file.txt"
```

如果需要批量刪除文件，應停止操作，並向用戶請求，讓用戶手動刪除。

## Codex CLI Documentation Editing

以後修改 Codex CLI 文檔時，不要直接覆蓋或刪改原文。

需要修改的原文應保留，並用刪除線標記；新增或替換內容用藍色文字標記。

適用於 Codex CLI 相關文檔、說明文字、README、教學文件與提交前的文檔草稿。

## Project Goal

建立可執行的 **多 Agent 台股智慧分析儀表板**。

使用者輸入台股代號後，系統使用 yfinance 抓 Yahoo Finance 歷史股價，使用 FinMind 抓台股基本面與籌碼資料，並由規則式多 Agent 產生辯論式 Markdown 投資分析報告。

## Data Sources

- yfinance：Open、High、Low、Close、Volume、MA20、MA60、20 日報酬率、平均成交量。
- FinMind：月營收、財務報表、EPS 或獲利指標、法人買賣超、融資融券、股利資料。

不得依賴 CSV 作為基本面與外資買賣超來源。舊版 `data/stock_data.csv` 已移除，正式資料來源必須為 yfinance 與 FinMind。

## Token Requirements

FinMind token 必須由系統管理者設定，不得要求一般使用者在前端輸入。

讀取順序：

1. Streamlit Secrets：`st.secrets["FINMIND_TOKEN"]`
2. 環境變數：`FINMIND_TOKEN`
3. `.env`
4. 若沒有 token，嘗試公開限制模式

token 不得被印出、顯示到前端或寫入報告。

前端只能顯示：

- `FinMind token 已由系統環境設定`
- `未偵測到 FinMind token，將嘗試公開限制模式`

## Constraints

- 不使用 OpenAI API。
- 不建立登入功能。
- 不建立真實交易功能。
- 不宣稱資料完全即時。
- 報告必須標示 yfinance 與 FinMind 來源。
- 報告必須說明資料可能延遲或不完整。
- 每份報告必須包含免責聲明。

## Agents

- Data Agent：整合 yfinance 與 FinMind 資料。某資料來源失敗時顯示清楚降級提示，不暴露 token，不讓 App 崩潰。
- 技術分析 Agent：使用 yfinance 股價、均線、成交量。
- 基本面 Agent：使用 FinMind 財報、月營收、EPS 或獲利資料。
- 籌碼分析 Agent：使用 FinMind 法人買賣超、融資融券。
- 風險控管 Agent：檢查跌破均線、短線漲幅過大、月營收衰退、EPS 不佳、法人賣超、融資增加但股價轉弱，並提出反方意見。
- 總結決策 Agent：整合結論為偏多、中立或偏空。

## Deployment Requirements

- 必須支援 Render 作為主要部署方式。
- 可支援 Streamlit Cloud。
- FinMind token 使用平台 Secrets、環境變數或 `.env`，不由使用者輸入。
- 不加入登入、交易、OpenAI API 或即時行情宣稱。

## Required Run Commands

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Required Disclaimer

本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。投資人仍應自行評估風險並承擔投資結果。

## General rules

- Use minimal, targeted changes.
- Do not refactor unrelated code.
- Do not rewrite large files unless necessary.
- Do not change unrelated UI, routes, API logic, environment variables, deployment settings, or package versions unless the task asks for it.
- Keep all user-facing UI text in Traditional Chinese.
- Do not invent data, scores, financial metrics, citations, or analysis results.
- Never commit secrets, API keys, tokens, `.env`, or private credentials.
- Prefer simple, maintainable solutions over clever or over-engineered ones.

## Task routing

Before acting, silently classify the task as S, M, or L.

S = text, style, copywriting, small UI, config typo, or one-file change.  
M = normal bug fix, small feature, UI section change, API field wiring, or limited multi-file change.  
L = build failure, deployment issue, data-flow issue, architecture change, security/privacy issue, investment scoring logic, or anything that may affect correctness across the app.

## Workflow

### S tasks

- Inspect only directly relevant files.
- Make the smallest safe change.
- Do not refactor.
- Do not run broad searches unless necessary.
- Verify with the narrowest reasonable check.

### M tasks

- Inspect relevant neighboring files.
- Make focused changes.
- Avoid unrelated cleanup.
- Run the relevant lint, typecheck, test, or build command if available.

### L tasks

- First understand the current architecture, data flow, or error path.
- Identify risks and assumptions before editing.
- Make a short plan before implementation.
- Implement in small steps.
- Verify with build, test, lint, or typecheck when available.
- If build/deployment fails, use the actual error message as the source of truth.
- Do not guess or make unrelated changes to silence errors.

## Investment analysis rules

- If data is missing or incomplete, clearly show the data gap.
- Do not fabricate confidence scores, ratings, financial numbers, or valuation conclusions.
- If evidence is weak, keep the recommendation neutral or conservative.
- Separate facts, assumptions, and model-generated judgments.
- Do not present generated analysis as professional investment advice.

## Verification rules

- Prefer existing project commands from `package.json`, README, or existing scripts.
- Do not introduce new dependencies unless necessary.
- Do not run long-lived dev servers unless explicitly needed.
- If verification cannot be completed, explain why.

## Final response

For Medium or Large tasks, include:

- Difficulty: S/M/L
- Files changed
- Verification performed
- Remaining risks

For very small tasks, use a concise summary instead of a fixed full format.
For small tasks, mention the files actually changed and any necessary verification.
Do not force every response into the complete fixed format when it would be unnecessary.
