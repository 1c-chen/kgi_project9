from database import engine, SessionLocal
from models import Base, User, QuizResult, TeamStructure, ModuleStateLock, CoachingIntervention, Question, QuizAttemptAnswer, Notification
from datetime import datetime, timedelta, timezone


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def reset():
    """清空所有資料，重新填入初始 seed 資料。"""
    db = SessionLocal()
    db.query(CoachingIntervention).delete()
    db.query(Notification).delete()
    db.query(QuizAttemptAnswer).delete()
    db.query(ModuleStateLock).delete()
    db.query(QuizResult).delete()
    db.query(Question).delete()
    db.query(TeamStructure).delete()
    db.query(User).delete()
    db.commit()
    db.close()
    seed(force=True)


def seed(force=False):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    if not force and db.query(User).first():
        print("資料庫已有資料，跳過 seed。")
        db.close()
        return

    # -------------------------------------------------------------------
    # 1. Users
    # -------------------------------------------------------------------
    manager1 = User(name="陳志明", email="manager1@kgi.com", role="manager", branch_code="TPE-Nangang")
    manager2 = User(name="林雅惠", email="manager2@kgi.com", role="manager", branch_code="TPE-Xinyi")

    agent_red    = User(name="王小明", email="agent1@kgi.com", role="agent", branch_code="TPE-Nangang")
    agent_amber  = User(name="李小花", email="agent2@kgi.com", role="agent", branch_code="TPE-Nangang")
    agent_green1 = User(name="張大偉", email="agent3@kgi.com", role="agent", branch_code="TPE-Nangang")
    agent_green2 = User(name="劉美玲", email="agent4@kgi.com", role="agent", branch_code="TPE-Nangang")
    agent_red2   = User(name="吳建宏", email="agent5@kgi.com", role="agent", branch_code="TPE-Xinyi")
    agent_green3 = User(name="蔡佳穎", email="agent6@kgi.com", role="agent", branch_code="TPE-Xinyi")
    agent_new    = User(name="林志豪", email="agent7@kgi.com", role="agent", branch_code="TPE-Nangang")

    db.add_all([manager1, manager2, agent_red, agent_amber, agent_green1, agent_green2, agent_red2, agent_green3, agent_new])
    db.commit()

    # -------------------------------------------------------------------
    # 2. TeamStructures
    # -------------------------------------------------------------------
    db.add_all([
        TeamStructure(agent_id=agent_red.user_id,    manager_id=manager1.user_id, branch_code="TPE-Nangang"),
        TeamStructure(agent_id=agent_amber.user_id,  manager_id=manager1.user_id, branch_code="TPE-Nangang"),
        TeamStructure(agent_id=agent_green1.user_id, manager_id=manager1.user_id, branch_code="TPE-Nangang"),
        TeamStructure(agent_id=agent_green2.user_id, manager_id=manager1.user_id, branch_code="TPE-Nangang"),
        TeamStructure(agent_id=agent_red2.user_id,   manager_id=manager2.user_id, branch_code="TPE-Xinyi"),
        TeamStructure(agent_id=agent_green3.user_id, manager_id=manager2.user_id, branch_code="TPE-Xinyi"),
        TeamStructure(agent_id=agent_new.user_id,    manager_id=manager1.user_id, branch_code="TPE-Nangang"),
    ])
    db.commit()

    # -------------------------------------------------------------------
    # 3. Questions（每模組 5 題）
    # -------------------------------------------------------------------
    q001_1 = Question(module_id="MOD-001", question_number=1, content="依旅遊保險資料共享規範，以下哪項個人資料共享需取得客戶「明示同意」？")
    q001_2 = Question(module_id="MOD-001", question_number=2, content="旅遊保險業者向合作夥伴共享資料時，審查申請期限為幾個工作天？")
    q001_3 = Question(module_id="MOD-001", question_number=3, content="以下何種情形可依規定豁免資料共享的同意要求？")
    q001_4 = Question(module_id="MOD-001", question_number=4, content="跨境資料傳輸須經哪個監管機關核准方可執行？")
    q001_5 = Question(module_id="MOD-001", question_number=5, content="資料共享相關紀錄依規定至少需保存幾年以備查核？")

    q002_1 = Question(module_id="MOD-002", question_number=1, content="投資連結型保單（投連險）最低年繳保費門檻依法規定為何？")
    q002_2 = Question(module_id="MOD-002", question_number=2, content="以下哪項投資標的依法不得納入投連險商品架構？")
    q002_3 = Question(module_id="MOD-002", question_number=3, content="推介投連險商品前，業務員必須持有哪項主管機關核准的資格認證？")
    q002_4 = Question(module_id="MOD-002", question_number=4, content="投連險說明書中，法規要求揭露的風險項目不包含哪項？")
    q002_5 = Question(module_id="MOD-002", question_number=5, content="客戶完成投連險簽約後，法定猶豫期（冷靜期）為幾天？")

    q003_1 = Question(module_id="MOD-003", question_number=1, content="依 FSC 個資保護條款，金融機構保存客戶個資的法定最長期限為幾年？")
    q003_2 = Question(module_id="MOD-003", question_number=2, content="哪種情況下金融機構必須事前提交「個資保護影響評估（DPIA）」？")
    q003_3 = Question(module_id="MOD-003", question_number=3, content="個資外洩事件發生後，需在幾小時內向 FSC 提出通報？")
    q003_4 = Question(module_id="MOD-003", question_number=4, content="以下哪種情況下，業務員可合法使用客戶個人資料？")
    q003_5 = Question(module_id="MOD-003", question_number=5, content="客戶提出資料刪除申請後，金融機構需在幾個工作天內完成處理？")

    db.add_all([
        q001_1, q001_2, q001_3, q001_4, q001_5,
        q002_1, q002_2, q002_3, q002_4, q002_5,
        q003_1, q003_2, q003_3, q003_4, q003_5,
    ])
    db.commit()

    # -------------------------------------------------------------------
    # 4. QuizResults（保留物件參照以便後續建立 QuizAttemptAnswers）
    # -------------------------------------------------------------------
    now = now_utc()

    # 王小明（紅）：MOD-001 連續失敗 3 次
    qr_r1 = QuizResult(agent_id=agent_red.user_id, module_id="MOD-001", score=45, is_passed=False, taken_at=now - timedelta(days=7))
    qr_r2 = QuizResult(agent_id=agent_red.user_id, module_id="MOD-001", score=50, is_passed=False, taken_at=now - timedelta(days=5))
    qr_r3 = QuizResult(agent_id=agent_red.user_id, module_id="MOD-001", score=40, is_passed=False, taken_at=now - timedelta(days=2))
    qr_r4 = QuizResult(agent_id=agent_red.user_id, module_id="MOD-003", score=80, is_passed=True,  taken_at=now - timedelta(days=3))

    # 李小花（黃）：MOD-002 失敗 2 次
    qr_a1 = QuizResult(agent_id=agent_amber.user_id, module_id="MOD-002", score=55, is_passed=False, taken_at=now - timedelta(days=6))
    qr_a2 = QuizResult(agent_id=agent_amber.user_id, module_id="MOD-002", score=57, is_passed=False, taken_at=now - timedelta(days=3))
    qr_a3 = QuizResult(agent_id=agent_amber.user_id, module_id="MOD-003", score=75, is_passed=True,  taken_at=now - timedelta(days=4))

    # 張大偉（黃）：MOD-001 連續 3 次下滑
    qr_g1_1 = QuizResult(agent_id=agent_green1.user_id, module_id="MOD-001", score=80, is_passed=True, taken_at=now - timedelta(days=6))
    qr_g1_2 = QuizResult(agent_id=agent_green1.user_id, module_id="MOD-001", score=74, is_passed=True, taken_at=now - timedelta(days=3))
    qr_g1_3 = QuizResult(agent_id=agent_green1.user_id, module_id="MOD-001", score=68, is_passed=True, taken_at=now - timedelta(days=1))

    # 劉美玲（綠）
    qr_g2_1 = QuizResult(agent_id=agent_green2.user_id, module_id="MOD-001", score=78, is_passed=True, taken_at=now - timedelta(days=4))
    qr_g2_2 = QuizResult(agent_id=agent_green2.user_id, module_id="MOD-003", score=88, is_passed=True, taken_at=now - timedelta(days=2))

    # 吳建宏（紅）：7 日均分低於 70%（5 筆達冷啟動門檻）
    qr_r2_1 = QuizResult(agent_id=agent_red2.user_id, module_id="MOD-002", score=55, is_passed=False, taken_at=now - timedelta(days=7))
    qr_r2_2 = QuizResult(agent_id=agent_red2.user_id, module_id="MOD-002", score=60, is_passed=True,  taken_at=now - timedelta(days=6))
    qr_r2_3 = QuizResult(agent_id=agent_red2.user_id, module_id="MOD-002", score=58, is_passed=False, taken_at=now - timedelta(days=4))
    qr_r2_4 = QuizResult(agent_id=agent_red2.user_id, module_id="MOD-002", score=63, is_passed=True,  taken_at=now - timedelta(days=2))
    qr_r2_5 = QuizResult(agent_id=agent_red2.user_id, module_id="MOD-002", score=65, is_passed=True,  taken_at=now - timedelta(days=1))
    qr_r2_6 = QuizResult(agent_id=agent_red2.user_id, module_id="MOD-003", score=60, is_passed=True,  taken_at=now - timedelta(days=1))

    # 蔡佳穎（綠）
    qr_g3_1 = QuizResult(agent_id=agent_green3.user_id, module_id="MOD-001", score=92, is_passed=True, taken_at=now - timedelta(days=3))
    qr_g3_2 = QuizResult(agent_id=agent_green3.user_id, module_id="MOD-002", score=86, is_passed=True, taken_at=now - timedelta(days=1))

    db.add_all([
        qr_r1, qr_r2, qr_r3, qr_r4,
        qr_a1, qr_a2, qr_a3,
        qr_g1_1, qr_g1_2, qr_g1_3, qr_g2_1, qr_g2_2,
        qr_r2_1, qr_r2_2, qr_r2_3, qr_r2_4, qr_r2_5, qr_r2_6,
        qr_g3_1, qr_g3_2,
    ])
    db.commit()

    # -------------------------------------------------------------------
    # 5. QuizAttemptAnswers（只為失敗的測驗建立逐題紀錄）
    # -------------------------------------------------------------------
    def ans(result, question, correct):
        return QuizAttemptAnswer(result_id=result.result_id, question_id=question.question_id, is_correct=correct)

    db.add_all([
        # 王小明 Quiz 1 (score=45)：Q1,Q3,Q4 答錯
        ans(qr_r1, q001_1, False), ans(qr_r1, q001_2, True),  ans(qr_r1, q001_3, False),
        ans(qr_r1, q001_4, False), ans(qr_r1, q001_5, True),

        # 王小明 Quiz 2 (score=50)：Q2,Q3,Q5 答錯
        ans(qr_r2, q001_1, True),  ans(qr_r2, q001_2, False), ans(qr_r2, q001_3, False),
        ans(qr_r2, q001_4, True),  ans(qr_r2, q001_5, False),

        # 王小明 Quiz 3 (score=40)：Q1,Q2,Q3,Q4 答錯
        ans(qr_r3, q001_1, False), ans(qr_r3, q001_2, False), ans(qr_r3, q001_3, False),
        ans(qr_r3, q001_4, False), ans(qr_r3, q001_5, True),

        # 李小花 Quiz 1 (score=55)：Q1,Q3,Q5 答錯
        ans(qr_a1, q002_1, False), ans(qr_a1, q002_2, True),  ans(qr_a1, q002_3, False),
        ans(qr_a1, q002_4, True),  ans(qr_a1, q002_5, False),

        # 李小花 Quiz 2 (score=57)：Q2,Q3,Q4 答錯
        ans(qr_a2, q002_1, True),  ans(qr_a2, q002_2, False), ans(qr_a2, q002_3, False),
        ans(qr_a2, q002_4, False), ans(qr_a2, q002_5, True),

        # 吳建宏 Quiz 1 (score=55)：Q1,Q2,Q4,Q5 答錯
        ans(qr_r2_1, q002_1, False), ans(qr_r2_1, q002_2, False), ans(qr_r2_1, q002_3, True),
        ans(qr_r2_1, q002_4, False), ans(qr_r2_1, q002_5, False),

        # 吳建宏 Quiz 2 (score=60)：Q1,Q3,Q5 答錯
        ans(qr_r2_2, q002_1, False), ans(qr_r2_2, q002_2, True),  ans(qr_r2_2, q002_3, False),
        ans(qr_r2_2, q002_4, True),  ans(qr_r2_2, q002_5, False),

        # 吳建宏 Quiz 3 (score=58)：Q2,Q3,Q4 答錯
        ans(qr_r2_3, q002_1, True),  ans(qr_r2_3, q002_2, False), ans(qr_r2_3, q002_3, False),
        ans(qr_r2_3, q002_4, False), ans(qr_r2_3, q002_5, True),

        # 吳建宏 Quiz 4 (score=63)：Q2,Q4 答錯
        ans(qr_r2_4, q002_1, True),  ans(qr_r2_4, q002_2, False), ans(qr_r2_4, q002_3, True),
        ans(qr_r2_4, q002_4, False), ans(qr_r2_4, q002_5, True),

        # 吳建宏 Quiz 5 (score=65)：Q1,Q3 答錯
        ans(qr_r2_5, q002_1, False), ans(qr_r2_5, q002_2, True),  ans(qr_r2_5, q002_3, False),
        ans(qr_r2_5, q002_4, True),  ans(qr_r2_5, q002_5, True),

        # 吳建宏 MOD-003 Quiz (score=60)：Q1,Q3,Q5 答錯
        ans(qr_r2_6, q003_1, False), ans(qr_r2_6, q003_2, True),  ans(qr_r2_6, q003_3, False),
        ans(qr_r2_6, q003_4, True),  ans(qr_r2_6, q003_5, False),
    ])
    db.commit()

    # -------------------------------------------------------------------
    # 6. ModuleStateLocks（預先鎖定紅色員工的模組）
    # -------------------------------------------------------------------
    lock_red = ModuleStateLock(
        agent_id=agent_red.user_id,
        module_id="MOD-001",
        lock_reason="failed_3x",
        locked_timestamp=now - timedelta(days=2),
        is_locked=True
    )
    lock_red2 = ModuleStateLock(
        agent_id=agent_red2.user_id,
        module_id="MOD-002",
        lock_reason="avg_below_70",
        locked_timestamp=now - timedelta(days=1),
        is_locked=True
    )
    db.add_all([lock_red, lock_red2])
    db.flush()

    db.add_all([
        Notification(manager_id=manager1.user_id, agent_id=agent_red.user_id,  lock_id=lock_red.lock_id),
        Notification(manager_id=manager2.user_id, agent_id=agent_red2.user_id, lock_id=lock_red2.lock_id),
    ])
    db.commit()

    print("Seed 完成！")
    print(f"  Manager: 陳志明（南港）、林雅惠（信義）")
    print(f"  紅色員工: 王小明（failed_3x）、吳建宏（avg_below_70）")
    print(f"  黃色員工: 李小花（連續 2 次失敗）、張大偉（連續 3 次下滑）")
    print(f"  綠色員工: 劉美玲、蔡佳穎")
    print(f"  空白員工: 林志豪（無任何答題紀錄）")

    db.close()


if __name__ == "__main__":
    seed()
