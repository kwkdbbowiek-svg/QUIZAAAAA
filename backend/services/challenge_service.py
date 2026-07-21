"""
Challenge xizmati — avtomatik boshlash, yakunlash va g'oliblarni aniqlash
"""

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.base import AsyncSessionLocal
from shared.database.models import (
    Challenge, ChallengeParticipant, ChallengeStatus,
    User, Transaction, TransactionType
)

logger = logging.getLogger(__name__)


async def pay_winners(challenge: Challenge, session: AsyncSession):
    """
    Challenge tugaganda g'oliblarga pul to'lash.
    Ishtirokchilar score bo'yicha tartiblangan, 1-2-3 o'rinlarga foizlar taqsimlanadi.
    """
    if challenge.winners_paid:
        return

    # Ishtirokchilarni score va vaqt bo'yicha tartiblash
    result = await session.execute(
        select(ChallengeParticipant)
        .where(ChallengeParticipant.challenge_id == challenge.id)
        .order_by(
            ChallengeParticipant.score.desc(),
            ChallengeParticipant.time_spent.asc()
        )
    )
    participants = result.scalars().all()

    if not participants:
        return

    # O'rinlarni belgilash
    for rank, participant in enumerate(participants, 1):
        participant.final_rank = rank

    prize_pool = challenge.prize_pool
    prizes = {
        1: prize_pool * challenge.first_place_percent / 100,
        2: prize_pool * challenge.second_place_percent / 100,
        3: prize_pool * challenge.third_place_percent / 100,
    }

    # G'oliblarga pul berish
    for rank, prize in prizes.items():
        if rank - 1 < len(participants) and prize > 0:
            participant = participants[rank - 1]
            participant.prize_earned = prize

            # Foydalanuvchi balansini yangilash
            user_result = await session.execute(
                select(User).where(User.id == participant.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                balance_before = user.balance
                user.balance += prize
                user.total_winnings += prize

                # Tranzaksiya yozish
                tx = Transaction(
                    user_id=user.id,
                    type=TransactionType.CHALLENGE_WIN,
                    amount=prize,
                    balance_before=balance_before,
                    balance_after=user.balance,
                    description=f"Challenge yutuq ({rank}-o'rin): {challenge.title}",
                    reference_id=challenge.id,
                )
                session.add(tx)
                logger.info(f"G'olib: {user.full_name} - {rank}-o'rin - {prize} so'm")

    challenge.winners_paid = True
    challenge.status = ChallengeStatus.FINISHED
    await session.commit()
    logger.info(f"Challenge {challenge.id} yakunlandi, g'oliblarga pul to'landi")


async def finish_challenge(challenge_id: int):
    """Challengeni yakunlash"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Challenge).where(Challenge.id == challenge_id)
        )
        challenge = result.scalar_one_or_none()
        if not challenge or challenge.winners_paid:
            return
        await pay_winners(challenge, session)


async def start_challenge(challenge_id: int):
    """Challengeni boshlash"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Challenge).where(Challenge.id == challenge_id)
        )
        challenge = result.scalar_one_or_none()
        if challenge and challenge.status == ChallengeStatus.UPCOMING:
            challenge.status = ChallengeStatus.ACTIVE
            await session.commit()
            logger.info(f"Challenge {challenge_id} boshlandi")


class ChallengeScheduler:
    """
    Challengelarni avtomatik boshlash va yakunlash scheduler'i
    """

    def __init__(self):
        self._running = False

    async def run(self):
        self._running = True
        logger.info("⏰ Challenge scheduler ishga tushdi")
        while self._running:
            try:
                await self._check_challenges()
            except Exception as e:
                logger.error(f"Scheduler xatosi: {e}")
            await asyncio.sleep(30)  # Har 30 soniyada tekshirish

    async def _check_challenges(self):
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            # Boshlash vaqti kelgan challengelar
            upcoming = await session.execute(
                select(Challenge).where(
                    and_(
                        Challenge.status == ChallengeStatus.UPCOMING,
                        Challenge.starts_at <= now,
                        Challenge.starts_at.isnot(None)
                    )
                )
            )
            for ch in upcoming.scalars().all():
                ch.status = ChallengeStatus.ACTIVE
                logger.info(f"Challenge boshlandi: {ch.title}")

            # Yakunlanish vaqti kelgan challengelar
            active = await session.execute(
                select(Challenge).where(
                    and_(
                        Challenge.status == ChallengeStatus.ACTIVE,
                        Challenge.ends_at <= now,
                        Challenge.ends_at.isnot(None)
                    )
                )
            )
            challenges_to_finish = active.scalars().all()
            await session.commit()

        # G'oliblarga pul to'lash
        for ch in challenges_to_finish:
            await finish_challenge(ch.id)

    def stop(self):
        self._running = False
