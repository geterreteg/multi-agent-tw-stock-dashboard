# 多 Agent 台股智慧分析儀表板：最新版 README 草案

本專案是財金資訊系統課程使用的台股研究儀表板。使用者輸入台股代號後，系統會整合股價、基本面、籌碼、風險與估值資料，並由規則式多 Agent 產生可追溯的分析結果。

目前正式主線是 FastAPI 後端加 Next.js 前端。根目錄 `app.py` 是 Streamlit legacy MVP，仍保留作為舊版展示與備援，不作為新版正式展示主線。

## 線上展示

新版正式前端：`https://multi-agent-tw-stock-dashboard-next.vercel.app`

後端 FastAPI production origin：`https://multi-agent-stock-api.onrender.com`

完整使用說明請見 `USER_GUIDE.md`。

## 主要功能

- 台股代號搜尋與個股研究頁。
- 綜合判斷、信心分數、資料缺口與資料品質狀態。
- 技術面：收盤價、MA20、MA60、20 日報酬率與短線動能。
- 基本面 / 估值：EPS、PE、營收成長、歷史 PE 與規則式估值區間。
- 籌碼與風險：三大法人、融資融券、官方資料日期與資料狀態。
- 辯論室：整理支持觀點、反方風險與決策整合。
- 決策筆記：使用瀏覽器 localStorage 保存個人筆記，不送到後端。
- 資料降級與 fallback：資料不足時明確顯示限制，不硬補結論。

## 專案架構

- `api/`：FastAPI 後端，新版主線。
- `next-dashboard/`：Next.js 前端，新版主線。
- `app.py`：Streamlit legacy MVP。
- `requirements.txt`：Streamlit legacy 依賴。
- `USER_GUIDE.md`：使用說明。
- `DEPLOYMENT.md`：部署說明。
- `PRODUCT_PLAN.md`：產品規劃。
- `tasks/`：專案狀態與交接紀錄。
- `plans/`：重大任務計畫文件。

## 資料來源

- TWSE / TPEx 官方資料：股價、三大法人、融資融券等公開資料。
- FinMind：基本面、財務與部分公開資料。
- yfinance：股價資料 fallback。

資料可能延遲、缺漏、限流、欄位格式改變或因網路不可用而降級。系統不宣稱資料完全即時。

## 本機執行概念

新版產品需要同時啟動 FastAPI 後端與 Next.js 前端。前端 API base URL 應指向後端 origin，不要包含 `/api/analyze`。詳細步驟請見 `USER_GUIDE.md`。

## Legacy Streamlit

若需要啟動舊版 Streamlit MVP，可使用根目錄 `app.py`。Streamlit legacy 與新版 FastAPI / Next.js 是不同路徑；若要展示新版正式產品，請使用 Next.js + FastAPI。

## 安全規範

- 不得提交私有環境設定、API key、token、密碼或 secrets。
- FinMind token 由系統管理者在環境變數或平台 Secrets 設定。
- 不得要求一般使用者在前端輸入 FinMind token。
- 不得在前端、log、README、報告、GitHub issue 或 commit message 顯示真實 token。
- 資料不足時必須顯示資料缺口，不得硬補數據、分數或估值。

## 不包含項目

- 不使用 OpenAI API。
- 不建立登入功能。
- 不建立真實交易功能。
- 不提供即時行情保證。
- 不宣稱分析結果是正式投資建議。

## 免責聲明

本系統分析結果僅供財金資訊系統課程、學術研究與投資參考，不構成任何買賣建議、獲利保證或專業投資顧問意見。投資人仍應自行評估風險，並自行承擔投資結果。
