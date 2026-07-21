"""
Challenge Quiz API — ishtirokchilar uchun real-time quiz
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timezone
from typing import Optional
import random

from shared.database import get_db, User, Challenge, ChallengeParticipant, ChallengeStatus, Question, Transaction, TransactionType
from backend.core.deps import get_current_user
from shared.database.redis_client import get_redis, CacheService

router = APIRouter(prefix="/api/challenge-quiz", tags=["Challenge Quiz"])


@router.get("/{challenge_id}/info")
async def get_challenge_info(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Challenge ma'lumotlari + foydalanuvchi holati"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")

    # Ishtirokchimi?
    part_result = await db.execute(
        select(ChallengeParticipant).where(
            and_(ChallengeParticipant.challenge_id == challenge_id,
                 ChallengeParticipant.user_id == current_user.id)
        )
    )
    participant = part_result.scalar_one_or_none()

    status = ch.status.value if hasattr(ch.status, 'value') else str(ch.status)

    return {
        "id": ch.id,
        "title": ch.title,
        "description": ch.description,
        "entry_fee": ch.entry_fee,
        "prize_pool": ch.prize_pool,
        "first_place_percent": ch.first_place_percent,
        "second_place_percent": ch.second_place_percent,
        "third_place_percent": ch.third_place_percent,
        "total_questions": ch.total_questions,
        "time_per_question": ch.time_per_question,
        "starts_at": ch.starts_at,
        "ends_at": ch.ends_at,
        "status": status,
        "current_participants": ch.current_participants,
        "max_participants": ch.max_participants,
        "winners_paid": ch.winners_paid or False,
        "is_participant": participant is not None,
        "my_score": participant.score if participant else 0,
        "my_rank": participant.final_rank if participant else None,
        "my_prize": participant.prize_earned if participant else 0,
        "finished": participant.finished if participant else False,
        "user_balance": current_user.balance,
    }


@router.post("/{challenge_id}/join")
async def join_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Challengega qo'shilish"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")

    status = ch.status.value if hasattr(ch.status, 'value') else str(ch.status)
    if status not in ("upcoming", "active"):
        raise HTTPException(status_code=400, detail="Bu challengega qo'shilish mumkin emas")

    if ch.current_participants >= ch.max_participants:
        raise HTTPException(status_code=400, detail="Challenge to'lgan")

    # Allaqachon qo'shilganmi?
    existing = await db.execute(
        select(ChallengeParticipant).where(
            and_(ChallengeParticipant.challenge_id == challenge_id,
                 ChallengeParticipant.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Siz allaqachon ishtirokchisiz")

    # To'lov
    if ch.entry_fee > 0:
        if current_user.balance < ch.entry_fee:
            raise HTTPException(
                status_code=400,
                detail=f"Balansingizda yetarli mablag' yo'q. Kerak: {ch.entry_fee:,.0f} so'm, sizda: {current_user.balance:,.0f} so'm"
            )
        balance_before = current_user.balance
        current_user.balance -= ch.entry_fee
        ch.prize_pool += ch.entry_fee
        tx = Transaction(
            user_id=current_user.id,
            type=TransactionType.CHALLENGE_ENTRY,
            amount=-ch.entry_fee,
            balance_before=balance_before,
            balance_after=current_user.balance,
            description=f"Challenge kirish: {ch.title}",
            reference_id=challenge_id,
        )
        db.add(tx)

    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=current_user.id,
        entry_paid=(ch.entry_fee > 0),
    )
    db.add(participant)
    ch.current_participants += 1
    await db.commit()

    return {
        "success": True,
        "message": "Challengega muvaffaqiyatli qo'shildingiz!",
        "new_balance": current_user.balance,
        "prize_pool": ch.prize_pool,
    }


@router.get("/{challenge_id}/start-quiz")
async def start_challenge_quiz(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Challenge quizini boshlash — savollarni olish"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")

    status = ch.status.value if hasattr(ch.status, 'value') else str(ch.status)
    if status != "active":
        raise HTTPException(status_code=400, detail="Challenge hali boshlanmagan yoki tugagan")

    # Ishtirokchimi?
    part_result = await db.execute(
        select(ChallengeParticipant).where(
            and_(ChallengeParticipant.challenge_id == challenge_id,
                 ChallengeParticipant.user_id == current_user.id)
        )
    )
    participant = part_result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=403, detail="Siz bu challengega qo'shilmagansiz")

    if participant.finished:
        raise HTTPException(status_code=400, detail="Siz allaqachon bu challengeni yakunladingiz")

    # Challenge savollarini olish
    question_ids = ch.question_ids or []

    if question_ids:
        # Admin qo'shgan savollar
        q_result = await db.execute(
            select(Question).where(
                and_(Question.id.in_(question_ids), Question.is_active == True)
            )
        )
        questions = q_result.scalars().all()
    else:
        # Umumiy savollardan random
        q_result = await db.execute(
            select(Question).where(Question.is_active == True)
        )
        all_q = q_result.scalars().all()
        count = min(ch.total_questions, len(all_q))
        if count == 0:
            raise HTTPException(status_code=400, detail="Challenge uchun savollar yo'q")
        questions = random.sample(all_q, count)

    # Savollarni to'g'ri javobsiz qaytarish
    questions_data = []
    for q in questions:
        options = [{"index": i, "text": o["text"]} for i, o in enumerate(q.options)]
        questions_data.append({
            "id": q.id,
            "text": q.text,
            "media_file_id": q.media_file_id,
            "question_type": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
            "options": options,
            "time_limit": getattr(q, 'time_limit', None) or ch.time_per_question,
        })

    now = datetime.now(timezone.utc)
    time_remaining = None
    if ch.ends_at:
        delta = (ch.ends_at.replace(tzinfo=timezone.utc) if ch.ends_at.tzinfo is None else ch.ends_at) - now
        time_remaining = max(0, int(delta.total_seconds()))

    return {
        "challenge_id": challenge_id,
        "title": ch.title,
        "questions": questions_data,
        "total": len(questions_data),
        "time_per_question": ch.time_per_question,
        "ends_at": ch.ends_at,
        "time_remaining": time_remaining,
        "prize_pool": ch.prize_pool,
        "first_place_percent": ch.first_place_percent,
        "second_place_percent": ch.second_place_percent,
        "third_place_percent": ch.third_place_percent,
    }


from pydantic import BaseModel
from typing import List

class AnswerSubmit(BaseModel):
    question_id: int
    selected_option: int
    time_taken: float

class AnswersSubmit(BaseModel):
    answers: List[AnswerSubmit]


@router.post("/{challenge_id}/submit")
async def submit_challenge_answers(
    challenge_id: int,
    data: AnswersSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Challenge javoblarini yuborish"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")

    part_result = await db.execute(
        select(ChallengeParticipant).where(
            and_(ChallengeParticipant.challenge_id == challenge_id,
                 ChallengeParticipant.user_id == current_user.id)
        )
    )
    participant = part_result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=403, detail="Siz bu challengeda qatnashmaysiz")

    if participant.finished:
        return {"already_finished": True, "score": participant.score}

    score = 0
    correct = 0
    total_time = 0.0

    for answer in data.answers:
        q_id = answer.question_id
        selected = answer.selected_option
        time_taken = answer.time_taken

        if selected < 0:  # Javob bermagan
            continue

        q_result = await db.execute(select(Question).where(Question.id == q_id))
        question = q_result.scalar_one_or_none()
        if not question:
            continue
        if not question:
            continue

        if 0 <= selected < len(question.options):
            is_correct = question.options[selected].get("is_correct", False)
            if is_correct:
                score += 10
                correct += 1
        total_time += time_taken

    participant.score = score
    participant.correct_answers = correct
    participant.total_answers = len(data.answers)
    participant.time_spent = total_time
    participant.finished = True
    participant.finished_at = datetime.now(timezone.utc)

    # User statistikasini yangilash
    current_user.total_games += 1
    current_user.correct_answers += correct
    current_user.total_answers += len(data.answers)

    status = ch.status.value if hasattr(ch.status, 'value') else str(ch.status)
    await db.commit()

    return {
        "success": True,
        "score": score,
        "correct": correct,
        "total": len(data.answers),
        "time_spent": total_time,
        "challenge_status": status,
        "message": "Javoblaringiz qabul qilindi! Challenge tugashini kuting." if status == "active" else "Challenge tugadi!",
    }


@router.get("/{challenge_id}/leaderboard")
async def get_challenge_leaderboard(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Real-time challenge reytingi"""
    result = await db.execute(
        select(ChallengeParticipant, User)
        .join(User, ChallengeParticipant.user_id == User.id)
        .where(ChallengeParticipant.challenge_id == challenge_id)
        .order_by(
            ChallengeParticipant.score.desc(),
            ChallengeParticipant.time_spent.asc()
        )
    )
    rows = result.all()

    leaderboard = []
    my_rank = None

    for idx, (p, u) in enumerate(rows, 1):
        entry = {
            "rank": idx,
            "full_name": u.full_name,
            "username": u.username,
            "score": p.score,
            "correct_answers": p.correct_answers,
            "time_spent": round(p.time_spent, 1),
            "finished": p.finished,
            "prize_earned": p.prize_earned,
            "is_me": u.id == current_user.id,
        }
        leaderboard.append(entry)
        if u.id == current_user.id:
            my_rank = idx

    return {
        "leaderboard": leaderboard,
        "my_rank": my_rank,
        "total_participants": len(rows),
    }
