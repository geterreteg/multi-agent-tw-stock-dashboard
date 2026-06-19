# Target Price Personal Tool V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在保留現有 FastAPI + Next.js 報告展示流程下，加入可驗證 EPS 門檻的規則式目標價、研究報告語氣、辯論室與瀏覽器端決策筆記。

**Architecture:** 後端以 `target_price.py` 封裝純估值規則，市場資料服務只負責產生具來源的 EPS / PE metadata，分析服務把估值結果以新增 API 欄位傳給報告與前端。前端以三個小元件接入既有研究 tabs，舊 response 缺少 `targetPrice` 時維持降級相容。

**Tech Stack:** Python 3、FastAPI、Pydantic、pandas、unittest、Next.js 15、React 19、TypeScript、Tailwind CSS、瀏覽器 localStorage。

---

### Task 1: EPS metadata 與 Target Price Engine

**Files:**
- Create: `api/app/services/target_price.py`
- Create: `api/tests/test_target_price.py`
- Modify: `api/app/services/market_data.py`
- Modify: `api/app/services/analysis.py`

- [ ] **Step 1: 寫入失敗測試，定義估值輸入與成功結果**

建立 `test_target_price.py`，以 `EpsEvidence` 與 `build_target_price()` 的期望介面測試：外部 PE 一致時產生整數 Bear/Base/Bull、1 位小數 upside、正確公式與 confidence 65。

- [ ] **Step 2: 執行紅燈測試**

Run: `python -m unittest tests.test_target_price.TargetPriceEngineTests.test_external_pe_builds_rule_based_range -v`

Expected: FAIL，因 `app.services.target_price` 尚不存在。

- [ ] **Step 3: 實作最小估值資料結構與成功路徑**

在 `target_price.py` 定義 immutable `EpsEvidence`，欄位為 `basis`、`value`、`source`、`periods`；`basis` 只接受 `FORWARD`、`TTM`、`FOUR_QUARTERS`、`SINGLE_QUARTER`、`UNAVAILABLE`。定義 `build_target_price(current_price, eps, current_pe, pe_source, has_valuation_gaps=False) -> TargetPriceResult`，其中 `pe_source` 只接受 `EXTERNAL`、`DERIVED`、`UNAVAILABLE`。

計算時保留原始精度，建立 response 前才套用價格整數、upside 1 位及 PE 2 位小數格式。

- [ ] **Step 4: 加入資料不足與 PE 來源測試**

測試單季 EPS、負 EPS、缺少價格、外部 PE 超過 10% 誤差、推導 PE 不做循環驗證、推導 PE confidence 60、估值缺口 confidence 50。

- [ ] **Step 5: 執行紅燈並完成最小 fallback 邏輯**

Run: `python -m unittest tests.test_target_price -v`

Expected before implementation: 新增案例 FAIL；完成後全部 PASS。

- [ ] **Step 6: 以失敗測試驅動 FinMind EPS metadata**

新增 `FinancialSummaryTests`，用具明確 `date` / `type` / `value` 的 dataframe 驗證：只有四個可辨識季度才回傳 `FOUR_QUARTERS`；最新單季只回傳 `SINGLE_QUARTER`；無法辨識期別回傳 `UNAVAILABLE`。不得把現行最新一筆 EPS 當成 TTM。

- [ ] **Step 7: 實作 `summarize_financials()` 結構化結果並接入 context**

保留舊 `metrics.eps` 顯示值，同時在 `StockContext` 加入 `eps_basis`、`eps_source`、`eps_periods` 與 `pe_source`。FinMind PER 欄位標為 `EXTERNAL`；缺少 PER 時讓 engine 決定是否標記 `DERIVED`。

- [ ] **Step 8: 執行目標價測試與既有回歸測試**

Run: `python -m unittest tests.test_target_price -v`

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

Expected: 全部 PASS。

### Task 2: API 契約、評級隔離與報告語氣

**Files:**
- Modify: `api/app/models.py`
- Modify: `api/app/services/analysis.py`
- Modify: `api/app/services/agents.py`
- Modify: `api/app/services/reports.py`
- Modify: `api/app/services/mock_data.py`
- Modify: `api/tests/test_target_price.py`
- Modify: `api/tests/test_chip_data_flow.py`

- [ ] **Step 1: 寫入 API 契約與評級隔離失敗測試**

測試 `AnalyzeResponse.targetPrice` 欄位完整；`INSUFFICIENT_DATA` response 仍保留既有 rating；Target Price Engine 不被 agents scoring function 呼叫或計入分數。

- [ ] **Step 2: 執行紅燈測試**

Run: `python -m unittest tests.test_target_price.TargetPriceApiTests -v`

Expected: FAIL，因模型尚無 `targetPrice`。

- [ ] **Step 3: 新增 Pydantic 契約並接入分析成功與失敗 response**

新增 `TargetPrice` model 與 `DebateMessage.evidenceTags`、`DebateMessage.role`。`analyze_symbol()` 在 agents 評分完成前後均不得用目標價改寫 rating；只把結果傳給報告與辯論組裝。

- [ ] **Step 4: 寫入研究語氣與限制揭露失敗測試**

測試 Markdown 包含「結論、依據、風險、資料限制」、固定 PE Multiple 揭露、格式一致的 Bear/Base/Bull；不足時包含「資料不足，暫不產生正式 12M 目標價」且沒有虛構數字。

