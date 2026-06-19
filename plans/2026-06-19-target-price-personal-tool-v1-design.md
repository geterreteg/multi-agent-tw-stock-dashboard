# 個人投資工具第一版設計

## 目標與範圍

本次以現有 FastAPI + Next.js 展示流程為主線，在不重做首頁、不改部署設定、不新增登入與資料庫的前提下，加入可展示、可回退、可延伸的個人投資工具第一版。

本次範圍包含：

- 保留既有多 Agent 報告與 Markdown 報告。
- 新增 12M 規則式目標價與估值參考區間。
- 將結論文案整理為機構研究報告式的「結論、依據、風險、資料限制」。
- 新增投資委員會形式的「辯論室」tab。
- 新增以瀏覽器 `localStorage` 保存的「決策筆記」tab。

本次不做：完整持股系統、登入、後端筆記儲存、資料庫重構、付費 API、歷史 PE 資料庫、同業比較、DCF、法人一致性預估、部署或 production API 設定變更。

## 架構決策

採用平衡模組化方案：

1. FastAPI 新增獨立 `target_price.py`，只負責 EPS 口徑、PE 來源、估值門檻與三情境計算。
2. 現有市場資料服務回傳結構化 EPS 與 PE metadata，舊有 `metrics.eps`、`metrics.peRatio` 保留以維持相容性。
3. `AnalyzeResponse` 新增 top-level `targetPrice`，讓摘要、基本面估值、報告與辯論共用同一份估值結果。
4. Next.js 新增目標價、辯論室與決策筆記小元件，由既有個股分析頁組裝，不重寫搜尋、圖表、籌碼或路由流程。

## EPS 口徑

### 優先順序

1. `forwardEPS`
2. `ttmEPS`
3. 最近四季 EPS 合計
4. 只有單季 EPS 時，不產生正式 12M 規則式目標價

### 可驗證條件

- forward EPS 必須有明確欄位或來源標記，不從單季 EPS 猜測。
- TTM EPS 必須有明確 TTM 欄位或可確認為連續十二個月資料。
- 最近四季合計必須由四個可辨識、互不重複且具期別的季度 EPS 組成。
- 若來源是累計 EPS，必須先可靠轉換為單季 EPS；無法辨識累計或單季口徑時，不得湊成四季合計。
- 現有 `summarize_financials()` 只取最新 EPS，不能證明是 TTM；改版前的該值一律不得直接用於目標價。
- 若只有單季 EPS，`baseTargetPrice = null`、`valuationMethod = "INSUFFICIENT_DATA"`，並在 `limitations` 說明原因。

## PE 來源與一致性

`currentPE` 必須帶有來源分類：

- `EXTERNAL`：來自 FinMind PER 等外部原始欄位。
- `DERIVED`：由 `currentPrice / epsUsed` 推導。
- `UNAVAILABLE`：沒有可使用的 PE。

一致性規則：

- `EXTERNAL`：以 `currentPrice / epsUsed` 計算 implied PE，與外部 `currentPE` 做合理誤差檢查。第一版容許相對誤差為 10%，以吸收價格日期與財報更新時間差。超過門檻即回傳 `INSUFFICIENT_DATA`，不得產生目標價。
- `DERIVED`：不得把 `currentPrice / epsUsed` 與同一公式推導的 `currentPE` 比較並宣稱為獨立驗證。此情境可產生規則式估值區間，但 confidence 上限較低，且 assumptions / limitations 必須揭露缺少外部 PE 佐證。
- `UNAVAILABLE`：若 current price 與 EPS 皆有效，可推導 `currentPE` 並標記為 `DERIVED`；否則回傳 `INSUFFICIENT_DATA`。
- EPS 必須大於 0，current price 與 current PE 必須為有效正數；否則不得使用 PE Multiple 法。

## Target Price Engine

### 計算公式

在 EPS 口徑通過門檻後：

```text
basePERatio = currentPE
bearPERatio = currentPE * 0.90
bullPERatio = currentPE * 1.10

baseTargetPrice = epsUsed * basePERatio
bearTargetPrice = epsUsed * bearPERatio
bullTargetPrice = epsUsed * bullPERatio
impliedUpsidePct = (baseTargetPrice / currentPrice - 1) * 100
```

第一版固定使用 10% 折價與 10% 溢價，不將其描述為市場統計區間。

### API 輸出

`targetPrice` 至少包含：

- `currentPrice`
- `baseTargetPrice`
- `bearTargetPrice`
- `bullTargetPrice`
- `impliedUpsidePct`
- `valuationMethod`
- `epsBasis`
- `epsUsed`
- `fairPERatio`
- `bearPERatio`
- `bullPERatio`
- `confidence`
- `assumptions`
- `limitations`

另加入 `peSource`，讓前端與報告能區分外部 PE 與推導 PE。`fairPERatio` 與 `basePERatio` 語意相同，API 依使用者要求保留欄位名 `fairPERatio`。

成功時 `valuationMethod = "RULE_BASED_PE_MULTIPLE"`；失敗時 `valuationMethod = "INSUFFICIENT_DATA"`，所有目標價欄位為 `null`。

### 命名與揭露

所有使用者可見位置只稱為「規則式目標價」或「估值參考區間」。不得稱為法人共識目標價、正式投顧目標價或完整合理價。

固定揭露文案：

