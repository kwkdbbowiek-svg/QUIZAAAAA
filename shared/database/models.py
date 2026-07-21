"""
Barcha database modellari - PostgreSQL
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean,
    Text, DateTime, ForeignKey, Enum, JSON, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    BANNED = "banned"
    PENDING = "pending"


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    CHALLENGE_ENTRY = "challenge_entry"
    CHALLENGE_WIN = "challenge_win"
    REFUND = "refund"
    ADMIN_ADJUST = "admin_adjust"


class ChallengeStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class QuestionType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    language_code = Column(String(10), default="uz")

    balance = Column(Float, default=0.0, nullable=False)
    xp_points = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)

    total_games = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)
    total_winnings = Column(Float, default=0.0)

    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_registered = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="user")
    challenge_participants = relationship("ChallengeParticipant", back_populates="user")
    quiz_sessions = relationship("QuizSession", back_populates="user")

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def accuracy(self) -> float:
        if self.total_answers == 0:
            return 0.0
        return round(self.correct_answers / self.total_answers * 100, 1)


class RequiredChannel(Base):
    __tablename__ = "required_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(50), unique=True, nullable=False)
    channel_name = Column(String(100), nullable=False)
    channel_link = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String(10), default="📚")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    questions = relationship("Question", back_populates="category")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    question_type = Column(Enum(QuestionType), default=QuestionType.TEXT)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)

    text = Column(Text, nullable=False)
    media_file_id = Column(String(200), nullable=True)
    media_url = Column(String(500), nullable=True)

    # Javoblar: [{"text": "...", "is_correct": true/false}]
    options = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=True)

    # Har bir savol uchun vaqt (soniyada)
    time_limit = Column(Integer, default=30)

    times_asked = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_by_admin = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="questions")

    @property
    def correct_answer(self):
        for opt in self.options:
            if opt.get("is_correct"):
                return opt
        return None

    @property
    def accuracy_rate(self) -> float:
        if self.times_asked == 0:
            return 0.0
        return round(self.correct_count / self.times_asked * 100, 1)


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    banner_file_id = Column(String(200), nullable=True)

    entry_fee = Column(Float, default=0.0, nullable=False)
    prize_pool = Column(Float, default=0.0, nullable=False)
    min_prize_pool = Column(Float, default=0.0)

    first_place_percent = Column(Float, default=50.0)
    second_place_percent = Column(Float, default=30.0)
    third_place_percent = Column(Float, default=10.0)
    admin_commission = Column(Float, default=10.0)

    total_questions = Column(Integer, default=20)
    time_per_question = Column(Integer, default=30)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)

    # Challenge savollari (JSON: list of question_ids)
    question_ids = Column(JSON, default=list)

    max_participants = Column(Integer, default=1000)
    current_participants = Column(Integer, default=0)

    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(ChallengeStatus), default=ChallengeStatus.UPCOMING)

    # G'oliblar tayinlandimi
    winners_paid = Column(Boolean, default=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    participants = relationship("ChallengeParticipant", back_populates="challenge")


class ChallengeParticipant(Base):
    __tablename__ = "challenge_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    score = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)
    time_spent = Column(Float, default=0.0)
    final_rank = Column(Integer, nullable=True)
    prize_earned = Column(Float, default=0.0)

    is_free_entry = Column(Boolean, default=False)
    entry_paid = Column(Boolean, default=False)
    finished = Column(Boolean, default=False)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    challenge = relationship("Challenge", back_populates="participants")
    user = relationship("User", back_populates="challenge_participants")

    __table_args__ = (
        Index("ix_challenge_participant", "challenge_id", "user_id", unique=True),
    )


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score = Column(Integer, default=0)
    time_spent = Column(Float, default=0.0)
    xp_earned = Column(Integer, default=0)

    answers_log = Column(JSON, default=list)

    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="quiz_sessions")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)

    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)

    description = Column(String(300), nullable=True)
    reference_id = Column(Integer, nullable=True)

    admin_id = Column(Integer, nullable=True)
    admin_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")


class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    message_type = Column(String(20), default="text")
    text = Column(Text, nullable=True)
    media_file_id = Column(String(200), nullable=True)
    button_text = Column(String(100), nullable=True)
    button_url = Column(String(500), nullable=True)

    total_sent = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")

    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