- [ ] **Step 5: 執行紅燈並重組報告文字**

Run: `python -m unittest tests.test_target_price.TargetPriceReportTests -v`

Expected before implementation: FAIL；更新 `agents.py` 與 `reports.py` 後 PASS。

- [ ] **Step 6: 擴充規則式辯論訊息**

以既有 agents、research report、target price 與 limitations 組成主持人、估值分析師、基本面分析師、技術面分析師、籌碼分析師、風控主管、反方分析師。每則訊息只引用既有 evidence 或限制文字。

- [ ] **Step 7: 更新 mock 與 fallback response**

Mock 可用明確標記的 TTM EPS 產生可追溯展示資料；failed response 固定回傳 `INSUFFICIENT_DATA`。不改 production 資料來源與設定。

- [ ] **Step 8: 執行後端完整回歸**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

Expected: 全部 PASS，既有 14 個籌碼測試仍通過。

### Task 3: 前端型別與格式化核心

**Files:**
- Modify: `next-dashboard/lib/types.ts`
- Create: `next-dashboard/lib/target-price.ts`
- Create: `next-dashboard/components/stocks/target-price-panel.tsx`
- Modify: `next-dashboard/components/stocks/stock-analysis-client.tsx`

- [ ] **Step 1: 先擴充型別並讓 TypeScript 暴露未實作引用**

新增 `TargetPrice`、擴充 `DebateMessage`，在既有 client 引用尚未建立的 `TargetPricePanel` 與格式化 helpers。

- [ ] **Step 2: 執行 TypeScript 紅燈**

Run: `npm.cmd exec tsc -- --noEmit --incremental false`

Expected: FAIL，找不到 target price module/component。

- [ ] **Step 3: 實作共用格式化與目標價元件**

`target-price.ts` 統一：台股價格整數、upside 1 位、PE 1 至 2 位；`TargetPricePanel` 顯示 Bear/Base/Bull、EPS basis、PE source、confidence、assumptions、limitations 與固定揭露。`INSUFFICIENT_DATA` 顯示指定 fallback。

- [ ] **Step 4: 接入摘要與基本面 / 估值 tab**

摘要只增加一張規則式目標價卡；基本面 tab 使用完整 panel。缺少 top-level `targetPrice` 的舊 response 轉成 client-side insufficient fallback。

- [ ] **Step 5: 執行 TypeScript 綠燈**

Run: `npm.cmd exec tsc -- --noEmit --incremental false`

Expected: PASS。

### Task 4: 辯論室與決策筆記

**Files:**
- Create: `next-dashboard/components/stocks/debate-room.tsx`
- Create: `next-dashboard/components/stocks/decision-notes.tsx`
- Modify: `next-dashboard/components/stocks/stock-analysis-client.tsx`

- [ ] **Step 1: 新增元件引用並執行 TypeScript 紅燈**

在 tabs union 與 builder 新增 `debate` / `notes`，引用尚未建立元件。

Run: `npm.cmd exec tsc -- --noEmit --incremental false`

Expected: FAIL，找不到元件。

- [ ] **Step 2: 實作 `DebateRoom`**

以暖白聊天泡泡顯示 role、stance、content 與 evidence tags；不得在前端推導新投資數字。空陣列顯示資料不足狀態。

- [ ] **Step 3: 實作 `DecisionNotes`**

使用 `tw-stock-decision-note:${symbol}` key；欄位符合設計，提供儲存與清除，顯示「僅儲存在此瀏覽器」。localStorage 例外時保留當前 state 並顯示無法持久保存。

- [ ] **Step 4: 將特殊 tab panel 接入既有 `StructuredResearchReport`**

保留原本 tabs 與圖表分支，只有 `debate` / `notes` 使用自訂 panel。

- [ ] **Step 5: 執行 TypeScript 綠燈**

Run: `npm.cmd exec tsc -- --noEmit --incremental false`

Expected: PASS。

### Task 5: 完整驗證與專案狀態

**Files:**
- Modify: `tasks/current.md`
- Modify: `tasks/handoff.md`

- [ ] **Step 1: 執行後端完整測試**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

- [ ] **Step 2: 執行 TypeScript 與 production build**

Run: `npm.cmd exec tsc -- --noEmit --incremental false`

Run: `npm.cmd run build`

- [ ] **Step 3: 執行 2330 與資料不足 smoke test**

直接呼叫 `analyze_symbol("2330", "6mo")`，輸出 valuationMethod、epsBasis、peSource 與 limitations；另以單季 EPS fixture 驗證 `INSUFFICIENT_DATA`。不得為通過展示而修改真實結果。

- [ ] **Step 4: 驗證既有展示流程與格式**

檢查 Markdown 仍含資料來源、Agent、免責聲明；確認目標價整數、upside 1 位、PE 1 至 2 位；確認 target price 未進入評分公式。

- [ ] **Step 5: 更新狀態與交接文件**

在 `tasks/current.md` 記錄新契約、限制與驗證結果；在 `tasks/handoff.md` 頂部新增本次有意義工作階段摘要。不得記錄 secrets、內部 token 或 production 設定值。

- [ ] **Step 6: 最終差異與敏感資訊檢查**

Run: `git diff --check`

Run: `git status --short`

Run: `git diff --name-only`

確認未修改 deployment、env、secrets、套件版本或 unrelated code。
