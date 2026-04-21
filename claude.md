# Project 9 — Manager Coaching Intervention Portal
## 行動準則

---

## 專案背景

微學習平台的 Project 9，負責「主管介入輔導 Portal」，核心故事是：

> 員工學習卡關 → 系統鎖定模組 → 主管收到通知 → 主管線下輔導 → 填寫紀錄解鎖 → 員工繼續學習

---

## 技術架構

| 層次 | 技術 |
|---|---|
| 後端框架 | FastAPI |
| 前端 | HTML + CSS + JS（Jinja2 模板） |
| 資料庫 | SQLite |
| ORM | SQLAlchemy |

架構採單一 Server，FastAPI 同時負責 API 邏輯與回傳 HTML 頁面。

---

## 資料夾結構

```
kgi_project/
├── main.py              # 所有路由
├── database.py          # 資料庫連線設定（engine、SessionLocal、Base）
├── models.py            # 資料表定義（5 張表）
├── crud.py              # 資料庫操作邏輯
├── seed.py              # 假資料（含已觸發鎖定的員工）
├── requirements.txt     # 套件版本記錄，pip install -r requirements.txt 還原環境
├── portal.db            # SQLite 檔案（自動產生，勿手動編輯）
├── venv/                # 虛擬環境（勿提交 git）
└── templates/
    ├── index.html        # 主頁面（主管帳號選擇）
    ├── roster.html       # Team Health Roster
    ├── diagnostic.html   # Diagnostic View
    ├── intervention.html # Intervention Log Form
    └── demo.html         # Demo 控制台
```

---

## 資料表設計（5 張）

### 文件定義（3 張）
- `TeamStructures` — 組織架構，agent 與 manager 的對應關係
- `ModuleStateLocks` — 模組鎖定狀態，lock_reason 記錄觸發原因
- `CoachingInterventions` — 主管輔導紀錄，作為 audit trail

### 自行補充（2 張）
- `Users` — 共用帳號資料表，role 欄位用字串（'agent' / 'manager'），保留擴充彈性
- `QuizResults` — 答題紀錄，屬於 Project 1 負責維護，本專案只讀取

> Users 和 QuizResults 在真實系統中由其他模組維護，Project 9 只作為消費端。
> Demo 階段用 seed.py 填入假資料，未來替換資料來源不影響核心邏輯。

---

## 核心業務邏輯（3 個機制）

### 1. 觸發引擎（`check_and_lock`）
- 員工交卷後即時評估
- **條件一：同一模組連續失敗 3 次**（取最近 3 筆，全部 is_passed == False）
- **條件二：7 日滾動平均分數 < 70%**
  - 冷啟動保護：解鎖後累計答題筆數需 >= 5 筆才啟動，避免少量低分誤觸發
- 達到條件 → 在 `ModuleStateLocks` 新增鎖定紀錄，並寫入主管通知

### 2. 預警機制（`get_agent_status` → amber）
超出 spec 的補充設計，作為鎖定前的早警：
- **條件一：最近 2 筆連續失敗**（短期急性問題，連續 3 次鎖定的前置警告）
- **條件二：最近 3 次分數連續下降**（對應 spec 的「score dropping」敘述）
- 設計邏輯：條件一抓短期急性、條件二抓趨勢惡化，兩者互補

### 3. 通知路由
- 查 `TeamStructures` 找直屬主管
- Demo 階段：用資料庫內部通知紀錄代替真實 email/簡訊

### 4. 解鎖協議
- 員工進入模組前查詢鎖定狀態，有鎖則擋住作答
- 主管填寫輔導紀錄（最低 20 字驗證）並送出
- 寫入 `CoachingInterventions`，將 `is_locked` 改為 false
- 解鎖後，`_get_since()` 重新計算基準時間，員工重新進入冷啟動保護期

---

## 輔助函式（crud.py）

