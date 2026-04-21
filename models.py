from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)  # 'agent' or 'manager'
    branch_code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    quiz_results = relationship("QuizResult", back_populates="agent")
    team_as_agent = relationship("TeamStructure", foreign_keys="TeamStructure.agent_id", back_populates="agent")
    team_as_manager = relationship("TeamStructure", foreign_keys="TeamStructure.manager_id", back_populates="manager")


class QuizResult(Base):
    """
    屬於 Project 1 負責寫入，Project 9 只讀取。
    Demo 階段由 seed.py 填入假資料。
    """
    __tablename__ = "quiz_results"

    result_id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    module_id = Column(String, nullable=False)
    score = Column(Float, nullable=False)  # 0~100
    is_passed = Column(Boolean, nullable=False)
    taken_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("User", back_populates="quiz_results")
    answers = relationship("QuizAttemptAnswer", back_populates="result")


class Question(Base):
    """
    每個模組的題目，由 Project 1 維護。Demo 階段由 seed.py 填入假資料。
    """
    __tablename__ = "questions"

    question_id = Column(Integer, primary_key=True, index=True)
    module_id = Column(String, nullable=False, index=True)
    question_number = Column(Integer, nullable=False)  # 1~5，顯示用
    content = Column(String, nullable=False)

    answers = relationship("QuizAttemptAnswer", back_populates="question")


class QuizAttemptAnswer(Base):
    """
    每次測驗的逐題作答紀錄，由 Project 1 維護。Demo 階段由 seed.py 填入假資料。
    """
    __tablename__ = "quiz_attempt_answers"

    answer_id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("quiz_results.result_id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.question_id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)

    result = relationship("QuizResult", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class TeamStructure(Base):
    __tablename__ = "team_structures"

    mapping_id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    branch_code = Column(String, nullable=False)
    effective_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("User", foreign_keys=[agent_id], back_populates="team_as_agent")
    manager = relationship("User", foreign_keys=[manager_id], back_populates="team_as_manager")


class ModuleStateLock(Base):
    __tablename__ = "module_state_locks"

    lock_id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    module_id = Column(String, nullable=False)
    lock_reason = Column(String, nullable=False)  # 'failed_3x' or 'avg_below_70'
    locked_timestamp = Column(DateTime, default=datetime.utcnow)
    is_locked = Column(Boolean, default=True)

    # Relationships
    agent = relationship("User")
    coaching_interventions = relationship("CoachingIntervention", back_populates="lock")


class CoachingIntervention(Base):
    __tablename__ = "coaching_interventions"

    intervention_id = Column(Integer, primary_key=True, index=True)
    lock_id = Column(Integer, ForeignKey("module_state_locks.lock_id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    manager_notes_text = Column(Text, nullable=False)
    unlocked_timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lock = relationship("ModuleStateLock", back_populates="coaching_interventions")
    manager = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    lock_id = Column(Integer, ForeignKey("module_state_locks.lock_id"), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    manager = relationship("User", foreign_keys=[manager_id])
    agent = relationship("User", foreign_keys=[agent_id])
    lock = relationship("ModuleStateLock")