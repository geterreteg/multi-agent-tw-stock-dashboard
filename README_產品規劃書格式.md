# 財金資訊系統開發 - 產品規劃書

# 多 Agent 台股智慧分析儀表板


### 1. 說明要解決什麼問題

一般投資人或學生在分析台股時，常常需要同時查詢股價、技術指標、基本面、籌碼面與風險資訊。這些資料分散在不同網站或資料來源中，使用者需要自己整理、比較與判斷，過程繁瑣且容易遺漏重點。

本系統希望解決以下問題：

- 股票資料來源分散，使用者需要在多個網站間切換。
- 一般使用者不一定知道該如何同時解讀技術面、基本面與籌碼面。
- 傳統查股工具多半只提供資料，不一定能整理成完整分析報告。
- 課堂展示需要一個可操作、可解釋、具財金資訊系統特色的 MVP。

### 2. 誰會使用這個系統

本系統的目標使用者包含：

- 財金資訊系統課程學生
- 想快速了解台股個股狀況的一般投資人
- 需要整理股票分析報告的初學者
- 想展示金融資料 API 整合與分析流程的課堂專題使用者

使用者不需要自行整理 CSV，也不需要在前端輸入 FinMind token。系統管理者會在部署環境中設定 token，讓使用者只需要輸入股票代碼即可使用。

### 3. 何需要這個系統

本系統的需求來自於「投資分析資訊整合」與「財金系統展示」兩個面向。

在投資分析上，使用者需要快速知道：

- 股價近期走勢如何
- 是否站上或跌破重要均線
- 基本面是否穩定
- 法人籌碼是否支持
- 是否存在追高、估值偏高或資料不足風險

在課程專題上，本系統可以展示：

- 金融資料 API 串接
- 資料清洗與降級處理
- 規則式多 Agent 分析
- Streamlit 互動式介面
- Markdown 投資研究報告產生
- 部署後的網頁化使用流程

### 4. 系統如何運作

使用者輸入台股股票代碼後，系統會自動整合 yfinance 與 FinMind 資料來源。

資料流程如下：

```text
使用者輸入股票代碼
        ↓
yfinance 抓取股價、成交量與歷史價格
        ↓
FinMind 抓取台股基本面、月營收、法人買賣超與融資融券資料
        ↓
Data Agent 整合資料並檢查缺漏
        ↓
技術分析 Agent、基本面 Agent、籌碼分析 Agent、風險控管 Agent 分別分析
        ↓
Agent 辯論與互評
        ↓
總結決策 Agent 產生偏多 / 中立 / 偏空結論
        ↓
輸出 Markdown 投資分析報告
```

### 5. 如何驗證系統有價值

本系統的價值可以從以下面向驗證：

- 使用者只需輸入股票代碼即可產生完整分析流程。
- 系統能整合股價、基本面、籌碼與風險資訊。
- 多 Agent 分工能讓分析邏輯更清楚，而不是只給單一結論。
- 當資料來源失敗或資料不足時，系統不會崩潰，而會顯示降級提示。
- 報告能下載並作為課堂展示或學術研究參考。
- 系統不依賴手動 CSV 補資料，更符合方便性與大眾使用需求。

### 6. MVP（Minimum Viable Product，最小可行產品）如何完成

本專案 MVP 以 Streamlit 網頁形式完成，核心功能如下：

| 功能模組 | MVP 內容 |
|---|---|
| 股票代碼輸入 | 使用者輸入台股代碼，例如 2330 |
| 股價資料更新 | 使用 yfinance 取得 Open、High、Low、Close、Volume |
| 技術指標計算 | 計算 MA20、MA60、20 日報酬率、平均成交量 |
| 基本面資料 | 使用 FinMind 取得月營收、財報、EPS 或獲利資料 |
| 籌碼資料 | 使用 FinMind 取得法人買賣超與融資融券資料 |
| 多 Agent 分析 | 技術、基本面、籌碼、風險與總結 Agent 分工分析 |
| Agent 辯論區 | 以對話方式呈現不同 Agent 的觀點與反方風險 |
| 報告產生 | 自動產生 Markdown 投資分析報告 |
| 錯誤降級 | API 失敗或資料不足時顯示提示，不讓 App 崩潰 |
| 部署支援 | 支援本機、Streamlit Cloud 與 Render 部署 |

---

## 二、產品背景與痛點

在財金資訊系統開發中，重點不是只有程式會跑，而是：

- 是否真正解決金融市場或使用者需求
- 是否有可取得的資料來源
- 是否有商業或研究價值
- 是否能被實際操作與展示

台股分析資料雖然公開，但對一般使用者而言仍然分散且難以快速整理。本系統透過 yfinance 與 FinMind 取得可更新資料，並用多 Agent 分工方式將資訊轉換成較容易理解的分析報告。

---

## 三、資料來源與資料限制

### 1. yfinance

用途：

- Open
- High
- Low
- Close
- Volume
- MA20
- MA60
- 20 日報酬率
- 平均成交量

限制：

