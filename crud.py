from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import User, QuizResult, TeamStructure, ModuleStateLock, CoachingIntervention, Question, QuizAttemptAnswer, Notification


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# -------------------------------------------------------------------
# 狀態判斷輔助函式
# -------------------------------------------------------------------

def _get_since(db: Session, agent_id: int, module_id: str) -> datetime:
    """取得該模組最近一次解鎖時間，沒有則回傳 epoch。"""
    last_intervention = (
        db.query(CoachingIntervention)
        .join(ModuleStateLock, CoachingIntervention.lock_id == ModuleStateLock.lock_id)
        .filter(
            ModuleStateLock.agent_id == agent_id,
            ModuleStateLock.module_id == module_id
        )
        .order_by(CoachingIntervention.unlocked_timestamp.desc())
        .first()
    )
    return last_intervention.unlocked_timestamp if last_intervention else datetime(1970, 1, 1)


def get_agent_status(db: Session, agent_id: int) -> str:
    """
    回傳員工的顏色狀態：
      red   → 有任何模組處於鎖定中
      amber → 條件一：解鎖後最近 2 筆連續失敗（任一模組）
              條件二：解鎖後最近 3 次連續下降（任一模組）
      green → 正常
    """
    # 紅：有鎖定中的模組
    active_lock = db.query(ModuleStateLock).filter(
        ModuleStateLock.agent_id == agent_id,
        ModuleStateLock.is_locked == True
    ).first()
    if active_lock:
        return "red"

    module_ids = [
        row[0] for row in
        db.query(QuizResult.module_id)
        .filter(QuizResult.agent_id == agent_id)
        .distinct()
        .all()
    ]

    for mod_id in module_ids:
        since = _get_since(db, agent_id, mod_id)

        # 黃條件一：解鎖後最近 2 筆連續失敗
        recent_2 = (
            db.query(QuizResult)
            .filter(
                QuizResult.agent_id == agent_id,
                QuizResult.module_id == mod_id,
                QuizResult.taken_at > since
            )
            .order_by(QuizResult.taken_at.desc())
            .limit(2)
            .all()
        )
        if len(recent_2) == 2 and all(not r.is_passed for r in recent_2):
            return "amber"

        # 黃條件二：最近 3 次連續下降
        recent_3 = (
            db.query(QuizResult)
            .filter(
                QuizResult.agent_id == agent_id,
                QuizResult.module_id == mod_id,
                QuizResult.taken_at > since
            )
            .order_by(QuizResult.taken_at.desc())
            .limit(3)
            .all()
        )
        if len(recent_3) == 3 and recent_3[0].score < recent_3[1].score < recent_3[2].score:
            return "amber"

    return "green"


# -------------------------------------------------------------------
# Roster（團隊健康名單）
# -------------------------------------------------------------------

def get_team_roster(db: Session, manager_id: int) -> list:
    """
    取得主管的所有直屬部屬，附上顏色狀態。
    """
    team = db.query(TeamStructure).filter(
        TeamStructure.manager_id == manager_id
    ).all()

    roster = []
    for member in team:
        agent = db.query(User).filter(User.user_id == member.agent_id).first()
        status = get_agent_status(db, agent.user_id)
        roster.append({
            "agent_id": agent.user_id,
            "name": agent.name,
            "email": agent.email,
            "branch_code": agent.branch_code,
            "status": status
        })

    return roster


# -------------------------------------------------------------------
# Diagnostic（診斷詳情）
# -------------------------------------------------------------------

def _build_attempt_details(db: Session, attempts: list) -> tuple[list, list]:
    """將 QuizResult 列表轉換為 attempt_details 和 wrong_summary。"""
    wrong_counts: dict[int, dict] = {}
    attempt_details = []
    for attempt in attempts:
        wrong_rows = (
            db.query(QuizAttemptAnswer, Question)
            .join(Question, QuizAttemptAnswer.question_id == Question.question_id)
            .filter(
                QuizAttemptAnswer.result_id == attempt.result_id,
                QuizAttemptAnswer.is_correct == False
            )
            .all()
        )
        wrong_questions = []
        for _, question in wrong_rows:
            wrong_questions.append({
                "question_number": question.question_number,
                "content": question.content
            })
            if question.question_id not in wrong_counts:
                wrong_counts[question.question_id] = {
                    "question_number": question.question_number,
                    "content": question.content,
                    "count": 0
                }
            wrong_counts[question.question_id]["count"] += 1

        attempt_details.append({
            "score": attempt.score,
            "is_passed": attempt.is_passed,
            "taken_at": attempt.taken_at.strftime("%Y-%m-%d"),
            "wrong_questions": wrong_questions
        })

    wrong_summary = sorted(
        [{"question_number": v["question_number"], "content": v["content"], "count": v["count"]}
         for v in wrong_counts.values()],
        key=lambda x: (-x["count"], x["question_number"])
    )
    return attempt_details, wrong_summary


