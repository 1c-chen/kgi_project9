# Project 9 — Manager Coaching Intervention Portal

主管輔導介入系統，協助主管即時掌握員工學習狀況並進行介入輔導。

---

## 系統流程

```
員工學習卡關 → 系統鎖定模組 → 主管收到通知
→ 主管線下輔導 → 填寫紀錄解鎖 → 員工繼續學習
```

---

## 技術架構

- **後端**：FastAPI
- **前端**：HTML + CSS + JavaScript（Jinja2 模板）
- **資料庫**：SQLite + SQLAlchemy ORM

---

## 專案結構

```
kgi_project/
├── main.py          # 所有路由與頁面渲染
├── models.py        # 資料表定義（5 張）
├── crud.py          # 核心業務邏輯與資料庫操作
├── database.py      # 資料庫連線設定
├── seed.py          # Demo 假資料初始化
├── requirements.txt # 套件清單
└── templates/       # 前端頁面（5 頁）
    ├── index.html        # 主頁面
    ├── roster.html       # Team Health Roster
    ├── diagnostic.html   # Diagnostic View
    ├── intervention.html # Intervention Log
    └── demo.html         # Demo 控制台
```

---

## 快速啟動

```bash
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

打開瀏覽器前往 http://localhost:8000

---

## Demo 假資料

預設涵蓋三種學習狀態，共 7 名員工：

- 🔴 **紅（需介入）× 2** — 涵蓋兩種鎖定條件
- 🟡 **黃（需注意）× 2** — 涵蓋兩種預警條件
- 🟢 **綠（正常）× 3** — 含一名無答題紀錄的冷啟動情境

| 員工 | 狀態 | 原因 |
|---|---|---|
| 王小明 | 🔴 需介入 | MOD-001 連續失敗 3 次 |
| 吳建宏 | 🔴 需介入 | MOD-002 7 日均分低於 70% |
| 李小花 | 🟡 需注意 | MOD-002 連續失敗 2 次 |
| 張大偉 | 🟡 需注意 | MOD-001 連續 3 次分數下滑 |
| 劉美玲 | 🟢 正常 | — |
| 蔡佳穎 | 🟢 正常 | — |
| 林志豪 | 🟢 正常 | 無任何答題紀錄 |

---

## 核心業務邏輯

### 鎖定觸發條件（二擇一）

- **條件一**：同一模組連續失敗 3 次
- **條件二**：7 日滾動平均分數 < 70%（解鎖後累計 ≥ 5 筆才啟動，冷啟動保護）

### 預警機制（Amber）

- 最近 2 筆連續失敗 → 短期急性問題預警
- 最近 3 次分數連續下降 → 趨勢惡化預警

### 解鎖協議

主管填寫輔導紀錄（最低 20 字）並確認送出，模組自動解鎖，員工重新進入冷啟動保護期。