- yfinance 不是 Yahoo Finance 官方 API。
- 資料可能延遲、不完整或因網路狀況失敗。
- 本系統不宣稱資料完全即時。

### 2. FinMind

用途：

- 台股基本資料
- 月營收
- 財務報表
- EPS 或獲利指標
- 本益比
- 法人買賣超
- 融資融券
- 股利資料

限制：

- FinMind 資料可能受 token、權限、網路與更新時間影響。
- 若沒有 token，系統會嘗試公開限制模式。
- 若資料無法取得，系統會顯示資料不足，不會讓 App 崩潰。

### 3. FinMind Token 設計

FinMind token 由系統管理者設定，不由一般使用者輸入。

讀取順序：

1. Streamlit Secrets：`st.secrets["FINMIND_TOKEN"]`
2. 環境變數：`FINMIND_TOKEN`
3. `.env`
4. 若沒有 token，嘗試公開限制模式

前端只會顯示 token 狀態，不會顯示 token 內容。

---

## 四、系統功能設計

### 1. 股票總覽 Dashboard

使用 `st.metric` 顯示：

- 最新收盤價
- 20 日報酬率
- 20 日均線
- 60 日均線
- EPS
- 本益比
- 月營收成長率
- 外資買賣超

若資料抓不到，顯示「資料暫無」，不直接報錯。

### 2. 圖表區

使用分頁呈現：

- 股價走勢
- 成交量
- 均線分析
- 法人籌碼
- 基本面資料

### 3. 多 Agent 分析區

- Data Agent：整合 yfinance 與 FinMind。
- 技術分析 Agent：分析股價、均線、成交量與報酬率。
- 基本面 Agent：分析月營收、EPS、本益比與財報資料。
- 籌碼分析 Agent：分析法人買賣超與融資融券。
- 風險控管 Agent：提出反方風險與資料不足風險。
- 總結決策 Agent：整合結論並輸出偏多、中立或偏空。

### 4. Agent 辯論區

系統不只顯示單一分析結論，而是讓不同 Agent 以對話方式呈現觀點。例如：

```text
技術分析 Agent：
目前股價站上均線，短線趨勢偏多。

基本面 Agent：
我同意趨勢改善，但若本益比偏高，仍需注意估值壓力。

籌碼分析 Agent：
法人近期買超，籌碼面支持短線動能。

風險控管 Agent：
我反對過度樂觀，若短線漲幅過大，可能有回檔風險。

總結決策 Agent：
綜合判斷為中立偏多，但不建議追高。
```

---

## 五、技術架構

| 項目 | 使用技術 |
|---|---|
| 前端與互動介面 | Streamlit |
| 股價資料 | yfinance |
| 台股基本面與籌碼資料 | FinMind |
| 環境變數管理 | python-dotenv、Streamlit Secrets |
| 分析邏輯 | 規則式多 Agent |
| 報告輸出 | Markdown |
| 部署 | Streamlit Cloud / Render |
| 開發輔助 | Codex subagents / 角色型 agent |

---

## 六、開發流程與 Codex 角色型 Agent

本專案在開發流程中導入 Codex subagents / 角色型 agent 分工概念，將工作拆分為：

- Product Planning Agent：產品規劃書與需求整理
- Data Integration Agent：yfinance、FinMind 與 token 管理
- Frontend Agent：Streamlit UI 與 Dashboard 呈現
- Analysis Agent：多 Agent 分析規則與報告邏輯
- Documentation Agent：README、AGENTS、DEPLOYMENT 文件
- QA Agent：測試錯誤處理、資料降級與 token 安全性

這樣可以讓專案不只是完成一個程式，而是以產品開發流程完成一個可展示的財金資訊系統 MVP。

---

## 七、安裝與執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

如果 Streamlit 不在 PATH，可改用：

```bash
python -m streamlit run app.py
```

---

## 八、部署方式

### Streamlit Cloud

- 將專案推到 GitHub。
- 在 Streamlit Cloud 建立 App。
- 在 App Secrets 加入：

```toml
FINMIND_TOKEN = "your_finmind_token_here"
```

### Render

Environment Variables 設定：

```text
FINMIND_TOKEN=your_finmind_token_here
```

Start Command：

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

---

## 九、風險與限制

- 本系統不使用 OpenAI API。
- 本系統不建立登入功能。
- 本系統不建立真實交易功能。
- 本系統不宣稱資料完全即時。
- yfinance 不是 Yahoo Finance 官方 API。
- FinMind 資料可能受 token、權限、網路與更新時間影響。
- 分析結果為規則式推論，不代表真實投資建議。
- 資料來源失敗時，系統會降級顯示，不保證所有指標都能取得。

---

## 十、預期價值

本系統能協助使用者以較低門檻取得台股個股分析，並將分散的市場資料整理成結構化報告。對課程專題而言，本系統能展示金融資料 API、Streamlit 視覺化、多 Agent 分析流程、錯誤處理與部署能力，符合財金資訊系統開發的實作與展示需求。

---

## 十一、免責聲明

本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。投資人仍應自行評估風險並承擔投資結果。