- **`_get_since(db, agent_id, module_id)`** — 取得該模組最近一次解鎖時間，作為所有條件的計算基準；無解鎖紀錄則回傳 epoch
- **`_build_attempt_details(db, attempts)`** — 將 QuizResult 列表轉換為 attempt_details（逐題展開）與 wrong_summary（跨測驗錯題統計，含所有答題，非僅失敗）

---

## 模組名稱對應（main.py `MODULE_NAMES`）

| module_id | 全名 |
|---|---|
| MOD-001 | MOD-001 旅遊保險資料共享規範 |
| MOD-002 | MOD-002 投資連結型保單（投連險）法規 |
| MOD-003 | MOD-003 FSC 個資保護條款 |

新增模組只需在 `main.py` 的 `MODULE_NAMES` dict 加一行。

---

## 前端頁面（4 頁）

### index.html — 主頁面
- 系統名稱：主管輔導介入系統
- Demo 用主管帳號選擇入口

### roster.html — Team Health Roster
- 主管的直屬部屬清單，附摘要統計（紅/黃/綠人數）
- 綠（健康）/ 黃（預警，可點入查看答題紀錄）/ 紅（模組鎖定，需介入）
- Header 左側：← 返回首頁；右側：頁面名稱 + 通知鈴鐺

### diagnostic.html — Diagnostic View
- 紅色員工：顯示鎖定模組、鎖定原因、答題紀錄（可展開逐題）、本鎖定週期錯題統計、AI 建議、填寫輔導紀錄按鈕
- 黃色員工：僅顯示各模組答題紀錄，無鎖定資訊與介入按鈕
- Header 左側：← 返回名單

### intervention.html — Intervention Log Form
- 輔導內容 textarea（最低 20 字驗證，即時字數顯示）
- 送出前彈出確認對話框
- 按鈕文字：「確認送出並簽核解鎖」（代替數位簽署）
- Header 左側：← 返回診斷頁

---

## Seed 資料（seed.py）

| 員工 | 狀態 | 觸發原因 |
|---|---|---|
| 王小明 | 紅 | MOD-001 連續失敗 3 次（45→50→40） |
| 吳建宏 | 紅 | MOD-002 7 日均分低於 70%（5 筆達冷啟動門檻） |
| 李小花 | 黃 | MOD-002 連續失敗 2 次（55→57） |
| 張大偉 | 黃 | MOD-001 連續 3 次下滑（80→74→68） |
| 劉美玲 | 綠 | 正常 |
| 蔡佳穎 | 綠 | 正常 |
| 林志豪 | 綠 | 無任何答題紀錄（冷啟動） |

重置指令：`python -c "from seed import reset; reset()"`

---

## 可簡化的部分

| 功能 | Demo 做法 |
|---|---|
| 真實通知（email） | 資料庫內部通知紀錄 |
| AI 生成回饋 | 靜態假文字 |
| 數位簽署 | 「確認送出並簽核解鎖」按鈕，說明可串接電子簽章服務 |
| 員工端完整介面 | 只做模擬答題按鈕（Demo 控制台） |

---

## 面試重點說明備忘

- 單一 Server 設計：「簡化 Demo，實際生產環境會前後端分離」
- Users/QuizResults 由其他模組維護：「Project 9 只作為消費端，設計保留模組邊界」
- Seed 假資料：「替換資料來源不影響核心邏輯，架構具備擴充彈性」
- 數位簽署簡化：「Demo 用確認按鈕代替，實際可串接電子簽章服務（如 Project 8）」
- 冷啟動保護：「避免少量資料誤觸發，amber 門檻 3 筆、lock 門檻 5 筆，刻意設計 buffer 讓 amber 比 lock 先觸發」
- Amber 預警：「spec 未要求，主動設計作為鎖定前的早警層，對應 score dropping 的業務語意」
- 連續 vs 累積：「選連續失敗而非累積，因為連續代表短期急性問題；7 日均分抓長期慢性問題，兩個條件互補」
