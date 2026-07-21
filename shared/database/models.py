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


# ─── Enumeratsiyalar ─────────────────────────────────────────────────────────

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


# ─── Foydalanuvchilar ─────────────────────────────────────────────────────────

class User(Base):
    """Telegram foydalanuvchilar"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    language_code = Column(String(10), default="uz")

    # Balans va XP
    balance = Column(Float, default=0.0, nullable=False)
    xp_points = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)

    # Statistika
    total_games = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)
    total_winnings = Column(Float, default=0.0)

    # Status
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_registered = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    challenge_participants = relationship("ChallengeParticipant", back_populates="user")
    quiz_sessions = relationship("QuizSession", back_populates="user")

    def __repr__(self):
        return f"<User {self.telegram_id} - {self.first_name}>"

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


# ─── Majburiy Kanallar ────────────────────────────────────────────────────────

class RequiredChannel(Base):
    """Admin qo'shadigan majburiy kanallar"""
    __tablename__ = "required_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(50), unique=True, nullable=False)
    channel_name = Column(String(100), nullable=False)
    channel_link = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Channel {self.channel_name}>"


# ─── Kategoriyalar ────────────────────────────────────────────────────────────

class Category(Base):
    """Savollar kategoriyalari"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String(10), default="📚")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    questions = relationship("Question", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


# ─── Savollar ─────────────────────────────────────────────────────────────────

class Question(Base):
    """Test savollari"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    question_type = Column(Enum(QuestionType), default=QuestionType.TEXT)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)

    # Savol matni
    text = Column(Text, nullable=False)
    media_file_id = Column(String(200), nullable=True)  # Telegram file_id
    media_url = Column(String(500), nullable=True)

    # Javoblar (JSON: [{"text": "...", "is_correct": true/false}])
    options = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=True)  # To'g'ri javob izohi

    # Statistika
    times_asked = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    created_by_admin = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="questions")

    def __repr__(self):
        return f"<Question {self.id}: {self.text[:50]}>"

    @property
    def correct_answer(self):
        """To'g'ri javobni qaytaradi"""
        for opt in self.options:
            if opt.get("is_correct"):
                return opt
        return None

    @property
    def accuracy_rate(self) -> float:
        if self.times_asked == 0:
            return 0.0
        return round(self.correct_count / self.times_asked * 100, 1)


# ─── Challenge'lar ────────────────────────────────────────────────────────────

class Challenge(Base):
    """Pullik/bepul katta challengelar"""
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    banner_file_id = Column(String(200), nullable=True)

    # Narx va fond
    entry_fee = Column(Float, default=0.0, nullable=False)  # Kirish narxi (0 = bepul)
    prize_pool = Column(Float, default=0.0, nullable=False)  # Umumiy fond
    min_prize_pool = Column(Float, default=0.0)  # Kafolatlangan minimal fond

    # G'oliblik foizlari
    first_place_percent = Column(Float, default=50.0)   # 1-o'rin %
    second_place_percent = Column(Float, default=30.0)  # 2-o'rin %
    third_place_percent = Column(Float, default=10.0)   # 3-o'rin %
    admin_commission = Column(Float, default=10.0)      # Admin komissiya %

    # Sozlamalar
    total_questions = Column(Integer, default=20)
    time_per_question = Column(Integer, default=30)  # sekundda
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)

    # Ishtirokchilar
    max_participants = Column(Integer, default=1000)
    current_participants = Column(Integer, default=0)

    # Vaqt
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(ChallengeStatus), default=ChallengeStatus.UPCOMING)

    # Admin
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    participants = relationship("ChallengeParticipant", back_populates="challenge")

    def __repr__(self):
        return f"<Challenge {self.id}: {self.title}>"


class ChallengeParticipant(Base):
    """Challenge ishtirokchilari"""
    __tablename__ = "challenge_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Natijalar
    score = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)
    time_spent = Column(Float, default=0.0)  # sekundda
    final_rank = Column(Integer, nullable=True)
    prize_earned = Column(Float, default=0.0)

    # Status
    is_free_entry = Column(Boolean, default=False)  # Admin tekin qo'shgan
    entry_paid = Column(Boolean, default=False)
    finished = Column(Boolean, default=False)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    challenge = relationship("Challenge", back_populates="participants")
    user = relationship("User", back_populates="challenge_participants")

    __table_args__ = (
        Index("ix_challenge_participant", "challenge_id", "user_id", unique=True),
    )


# ─── Quiz Sessiyalari ─────────────────────────────────────────────────────────

class QuizSession(Base):
    """Individual quiz sessiyalari"""
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=True)  # Challenge yoki oddiy quiz
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Natijalar
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score = Column(Integer, default=0)
    time_spent = Column(Float, default=0.0)
    xp_earned = Column(Integer, default=0)

    # Savollar tarixi (JSON)
    answers_log = Column(JSON, default=list)

    # Status
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="quiz_sessions")


# ─── Moliyaviy Tranzaksiyalar ─────────────────────────────────────────────────

class Transaction(Base):
    """Barcha moliyaviy tranzaksiyalar"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)

    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)

    description = Column(String(300), nullable=True)
    reference_id = Column(Integer, nullable=True)  # challenge_id yoki boshqa ref

    # Admin tranzaksiyalari uchun
    admin_id = Column(Integer, nullable=True)
    admin_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.type} {self.amount} for user {self.user_id}>"


# ─── Broadcast Xabarlari ─────────────────────────────────────────────────────

class BroadcastMessage(Base):
    """Admin reklama/xabarnoma xabarlari"""
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Xabar kontenti
    message_type = Column(String(20), default="text")  # text, photo, video
    text = Column(Text, nullable=True)
    media_file_id = Column(String(200), nullable=True)
    button_text = Column(String(100), nullable=True)
    button_url = Column(String(500), nullable=True)

    # Statistika
    total_sent = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, sending, completed, failed

    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Broadcast {self.id}: {self.status}>"
