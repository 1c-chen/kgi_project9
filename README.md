# Project 9 — Manager Coaching Intervention Portal

主管輔導介入系統，作為微學習平台的一部分，協助主管即時掌握員工學習狀況並進行介入輔導。

---

## 系統流程

```
員工學習卡關 → 系統鎖定模組 → 主管收到通知
→ 主管線下輔導 → 填寫紀錄解鎖 → 員工繼續學習
```

---

## 技術架構

| 層次 | 技術 |
|---|---|
| 後端框架 | FastAPI |
| 前端 | HTML + CSS + JS（Jinja2 模板） |
| 資料庫 | SQLite |
| ORM | SQLAlchemy |

---

## 快速啟動

### 1. 建立虛擬環境並安裝套件

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 初始化資料庫（含 Demo 假資料）

```bash
python seed.py
```

### 3. 啟動伺服器

```bash
uvicorn main:app --reload
```

打開瀏覽器前往 [http://localhost:8000](http://localhost:8000)

---

## Demo 假資料說明

| 員工 | 狀態 | 原因 |
|---|---|---|
| 王小明 | 🔴 紅（需介入） | MOD-001 連續失敗 3 次 |
| 吳建宏 | 🔴 紅（需介入） | MOD-002 7 日均分低於 70% |
| 李小花 | 🟡 黃（需注意） | MOD-002 連續失敗 2 次 |
| 張大偉 | 🟡 黃（需注意） | MOD-001 連續 3 次分數下滑 |
| 劉美玲 | 🟢 綠（正常） | — |
| 蔡佳穎 | 🟢 綠（正常） | — |
| 林志豪 | 🟢 綠（正常） | 無任何答題紀錄 |

重置資料：

```bash
python -c "from seed import reset; reset()"
```

---

## 核心業務邏輯

### 鎖定觸發條件（二擇一）

- **條件一**：同一模組連續失敗 3 次（最近 3 筆全部未通過）
- **條件二**：7 日滾動平均分數 < 70%（解鎖後累計 ≥ 5 筆才啟動，冷啟動保護）

### 預警機制（Amber）

- 最近 2 筆連續失敗 → 短期急性問題預警
- 最近 3 次分數連續下降 → 趨勢惡化預警

### 解鎖協議

主管填寫輔導紀錄（最低 20 字）並確認送出，模組自動解鎖，員工重新進入冷啟動保護期。

---

## 頁面說明

| 頁面 | 路由 | 說明 |
|---|---|---|
| 主頁面 | `/` | 主管帳號選擇入口 |
| Team Health Roster | `/roster/{manager_id}` | 直屬部屬清單與狀態總覽 |
| Diagnostic View | `/diagnostic/{agent_id}` | 員工詳細答題紀錄與 AI 建議 |
| Intervention Log | `/intervention/{lock_id}` | 填寫輔導紀錄並解鎖模組 |
| Demo 控制台 | `/demo` | 模擬員工答題觸發各種情境 |
