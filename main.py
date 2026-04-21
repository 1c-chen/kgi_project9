from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base
import crud

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# -------------------------------------------------------------------
# 首頁：導向 Demo 用的主管登入選擇
# -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# -------------------------------------------------------------------
# Team Health Roster（團隊健康名單）
# -------------------------------------------------------------------

@app.get("/roster/{manager_id}", response_class=HTMLResponse)
def roster(manager_id: int, request: Request, db: Session = Depends(get_db)):
    team = crud.get_team_roster(db, manager_id)
    notifications = crud.get_unread_notifications(db, manager_id)
    return templates.TemplateResponse(request, "roster.html", {
        "manager_id": manager_id,
        "team": team,
        "notifications": notifications
    })


# -------------------------------------------------------------------
# Diagnostic View（診斷詳情）
# -------------------------------------------------------------------

MODULE_NAMES = {
    "MOD-001": "MOD-001 旅遊保險資料共享規範",
    "MOD-002": "MOD-002 投資連結型保單（投連險）法規",
    "MOD-003": "MOD-003 FSC 個資保護條款",
}

@app.get("/diagnostic/{agent_id}", response_class=HTMLResponse)
def diagnostic(agent_id: int, manager_id: int, request: Request, db: Session = Depends(get_db)):
    data = crud.get_diagnostic(db, agent_id)
    return templates.TemplateResponse(request, "diagnostic.html", {
        "manager_id": manager_id,
        "data": data,
        "module_names": MODULE_NAMES
    })


# -------------------------------------------------------------------
# Intervention Form（輔導紀錄表單）
# -------------------------------------------------------------------

@app.get("/intervention/{lock_id}", response_class=HTMLResponse)
def intervention_form(lock_id: int, manager_id: int, agent_id: int, request: Request, db: Session = Depends(get_db)):
    data = crud.get_diagnostic(db, agent_id)
    return templates.TemplateResponse(request, "intervention.html", {
        "lock_id": lock_id,
        "manager_id": manager_id,
        "agent_id": agent_id,
        "data": data
    })


@app.post("/intervention/{lock_id}")
def intervention_submit(
    lock_id: int,
    manager_id: int = Form(...),
    notes: str = Form(...),
    db: Session = Depends(get_db)
):
    if len(notes.strip()) < 20:
        raise HTTPException(status_code=400, detail="輔導紀錄至少需要 20 個字")

    result = crud.unlock_module(db, lock_id, manager_id, notes)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return RedirectResponse(url=f"/roster/{manager_id}", status_code=303)


# -------------------------------------------------------------------
# Demo 控制台
# -------------------------------------------------------------------

@app.get("/demo", response_class=HTMLResponse)
def demo_panel(request: Request, db: Session = Depends(get_db)):
    from models import User
    agents   = db.query(User).filter(User.role == "agent").all()
    managers = db.query(User).filter(User.role == "manager").all()
    status_list = [
        {**a.__dict__, "status": crud.get_agent_status(db, a.user_id)}
        for a in agents
    ]
    return templates.TemplateResponse(request, "demo.html", {
        "agents": agents,
        "managers": managers,
        "status_list": status_list
    })


# -------------------------------------------------------------------
# 重置資料庫（Demo 用）
# -------------------------------------------------------------------

@app.post("/api/reset")
def reset_db():
    from seed import reset
    reset()
    return {"message": "資料庫已重置"}


# -------------------------------------------------------------------
# 模擬答題（Demo 用：觸發鎖定流程）
# -------------------------------------------------------------------

@app.post("/api/notifications/read/{manager_id}")
def mark_notifications_read(manager_id: int, db: Session = Depends(get_db)):
    crud.mark_notifications_read(db, manager_id)
    return {"success": True}


@app.post("/api/quiz/submit")
def submit_quiz(
    agent_id: int = Form(...),
    module_id: str = Form(...),
    score: float = Form(...),
    days_ago: int = Form(0),
    db: Session = Depends(get_db)
):
    result = crud.submit_quiz(db, agent_id, module_id, score, days_ago)
    return result


@app.post("/api/quiz/batch")
def submit_quiz_batch(payload: list[dict], db: Session = Depends(get_db)):
    results = []
    for item in payload:
        r = crud.submit_quiz(
            db,
            agent_id=item["agent_id"],
            module_id=item["module_id"],
            score=item["score"],
            days_ago=item.get("days_ago", 0)
        )
        results.append(r)
    return results