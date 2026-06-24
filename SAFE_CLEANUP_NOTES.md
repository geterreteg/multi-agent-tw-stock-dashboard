# 安全清理紀錄

本次採取保守清理策略，只處理文件整理，不刪除或修改可能影響專案執行的檔案。

## 判定結果

沒有刪除任何 runtime、部署、測試、環境範例或交接相關檔案。

原因是以下檔案雖然看起來屬於舊版或輔助用途，但仍可能被展示、部署、交接或回歸驗證使用：

- `app.py`
- 根目錄 `requirements.txt`
- 根目錄 `render.yaml`
- `api/render.yaml`
- `api/`
- `next-dashboard/`
- `tasks/`
- `plans/`
- `.env.example` 類範例檔
- 測試檔與型別檔

## 已安全處理

- `README.md`：已更新為新版 FastAPI + Next.js 主線說明。
- `USER_GUIDE.md`：已新增最新版使用說明。
- `README_LATEST.md`：已完成推廣到 `README.md`，並刪除臨時草案檔，避免重複文件。

## 建議後續

若要真的刪除 legacy Streamlit 路徑，應先確認：

1. 正式展示只使用 Next.js + FastAPI。
2. Render 不再使用根目錄 Streamlit 設定。
3. 課堂報告與老師要求不再需要 Streamlit MVP。
4. 本機與線上驗證都已通過。

在上述條件未確認前，不建議刪除 legacy 檔案。
