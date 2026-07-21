"""
Challenge va Quiz API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List

from shared.database import (
    get_db, User, Challenge, ChallengeParticipant, ChallengeStatus,
    Question, QuizSession, Transaction, TransactionType, Category
)
from backend.core.deps import get_current_user, get_admin_user, get_rating_service, get_cache_service
from backend.schemas.challenge import (
    ChallengeCreate, ChallengeResponse, QuestionCreate, QuestionResponse,
    QuestionForQuiz, QuizAnswerSubmit, ParticipantResponse
)
from shared.database.redis_client import RatingService, CacheService

router = APIRouter(prefix="/api", tags=["Challenges & Quiz"])


# ─── Kategoriyalar ────────────────────────────────────────────────────────────

@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.is_active == True))
    return result.scalars().all()


@router.post("/admin/categories")
async def create_category(
    name: str = Body(...),
    description: str = Body(default=""),
    icon: str = Body(default="📚"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    category = Category(name=name, description=description, icon=icon)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


# ─── Savollar ─────────────────────────────────────────────────────────────────

@router.get("/questions", response_model=list[QuestionResponse])
async def get_questions(
    category_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: savollar ro'yxati"""
    query = select(Question).where(Question.is_active == True)
    if category_id:
        query = query.where(Question.category_id == category_id)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    
    offset = (page - 1) * limit
    query = query.order_by(desc(Question.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/admin/questions", response_model=QuestionResponse)
async def create_question(
    data: QuestionCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: yangi savol qo'shish"""
    question = Question(
        category_id=data.category_id,
        question_type=data.question_type,
        difficulty=data.difficulty,
        text=data.text,
        options=[o.model_dump() for o in data.options],
        explanation=data.explanation,
        created_by_admin=admin.id,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.put("/admin/questions/{question_id}")
async def update_question(
    question_id: int,
    data: QuestionCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: savolni tahrirlash"""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Savol topilmadi")
    
    question.text = data.text
    question.options = [o.model_dump() for o in data.options]
    question.difficulty = data.difficulty
    question.explanation = data.explanation
    await db.commit()
    return {"success": True}


@router.delete("/admin/questions/{question_id}")
async def delete_question(
    question_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Savol topilmadi")
    question.is_active = False
    await db.commit()
    return {"success": True}


# ─── Challenge'lar ────────────────────────────────────────────────────────────

@router.get("/challenges", response_model=list[ChallengeResponse])
async def get_challenges(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Challengelar ro'yxati"""
    query = select(Challenge)
    if status:
        query = query.where(Challenge.status == status)
    else:
        query = query.where(Challenge.status.in_(["upcoming", "active"]))
    
    offset = (page - 1) * limit
    query = query.order_by(desc(Challenge.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")
    return challenge


@router.post("/admin/challenges", response_model=ChallengeResponse)
async def create_challenge(
    data: ChallengeCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: yangi challenge yaratish"""
    # Foizlarni tekshirish
    total_percent = (
        data.first_place_percent +
        data.second_place_percent +
        data.third_place_percent +
        data.admin_commission
    )
    if abs(total_percent - 100.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Foizlar yig'indisi 100% bo'lishi kerak. Hozir: {total_percent}%"
        )
    
    challenge = Challenge(
        title=data.title,
        description=data.description,
        entry_fee=data.entry_fee,
        min_prize_pool=data.min_prize_pool,
        prize_pool=data.min_prize_pool,
        first_place_percent=data.first_place_percent,
        second_place_percent=data.second_place_percent,
        third_place_percent=data.third_place_percent,
        admin_commission=data.admin_commission,
        total_questions=data.total_questions,
        time_per_question=data.time_per_question,
        category_id=data.category_id,
        difficulty=data.difficulty,
        max_participants=data.max_participants,
        starts_at=data.starts_at,
        created_by=admin.id,
    )
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)
    return challenge


@router.post("/challenges/{challenge_id}/join")
async def join_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Challengega qo'shilish (kirish to'lovini to'lash)"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")
    
    if challenge.status.value not in ("upcoming", "active"):
        raise HTTPException(status_code=400, detail="Bu challenge'ga qo'shilish mumkin emas")
    
    if challenge.current_participants >= challenge.max_participants:
        raise HTTPException(status_code=400, detail="Challenge to'lgan")
    
    # Allaqachon ishtirok etayotganini tekshirish
    existing = await db.execute(
        select(ChallengeParticipant).where(
            and_(
                ChallengeParticipant.challenge_id == challenge_id,
                ChallengeParticipant.user_id == current_user.id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Siz allaqachon bu challengeda ishtirok etmoqdasiz")
    
    # To'lov
    if challenge.entry_fee > 0:
        if current_user.balance < challenge.entry_fee:
            raise HTTPException(status_code=400, detail="Balansingiz yetarli emas")
        
        balance_before = current_user.balance
        current_user.balance -= challenge.entry_fee
        challenge.prize_pool += challenge.entry_fee
        
        transaction = Transaction(
            user_id=current_user.id,
            type=TransactionType.CHALLENGE_ENTRY,
            amount=-challenge.entry_fee,
            balance_before=balance_before,
            balance_after=current_user.balance,
            description=f"Challenge kirish to'lovi: {challenge.title}",
            reference_id=challenge_id,
        )
        db.add(transaction)
    
    # Ishtirokchi qo'shish
    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=current_user.id,
        entry_paid=(challenge.entry_fee > 0),
    )
    db.add(participant)
    challenge.current_participants += 1
    
    await db.commit()
    return {"success": True, "message": "Challengega muvaffaqiyatli qo'shildingiz!"}


@router.post("/admin/challenges/{challenge_id}/add-user/{user_id}")
async def admin_add_user_to_challenge(
    challenge_id: int,
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: foydalanuvchini challengega tekin qo'shish"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")
    
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    existing = await db.execute(
        select(ChallengeParticipant).where(
            and_(
                ChallengeParticipant.challenge_id == challenge_id,
                ChallengeParticipant.user_id == user_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Foydalanuvchi allaqachon ishtirokchi")
    
    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=user_id,
        is_free_entry=True,
        entry_paid=True,
    )
    db.add(participant)
    challenge.current_participants += 1
    await db.commit()
    
    return {"success": True, "message": f"{user.full_name} challengega qo'shildi"}


# ─── Quiz O'tkazish ────────────────────────────────────────────────────────────

@router.get("/quiz/start")
async def start_quiz(
    category_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    count: int = Query(10, ge=5, le=30),
    current_user: User = Depends(get_current_user),
    cache: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
):
    """Bepul individual quiz boshlash"""
    query = select(Question).where(Question.is_active == True)
    if category_id:
        query = query.where(Question.category_id == category_id)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    
    result = await db.execute(query)
    all_questions = result.scalars().all()
    
    if len(all_questions) < count:
        raise HTTPException(status_code=400, detail="Yetarli savol mavjud emas")
    
    import random
    selected = random.sample(all_questions, count)
    
    # Quiz sessiyasi yaratish
    session = QuizSession(
        user_id=current_user.id,
        total_questions=count,
        category_id=category_id,
    )
    db.add(session)
    await db.flush()
    
    # Holat saqlash
    state = {
        "session_id": session.id,
        "questions": [q.id for q in selected],
        "current_index": 0,
        "score": 0,
        "correct": 0,
    }
    await cache.set_quiz_state(current_user.telegram_id, state, expire=3600)
    
    await db.commit()
    
    # Birinchi savolni qaytarish (to'g'ri javobsiz)
    first_q = selected[0]
    return {
        "session_id": session.id,
        "total": count,
        "current": 1,
        "question": _sanitize_question(first_q),
    }


@router.post("/quiz/answer")
async def submit_answer(
    data: QuizAnswerSubmit,
    current_user: User = Depends(get_current_user),
    cache: CacheService = Depends(get_cache_service),
    rating_service: RatingService = Depends(get_rating_service),
    db: AsyncSession = Depends(get_db)
):
    """Quiz javobi yuborish"""
    state = await cache.get_quiz_state(current_user.telegram_id)
    if not state:
        raise HTTPException(status_code=400, detail="Aktiv quiz topilmadi")
    
    current_index = state["current_index"]
    question_ids = state["questions"]
    
    if current_index >= len(question_ids):
        raise HTTPException(status_code=400, detail="Quiz tugagan")
    
    # Savolni tekshirish
    result = await db.execute(select(Question).where(Question.id == question_ids[current_index]))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Savol topilmadi")
    
    is_correct = question.options[data.selected_option].get("is_correct", False)
    
    # Statistika yangilash
    question.times_asked += 1
    if is_correct:
        question.correct_count += 1
        state["score"] += 10
        state["correct"] += 1
    
    state["current_index"] += 1
    
    # Session yangilash
    session_result = await db.execute(
        select(QuizSession).where(QuizSession.id == state["session_id"])
    )
    session = session_result.scalar_one_or_none()
    if session:
        session.correct_answers = state["correct"]
        session.score = state["score"]
    
    # Keyingi savol bormi?
    next_question = None
    is_finished = state["current_index"] >= len(question_ids)
    
    if not is_finished:
        next_q_result = await db.execute(
            select(Question).where(Question.id == question_ids[state["current_index"]])
        )
        next_question = next_q_result.scalar_one_or_none()
        await cache.set_quiz_state(current_user.telegram_id, state)
    else:
        # Quiz tugadi - XP berish
        xp_earned = state["correct"] * 5
        current_user.xp_points += xp_earned
        current_user.total_games += 1
        current_user.correct_answers += state["correct"]
        current_user.total_answers += len(question_ids)
        _update_level(current_user)
        
        if session:
            session.is_completed = True
            session.xp_earned = xp_earned
            from datetime import datetime
            session.completed_at = datetime.utcnow()
        
        await rating_service.update_score(current_user.telegram_id, xp_earned)
        await cache.delete_quiz_state(current_user.telegram_id)
    
    await db.commit()
    
    response = {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "score": state["score"],
        "current": state["current_index"],
        "total": len(question_ids),
        "is_finished": is_finished,
    }
    
    if not is_finished and next_question:
        response["next_question"] = _sanitize_question(next_question)
    
    if is_finished:
        response["final_score"] = state["score"]
        response["correct_count"] = state["correct"]
        response["xp_earned"] = current_user.xp_points
    
    return response


def _sanitize_question(question: Question) -> dict:
    """Savolni to'g'ri javobsiz qaytarish"""
    options = []
    for i, opt in enumerate(question.options):
        options.append({"index": i, "text": opt["text"]})
    
    return {
        "id": question.id,
        "text": question.text,
        "media_file_id": question.media_file_id,
        "question_type": question.question_type.value if hasattr(question.question_type, 'value') else question.question_type,
        "options": options,
    }


def _update_level(user: User):
    """XP asosida levelni yangilash"""
    xp = user.xp_points
    if xp >= 10000:
        user.level = 10
    elif xp >= 5000:
        user.level = 9
    elif xp >= 2500:
        user.level = 8
    elif xp >= 1200:
        user.level = 7
    elif xp >= 600:
        user.level = 6
    elif xp >= 300:
        user.level = 5
    elif xp >= 150:
        user.level = 4
    elif xp >= 75:
        user.level = 3
    elif xp >= 30:
        user.level = 2
    else:
        user.level = 1
