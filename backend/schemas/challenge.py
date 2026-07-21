"""
Challenge va Quiz Pydantic schema'lari
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class QuestionOption(BaseModel):
    text: str
    is_correct: bool = False


class QuestionCreate(BaseModel):
    category_id: Optional[int] = None
    question_type: str = "text"
    difficulty: str = "medium"
    text: str = Field(..., min_length=5)
    options: List[QuestionOption] = Field(..., min_length=2, max_length=6)
    explanation: Optional[str] = None

    @field_validator("options")
    @classmethod
    def validate_options(cls, v):
        correct_count = sum(1 for o in v if o.is_correct)
        if correct_count != 1:
            raise ValueError("Aynan 1 ta to'g'ri javob bo'lishi kerak")
        return v


class QuestionResponse(BaseModel):
    id: int
    category_id: Optional[int] = None
    question_type: str
    difficulty: str
    text: str
    media_file_id: Optional[str] = None
    options: List[dict]
    times_asked: int
    correct_count: int
    accuracy_rate: float
    is_active: bool

    model_config = {"from_attributes": True}

    @field_validator("question_type", "difficulty", mode="before")
    @classmethod
    def enum_to_str(cls, v):
        if hasattr(v, "value"):
            return v.value
        return str(v)


class QuestionForQuiz(BaseModel):
    """Quiz davomida foydalanuvchiga ko'rsatiladigan savol (to'g'ri javobsiz)"""
    id: int
    text: str
    media_file_id: Optional[str] = None
    question_type: str
    options: List[dict]  # is_correct maydoni olib tashlangan


class ChallengeCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    entry_fee: float = Field(default=0.0, ge=0)
    min_prize_pool: float = Field(default=0.0, ge=0)
    first_place_percent: float = Field(default=50.0, ge=0, le=100)
    second_place_percent: float = Field(default=30.0, ge=0, le=100)
    third_place_percent: float = Field(default=10.0, ge=0, le=100)
    admin_commission: float = Field(default=10.0, ge=0, le=100)
    total_questions: int = Field(default=20, ge=5, le=100)
    time_per_question: int = Field(default=30, ge=10, le=120)
    category_id: Optional[int] = None
    difficulty: str = "medium"
    max_participants: int = Field(default=1000, ge=2)
    starts_at: Optional[datetime] = None

    @field_validator("first_place_percent", "second_place_percent", "third_place_percent", "admin_commission")
    @classmethod
    def validate_percents(cls, v, info):
        return round(v, 2)


class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    entry_fee: float
    prize_pool: float
    first_place_percent: float
    second_place_percent: float
    third_place_percent: float
    admin_commission: float
    total_questions: int
    time_per_question: int
    max_participants: int
    current_participants: int
    status: str
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("status", mode="before")
    @classmethod
    def status_to_str(cls, v):
        if hasattr(v, "value"):
            return v.value
        return str(v)


class ParticipantResponse(BaseModel):
    user_id: int
    score: int
    correct_answers: int
    total_answers: int
    final_rank: Optional[int] = None
    prize_earned: float
    finished: bool

    model_config = {"from_attributes": True}


class QuizAnswerSubmit(BaseModel):
    question_id: int
    selected_option: int  # Index (0-3)
    time_taken: float  # Soniyada


class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: float
    balance_before: float
    balance_after: float
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("type", mode="before")
    @classmethod
    def enum_to_str(cls, v):
        if hasattr(v, "value"):
            return v.value
        return str(v)