def get_diagnostic(db: Session, agent_id: int) -> dict:
    """
    取得員工的診斷詳情。
    紅色員工：鎖定原因、每次測驗的逐題錯誤、跨測驗錯題統計。
    黃色員工：各模組的答題紀錄（無鎖定資訊）。
    """
    agent = db.query(User).filter(User.user_id == agent_id).first()
    status = get_agent_status(db, agent_id)

    locks = db.query(ModuleStateLock).filter(
        ModuleStateLock.agent_id == agent_id,
        ModuleStateLock.is_locked == True
    ).all()

    lock_details = []
    for lock in locks:
        since = _get_since(db, agent_id, lock.module_id)

        if lock.lock_reason == "failed_3x":
            attempts = db.query(QuizResult).filter(
                QuizResult.agent_id == agent_id,
                QuizResult.module_id == lock.module_id,
                QuizResult.is_passed == False,
                QuizResult.taken_at > since
            ).order_by(QuizResult.taken_at).all()
        else:  # avg_below_70
            seven_days_ago = now_utc() - timedelta(days=7)
            attempts = db.query(QuizResult).filter(
                QuizResult.agent_id == agent_id,
                QuizResult.module_id == lock.module_id,
                QuizResult.taken_at >= seven_days_ago,
                QuizResult.taken_at > since
            ).order_by(QuizResult.taken_at).all()

        attempt_details, wrong_summary = _build_attempt_details(db, attempts)

        lock_details.append({
            "lock_id": lock.lock_id,
            "module_id": lock.module_id,
            "lock_reason": lock.lock_reason,
            "locked_timestamp": lock.locked_timestamp.strftime("%Y-%m-%d %H:%M"),
            "attempts": attempt_details,
            "wrong_summary": wrong_summary,
            "ai_feedback": f"建議針對「{lock.module_id}」相關法規條文進行重點複習，尤其是資料共享與隱私保護的實務案例。"
        })

    # Amber：顯示各模組的解鎖後答題紀錄
    amber_details = []
    if status == "amber":
        module_ids = [
            row[0] for row in
            db.query(QuizResult.module_id)
            .filter(QuizResult.agent_id == agent_id)
            .distinct()
            .all()
        ]
        for mod_id in module_ids:
            since = _get_since(db, agent_id, mod_id)
            attempts = db.query(QuizResult).filter(
                QuizResult.agent_id == agent_id,
                QuizResult.module_id == mod_id,
                QuizResult.taken_at > since
            ).order_by(QuizResult.taken_at).all()
            if not attempts:
                continue
            attempt_details, _ = _build_attempt_details(db, attempts)
            amber_details.append({
                "module_id": mod_id,
                "attempts": attempt_details
            })

    return {
        "agent_id": agent.user_id,
        "name": agent.name,
        "status": status,
        "lock_details": lock_details,
        "amber_details": amber_details
    }


# -------------------------------------------------------------------
# Trigger Engine（觸發引擎）
# -------------------------------------------------------------------

def check_and_lock(db: Session, agent_id: int, module_id: str) -> str | None:
    """
    評估是否需要鎖定模組，回傳鎖定原因或 None。
    條件一：同一模組失敗 >= 3 次
    條件二：7 日滾動平均分數 < 70%
    """
    # 已經鎖定就不重複處理
    existing_lock = db.query(ModuleStateLock).filter(
        ModuleStateLock.agent_id == agent_id,
        ModuleStateLock.module_id == module_id,
        ModuleStateLock.is_locked == True
    ).first()
    if existing_lock:
        return None

    # 取得最近一次解鎖時間，只計算解鎖後的紀錄
    since = _get_since(db, agent_id, module_id)

    # 條件一：解鎖後最近 3 筆連續失敗
    recent_3 = (
        db.query(QuizResult)
        .filter(
            QuizResult.agent_id == agent_id,
            QuizResult.module_id == module_id,
            QuizResult.taken_at > since
        )
        .order_by(QuizResult.taken_at.desc())
        .limit(3)
        .all()
    )

    if len(recent_3) == 3 and all(not r.is_passed for r in recent_3):
        lock = ModuleStateLock(
            agent_id=agent_id,
            module_id=module_id,
            lock_reason="failed_3x",
            is_locked=True
        )
        db.add(lock)
        db.flush()
        _write_notification(db, agent_id, lock.lock_id)
        db.commit()
        return "failed_3x"

    # 條件二：解鎖後累計 >= 4 筆，且 7 日滾動均分 < 70%（冷啟動保護）
    total_since = db.query(QuizResult).filter(
        QuizResult.agent_id == agent_id,
        QuizResult.module_id == module_id,
        QuizResult.taken_at > since
    ).count()

    seven_days_ago = now_utc() - timedelta(days=7)
    results = db.query(QuizResult).filter(
        QuizResult.agent_id == agent_id,
        QuizResult.module_id == module_id,
        QuizResult.taken_at >= seven_days_ago,
        QuizResult.taken_at > since
    ).all()

    if total_since >= 5 and results:
        avg_score = sum(r.score for r in results) / len(results)
        if avg_score < 70:
            lock = ModuleStateLock(
                agent_id=agent_id,
                module_id=module_id,
                lock_reason="avg_below_70",
                is_locked=True
            )
            db.add(lock)
            db.flush()
            _write_notification(db, agent_id, lock.lock_id)
            db.commit()
            return "avg_below_70"

    return None


