# Project 9 — Manager Coaching Intervention Portal

主管輔導介入系統，協助主管即時掌握員工學習狀況並進行介入輔導。

## 系統流程

```
員工學習卡關 → 系統鎖定模組 → 主管收到通知
→ 主管線下輔導 → 填寫紀錄解鎖 → 員工繼續學習
```

## 技術架構

- 後端：FastAPI
- 前端：HTML + CSS + JS（Jinja2 模板）
- 資料庫：SQLite + SQLAlchemy

## 專案結構

```
kgi_project/
├── main.py          # 所有路由
├── models.py        # 資料表定義
├── crud.py          # 資料庫操作邏輯
├── database.py      # 資料庫連線設定
├── seed.py          # Demo 假資料
├── requirements.txt # 套件清單
└── templates/       # 前端頁面（5 頁）
```

## 快速啟動

```bash
# 安裝套件
pip install -r requirements.txt

# 初始化資料庫
python seed.py

# 啟動伺服器
uvicorn main:app --reload
```

打開瀏覽器前往 http://localhost:8000