> 本目標價採規則式 PE Multiple 法，以目前可驗證本益比作為 Base Case 估值基準，並以固定折溢價建立 Bear / Bull 情境。由於尚未納入歷史 PE 區間、同業估值、DCF 與法人一致性預估，本目標價應視為估值參考區間，而非正式法人目標價。

### Confidence 分層

- EPS 為 forward / TTM / 近四季合計，且外部 PE 通過口徑一致性檢查：最高 65。
- EPS 可用，但 PE 僅由 current price / EPS 推導、沒有外部 PE 佐證：最高 60。
- 非核心資料缺口影響估值解讀但仍通過正式計算門檻：最高 50。
- EPS 口徑不足：`INSUFFICIENT_DATA`，不產生正式 confidence；API 使用 0 表示未形成估值信心。

第一版 confidence 是資料覆蓋與口徑可信度，不是上漲機率或模型命中率。

## 研究報告語氣

現有評分與事實不改，只重組表達：

1. **結論**：評級、規則式目標價狀態與評級強度限制。
2. **依據**：價格、均線、營收、EPS、估值與籌碼等已取得證據。
3. **風險**：現有 risk agent 與反方觀點，不新增未取得數字。
4. **資料限制**：EPS / PE 口徑、資料延遲、缺少歷史 PE、同業 PE、DCF 與法人一致性預估。

Markdown 報告保留原有資料來源、Agent 區段與免責聲明，並加入規則式估值區間章節。現有前端摘要也採同一結構，避免 API 與 UI 使用不同結論。

## 辯論室

辯論室使用暖白金融產品風格的聊天泡泡，不做娛樂化角色扮演。每則訊息包含：

- `role`：主持人、估值分析師、基本面分析師、技術面分析師、籌碼分析師、風控主管、反方分析師。
- `stance`：支持、保留、反方或共識等立場。
- `content`：只根據 API 已取得事實與 Target Price Engine 結果。
- `evidenceTags`：引用已存在的價格、均線、EPS、PE、營收、法人、融資或資料缺口文字。

後端擴充現有 `debate` 契約，不另建生成式服務。主持人負責開場與共識；估值分析師說明目標價假設或資料不足；反方分析師引用 `variantView` 與 `risks`；其餘角色映射現有 Agent。若估值不足，辯論內容必須直接說明不產生正式 12M 目標價。

## 決策筆記

第一版為 client-side UI，欄位包含：

- 我的動作：觀察 / 買進 / 持有 / 減碼 / 賣出
- 投資假說
- 目標價
- 停損條件
- 看錯條件
- 追蹤重點
- 備註

以股票代號作為 `localStorage` key 的一部分，瀏覽器載入後恢復內容。儲存狀態需提示「僅儲存在此瀏覽器」，不得暗示已同步雲端。目標價為使用者筆記欄位，不自動覆寫規則式目標價，也不送往後端。

## 前端整合

- 摘要區：新增規則式目標價卡；資料不足時顯示「資料不足，暫不產生正式 12M 目標價」。
- 基本面 / 估值：新增 Bear / Base / Bull 卡片、EPS basis、PE source、confidence、assumptions 與 limitations。
- 辯論室：新增獨立 tab，呈現投資委員會訊息串與 evidence tags。
- 決策筆記：新增獨立 tab，呈現表單、儲存與清除單筆股票筆記功能。
- 既有摘要、技術面、基本面、籌碼風險、總結與圖表流程保留。

## 錯誤與降級

- Target Price Engine 不得使 `/api/analyze` 失敗；資料不足時回傳結構完整的 `INSUFFICIENT_DATA`。
- 任何無法辨識的 EPS 口徑皆視為不足，不猜測、不補值。
- PE 外部口徑不一致時，limitations 同時說明外部 PE 與 price / EPS 無法合理核對。
- 前端必須對缺少 `targetPrice` 的舊版後端相容，顯示 fallback 而非崩潰。
- localStorage 不可用時，決策筆記仍可在當前頁面編輯，並提示無法持久保存。

## 測試與驗收

### 後端單元與契約測試

- forward / TTM / 近四季 EPS 成功案例。
- 單季 EPS 回傳 `INSUFFICIENT_DATA`。
- 外部 PE 一致性通過與超過誤差門檻案例。
- 推導 PE 不被宣稱為獨立驗證，confidence 上限為 60。
- 估值資料缺口時 confidence 上限為 50。
- 無效價格、負 EPS、無法辨識 EPS 期別皆不得產生目標價。
- API `targetPrice` 契約、Markdown 報告結構與限制揭露。
- 既有報告、籌碼與失敗 fallback 測試維持通過。

### 前端驗收

- TypeScript 檢查。
- production build 在成本合理且環境可用時執行。
- 2330 顯示成功估值或明確說明 EPS 口徑不足，不因示範需求硬算。
- 一檔資料不足股票顯示 fallback，沒有虛構目標價。
- 辯論室角色、立場、內容與 evidence tags 完整。
- 決策筆記可依股票代號保存與恢復。
- 原本搜尋、個股報告 tabs、圖表、籌碼資料與 Markdown 報告流程未損壞。

## 回退與相容性

實作前基線為 `main` commit `94a6812`，工作區乾淨。新功能以新增欄位與元件為主，不移除舊 API 欄位；舊前端或缺少 `targetPrice` 的 response 仍可降級顯示。部署設定、環境變數、production API 與 secrets 不在修改範圍。
