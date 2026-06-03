# 多 Agent 台股智慧分析儀表板

本專案是一個可執行的 Streamlit MVP。使用者輸入台股代號後，系統會整合 yfinance 與 FinMind 資料，並由規則式多 Agent 產生辯論式 Markdown 投資分析報告。

## 產品目標

- 協助財金資訊系統課程展示金融資料 API 整合、資料降級處理與多 Agent 規則推論。
- 讓使用者快速比較技術面、基本面、籌碼面與風險面。
- 產生可下載的 Markdown 分析報告，方便課堂展示與學術研究。

## 資料來源

- yfinance：Open、High、Low、Close、Volume、MA20、MA60、20 日報酬率、平均成交量。
- FinMind：台股基本資料、月營收、財務報表、EPS 或獲利指標、本益比、法人買賣超、融資融券、股利資料。


## FinMind Token

FinMind token 由系統管理者設定，不由使用者在前端輸入。

讀取順序：

1. Streamlit Secrets：`st.secrets["FINMIND_TOKEN"]`
2. 環境變數：`FINMIND_TOKEN`
3. `.env`
4. 若沒有 token，嘗試公開限制模式

前端只會顯示安全狀態，不會顯示 token 內容：

- `FinMind token 已由系統環境設定`
- `未偵測到 FinMind token，將嘗試公開限制模式`

## 多 Agent 分工

- Data Agent：整合 yfinance 與 FinMind。任一來源失敗時顯示降級提示，不讓 App 崩潰。
- 技術分析 Agent：使用 yfinance 股價、均線、成交量與 20 日報酬率。
- 基本面 Agent：使用 FinMind 月營收、財報、EPS 或獲利資料。
- 籌碼分析 Agent：使用 FinMind 法人買賣超與融資融券。
- 風險控管 Agent：提出反方意見，包含跌破均線、短線漲幅過大、月營收衰退、EPS 不佳、法人賣超、融資增加但股價轉弱、資料不足風險。
- 總結決策 Agent：輸出偏多、中立或偏空。

## 安裝與執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

如果 Streamlit 不在 PATH，可改用：

```bash
python -m streamlit run app.py
```

## 部署

部署方式請見 [DEPLOYMENT.md](DEPLOYMENT.md)。本專案以 Render 為主要部署目標，也可支援 Streamlit Cloud。

- Streamlit Cloud：將 `FINMIND_TOKEN` 設定在 App Secrets。
- Render：將 `FINMIND_TOKEN` 設定在 Environment Variables。
- 不應要求一般使用者輸入或管理 token。

## 限制

- 不使用 OpenAI API。
- 不建立登入功能。
- 不建立真實交易功能。
- 不宣稱資料完全即時。
- yfinance 不是 Yahoo Finance 官方 API。
- FinMind 資料可能受 token、權限、網路與更新時間影響。

## 免責聲明

本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。投資人仍應自行評估風險並承擔投資結果。
