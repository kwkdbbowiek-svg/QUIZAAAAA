"""
Quiz handler - Test va quiz o'tkazish
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
import random

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, Question, Category, QuizSession
from shared.database.redis_client import get_redis, CacheService, RatingService
from bot.keyboards.main_menu import get_main_menu, get_quiz_categories_keyboard, get_difficulty_keyboard

router = Router(name="quiz")

QUESTIONS_PER_QUIZ = 10
XP_PER_CORRECT = 5


@router.message(F.text == "🎯 Quiz Boshlash")
async def start_quiz_menu(message: Message, user: User):
    """Quiz kategoriyasini tanlash"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Category).where(Category.is_active == True)
        )
        categories = result.scalars().all()
    
    if not categories:
        await message.answer(
            "😔 Hozircha test kategoriyalari mavjud emas.\n"
            "Adminlar tez orada qo'shadi! 🔜"
        )
        return
    
    await message.answer(
        "🎯 <b>Quiz Boshlash</b>\n\n"
        "Qaysi sohada bilimingizni sinab ko'rmoqchisiz?\n"
        "Kategoriyani tanlang:",
        reply_markup=get_quiz_categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith("quiz_cat_"))
async def select_quiz_category(callback: CallbackQuery, user: User):
    """Kategoriya tanlash"""
    category_id = callback.data.replace("quiz_cat_", "")
    
    if category_id == "all":
        await callback.message.edit_text(
            "🎲 <b>Qiyinlik darajasini tanlang:</b>",
            reply_markup=get_difficulty_keyboard("all")
        )
    else:
        await callback.message.edit_text(
            "🎲 <b>Qiyinlik darajasini tanlang:</b>",
            reply_markup=get_difficulty_keyboard(category_id)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_diff_"))
async def start_quiz(callback: CallbackQuery, user: User):
    """Quiz boshlash"""
    parts = callback.data.split("_")
    difficulty = parts[2]
    category_id = parts[3] if parts[3] != "all" else None
    
    async with AsyncSessionLocal() as session:
        query = select(Question).where(Question.is_active == True)
        if category_id:
            query = query.where(Question.category_id == int(category_id))
        if difficulty != "all":
            query = query.where(Question.difficulty == difficulty)
        
        result = await session.execute(query)
        questions = result.scalars().all()
    
    if len(questions) < QUESTIONS_PER_QUIZ:
        await callback.message.edit_text(
            f"😔 Bu kategoriyada yetarli savol mavjud emas.\n"
            f"Hozir: {len(questions)} ta, kerak: {QUESTIONS_PER_QUIZ} ta"
        )
        await callback.answer()
        return
    
    selected_questions = random.sample(questions, QUESTIONS_PER_QUIZ)
    question_ids = [q.id for q in selected_questions]
    
    # Redis'ga quiz holatini saqlash
    redis = await get_redis()
    cache = CacheService(redis)
    
    # Yangi sessiya yaratish
    async with AsyncSessionLocal() as session:
        quiz_session = QuizSession(
            user_id=user.id,
            total_questions=QUESTIONS_PER_QUIZ,
            category_id=int(category_id) if category_id else None,
        )
        session.add(quiz_session)
        await session.flush()
        session_id = quiz_session.id
        await session.commit()
    
    state = {
        "session_id": session_id,
        "questions": question_ids,
        "current_index": 0,
        "score": 0,
        "correct": 0,
        "difficulty": difficulty,
    }
    await cache.set_quiz_state(user.telegram_id, state, expire=3600)
    
    await callback.message.delete()
    await send_quiz_question(callback.message, user, selected_questions[0], 1, QUESTIONS_PER_QUIZ)
    await callback.answer()


async def send_quiz_question(
    message: Message,
    user: User,
    question: Question,
    current: int,
    total: int,
    score: int = 0,
    correct: int = 0,
):
    """Savolni yuborish"""
    # Javob variantlari tugmalari
    options = []
    for i, opt in enumerate(question.options):
        options.append([
            InlineKeyboardButton(
                text=f"{['A', 'B', 'C', 'D'][i]}. {opt['text']}",
                callback_data=f"quiz_answer_{question.id}_{i}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=options)
    
    difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(
        question.difficulty.value if hasattr(question.difficulty, 'value') else question.difficulty,
        "⚪"
    )
    
    text = (
        f"📝 <b>Savol {current}/{total}</b> {difficulty_emoji}\n"
        f"💯 Joriy ball: <b>{score}</b>\n\n"
        f"<b>{question.text}</b>"
    )
    
    if question.media_file_id:
        q_type = question.question_type.value if hasattr(question.question_type, 'value') else question.question_type
        if q_type == "image":
            await message.answer_photo(photo=question.media_file_id, caption=text, reply_markup=keyboard)
            return
        elif q_type == "video":
            await message.answer_video(video=question.media_file_id, caption=text, reply_markup=keyboard)
            return
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("quiz_answer_"))
async def process_quiz_answer(callback: CallbackQuery, user: User):
    """Quiz javobini qayta ishlash"""
    parts = callback.data.split("_")
    question_id = int(parts[2])
    selected_option = int(parts[3])
    
    redis = await get_redis()
    cache = CacheService(redis)
    
    state = await cache.get_quiz_state(user.telegram_id)
    if not state:
        await callback.message.edit_text("⏱ Quiz muddati tugagan. Qaytadan boshlang!")
        await callback.answer()
        return
    
    current_index = state["current_index"]
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Question).where(Question.id == question_id))
        question = result.scalar_one_or_none()
        
        if not question:
            await callback.answer("Savol topilmadi!", show_alert=True)
            return
        
        is_correct = question.options[selected_option].get("is_correct", False)
        
        # Savolni yangilash
        question.times_asked += 1
        if is_correct:
            question.correct_count += 1
            state["score"] += 10
            state["correct"] += 1
        
        state["current_index"] += 1
        
        # Javob natijasi
        correct_text = next((o["text"] for o in question.options if o.get("is_correct")), "")
        if is_correct:
            result_text = f"✅ To'g'ri!\n✅ To'g'ri javob: <b>{correct_text}</b>"
        else:
            result_text = f"❌ Noto'g'ri!\n❌ To'g'ri javob: <b>{correct_text}</b>"
        if question.explanation:
            result_text += f"\n\n💡 <i>{question.explanation}</i>"
        
        await callback.message.edit_reply_markup(reply_markup=None)
        
        # Keyingi savol bormi?
        is_finished = state["current_index"] >= len(state["questions"])
        
        if not is_finished:
            next_q_id = state["questions"][state["current_index"]]
            next_q_result = await session.execute(select(Question).where(Question.id == next_q_id))
            next_question = next_q_result.scalar_one_or_none()
            
            await cache.set_quiz_state(user.telegram_id, state)
            await session.commit()
            
            await callback.message.answer(result_text)
            
            if next_question:
                await send_quiz_question(
                    callback.message, user, next_question,
                    state["current_index"] + 1, len(state["questions"]),
                    state["score"], state["correct"]
                )
        else:
            # Quiz tugadi
            xp_earned = state["correct"] * XP_PER_CORRECT
            
            # Foydalanuvchini yangilash
            db_user_result = await session.execute(select(User).where(User.id == user.id))
            db_user = db_user_result.scalar_one_or_none()
            if db_user:
                db_user.xp_points += xp_earned
                db_user.total_games += 1
                db_user.correct_answers += state["correct"]
                db_user.total_answers += len(state["questions"])
                _update_level(db_user)
            
            # Sessiyani yangilash
            quiz_result = await session.execute(
                select(QuizSession).where(QuizSession.id == state["session_id"])
            )
            quiz_session = quiz_result.scalar_one_or_none()
            if quiz_session:
                quiz_session.correct_answers = state["correct"]
                quiz_session.score = state["score"]
                quiz_session.is_completed = True
                quiz_session.xp_earned = xp_earned
                from datetime import datetime
                quiz_session.completed_at = datetime.utcnow()
            
            await session.commit()
            
            # Reytingni yangilash
            rating_service = RatingService(redis)
            await rating_service.update_score(user.telegram_id, xp_earned)
            await cache.delete_quiz_state(user.telegram_id)

            accuracy = round(state["correct"] / len(state["questions"]) * 100)
            congrats = "🏆 Ajoyib natija!" if accuracy >= 80 else "📚 Ko'proq mashq qiling!"
            correct_count = state['correct']
            total_count = len(state['questions'])
            score_val = state['score']

            await callback.message.answer(result_text)
            await callback.message.answer(
                f"🎉 <b>Quiz yakunlandi!</b>\n\n"
                f"✅ To'g'ri javoblar: <b>{correct_count}/{total_count}</b>\n"
                f"💯 Ball: <b>{score_val}</b>\n"
                f"🎯 Aniqlik: <b>{accuracy}%</b>\n"
                f"⭐ Qozonilgan XP: <b>+{xp_earned}</b>\n\n"
                f"{congrats}\n\n"
                f"Yana bir quiz ishlashni xohlaysizmi?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Qaytadan", callback_data="quiz_again")],
                    [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_main")],
                ])
            )
    
    await callback.answer()


@router.callback_query(F.data == "quiz_again")
async def quiz_again(callback: CallbackQuery, user: User):
    """Qaytadan quiz"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Category).where(Category.is_active == True))
        categories = result.scalars().all()
    
    await callback.message.edit_text(
        "🎯 Kategoriyani tanlang:",
        reply_markup=get_quiz_categories_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, user: User):
    """Bosh menyuga qaytish"""
    from bot.keyboards.main_menu import get_main_menu
    await callback.message.answer("🏠 Bosh menyu", reply_markup=get_main_menu())
    await callback.answer()


def _update_level(user: User):
    """XP asosida levelni yangilash"""
    xp = user.xp_points
    levels = [(10000, 10), (5000, 9), (2500, 8), (1200, 7), (600, 6),
              (300, 5), (150, 4), (75, 3), (30, 2)]
    user.level = 1
    for threshold, level in levels:
        if xp >= threshold:
            user.level = level
            break