def _write_notification(db: Session, agent_id: int, lock_id: int):
    """找直屬主管並寫入通知。"""
    team = db.query(TeamStructure).filter(TeamStructure.agent_id == agent_id).first()
    if team:
        db.add(Notification(
            manager_id=team.manager_id,
            agent_id=agent_id,
            lock_id=lock_id
        ))


def submit_quiz(db: Session, agent_id: int, module_id: str, score: float, days_ago: int = 0) -> dict:
    """
    記錄答題結果，並觸發鎖定引擎。
    若模組已鎖定，拒絕作答。
    days_ago: 模擬幾天前作答（Demo 用）
    """
    existing_lock = db.query(ModuleStateLock).filter(
        ModuleStateLock.agent_id == agent_id,
        ModuleStateLock.module_id == module_id,
        ModuleStateLock.is_locked == True
    ).first()

    if existing_lock:
        return {
            "score": None,
            "is_passed": False,
            "lock_triggered": None,
            "error": "模組已鎖定，需主管介入後才能繼續作答"
        }

    is_passed = score >= 60
    taken_at = now_utc() - timedelta(days=days_ago)
    result = QuizResult(
        agent_id=agent_id,
        module_id=module_id,
        score=score,
        is_passed=is_passed,
        taken_at=taken_at
    )
    db.add(result)
    db.flush()  # 取得 result_id

    # 自動分配錯題（依分數決定錯幾題，依作答次數循環偏移）
    questions = (
        db.query(Question)
        .filter(Question.module_id == module_id)
        .order_by(Question.question_number)
        .all()
    )
    if questions:
        wrong_count = min(round((100 - score) / 20), len(questions))
        wrong_count = max(wrong_count, 0)
        attempt_num = db.query(QuizResult).filter(
            QuizResult.agent_id == agent_id,
            QuizResult.module_id == module_id,
            QuizResult.result_id != result.result_id
        ).count()
        n = len(questions)
        for i, q in enumerate(questions):
            is_correct = ((i - attempt_num) % n) >= wrong_count
            db.add(QuizAttemptAnswer(
                result_id=result.result_id,
                question_id=q.question_id,
                is_correct=is_correct
            ))

    db.commit()

    lock_reason = check_and_lock(db, agent_id, module_id)

    return {
        "score": score,
        "is_passed": is_passed,
        "lock_triggered": lock_reason,
        "error": None
    }


# -------------------------------------------------------------------
# Unlock Protocol（解鎖協議）
# -------------------------------------------------------------------

def unlock_module(db: Session, lock_id: int, manager_id: int, notes: str) -> dict:
    """
    主管填寫輔導紀錄後解鎖模組。
    """
    lock = db.query(ModuleStateLock).filter(
        ModuleStateLock.lock_id == lock_id
    ).first()

    if not lock or not lock.is_locked:
        return {"success": False, "message": "找不到鎖定紀錄或模組已解鎖"}

    # 寫入輔導紀錄
    intervention = CoachingIntervention(
        lock_id=lock_id,
        manager_id=manager_id,
        manager_notes_text=notes,
        unlocked_timestamp=now_utc()
    )
    db.add(intervention)

    # 解鎖
    lock.is_locked = False
    db.commit()

    return {"success": True, "message": f"模組 {lock.module_id} 已解鎖"}


# -------------------------------------------------------------------
# Notifications（通知）
# -------------------------------------------------------------------

def get_unread_notifications(db: Session, manager_id: int) -> list:
    rows = (
        db.query(Notification, User, ModuleStateLock)
        .join(User, Notification.agent_id == User.user_id)
        .join(ModuleStateLock, Notification.lock_id == ModuleStateLock.lock_id)
        .filter(
            Notification.manager_id == manager_id,
            Notification.is_read == False
        )
        .order_by(Notification.created_at.desc())
        .all()
    )
    return [
        {
            "notification_id": n.notification_id,
            "agent_name": u.name,
            "module_id": lock.module_id,
            "lock_reason": lock.lock_reason,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for n, u, lock in rows
    ]


def mark_notifications_read(db: Session, manager_id: int):
    db.query(Notification).filter(
        Notification.manager_id == manager_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()