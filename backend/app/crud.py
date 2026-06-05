import json
from datetime import date
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.curriculum import GRAMMAR_POINTS, LESSONS, PLACEMENT_QUESTIONS, WORDS
from app.models import GrammarPoint, Lesson, User, UserLesson, UserWord, Word
from app.srs import schedule_review, seeding_card


async def get_or_create_user(db: AsyncSession, telegram_id: int, username: Optional[str] = None):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username, created_at=date.today().isoformat())
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_user_progress(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    if not user:
        return None

    result = await db.execute(
        select(func.count()).select_from(UserWord).where(
            UserWord.user_id == user_id,
            UserWord.next_review <= date.today().isoformat(),
        )
    )
    words_due = result.scalar() or 0

    result = await db.execute(select(func.count()).select_from(UserLesson).where(UserLesson.user_id == user_id))
    lessons_completed = result.scalar() or 0

    result = await db.execute(select(func.count()).select_from(Lesson).where(Lesson.level <= user.current_level))
    total_lessons = result.scalar() or 0

    return {
        "user_id": user.id,
        "level": user.current_level,
        "xp": user.xp,
        "streak": user.streak,
        "total_words_learned": user.total_words_learned,
        "words_due_today": words_due,
        "lessons_completed": lessons_completed,
        "total_lessons": total_lessons,
    }


async def get_due_words(db: AsyncSession, user_id: int, limit: int = 10):
    result = await db.execute(
        select(UserWord, Word)
        .join(Word, UserWord.word_id == Word.id)
        .where(
            UserWord.user_id == user_id,
            UserWord.next_review <= date.today().isoformat(),
        )
        .order_by(UserWord.difficulty.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "word_id": word.id,
            "spanish": word.spanish,
            "german": word.german,
            "state": uw.state,
            "stability": uw.stability,
            "difficulty": uw.difficulty,
            "next_review": uw.next_review,
        }
        for uw, word in rows
    ]


async def review_word(db: AsyncSession, user_id: int, word_id: int, rating: int):
    result = await db.execute(
        select(UserWord).where(UserWord.user_id == user_id, UserWord.word_id == word_id)
    )
    uw = result.scalar_one_or_none()
    if not uw:
        return None

    today = date.today().isoformat()
    params = schedule_review(
        state=uw.state,
        stability=uw.stability,
        difficulty=uw.difficulty,
        elapsed_days=uw.elapsed_days,
        scheduled_days=uw.scheduled_days,
        rating=rating,
        review_date_str=today,
    )

    uw.state = params["state"]
    uw.stability = params["stability"]
    uw.difficulty = params["difficulty"]
    uw.elapsed_days = params["elapsed_days"]
    uw.scheduled_days = params["scheduled_days"]
    uw.reps += params["reps"]
    uw.lapses += params["lapses"]
    uw.last_review = today
    uw.next_review = params["next_review"]

    if rating >= 3 and uw.state == 0:
        user = await db.get(User, user_id)
        if user and user.id:
            user.total_words_learned += 1

    await db.commit()
    return params


async def assign_words_to_user(db: AsyncSession, user_id: int, word_ids: list[int]):
    for wid in word_ids:
        result = await db.execute(
            select(UserWord).where(UserWord.user_id == user_id, UserWord.word_id == wid)
        )
        if result.scalar_one_or_none() is None:
            card = seeding_card(wid)
            uw = UserWord(user_id=user_id, word_id=wid, **card)
            db.add(uw)
    await db.commit()


async def get_words_by_lesson(db: AsyncSession, lesson_id: int):
    result = await db.execute(select(Word))
    return result.scalars().all()


async def get_next_lesson(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    if not user:
        return None

    result = await db.execute(
        select(Lesson.id).join(UserLesson, (UserLesson.lesson_id == Lesson.id) & (UserLesson.user_id == user_id))
    )
    completed_ids = set(row[0] for row in result.all())

    result = await db.execute(
        select(Lesson)
        .where(Lesson.level == user.current_level, Lesson.id.notin_(completed_ids) if completed_ids else True)
        .order_by(Lesson.sort_order)
        .limit(1)
    )
    lesson = result.scalar_one_or_none()

    if lesson is None:
        next_levels = {"A0": "A1", "A1": "A2", "A2": "B1", "B1": "B2"}
        next_level = next_levels.get(user.current_level)
        if next_level:
            result = await db.execute(
                select(Lesson).where(Lesson.level == next_level).order_by(Lesson.sort_order).limit(1)
            )
            lesson = result.scalar_one_or_none()
            if lesson:
                user.current_level = next_level
                await db.commit()

    return lesson


async def complete_lesson(db: AsyncSession, user_id: int, lesson_id: int, score: int, time_spent: int):
    result = await db.execute(
        select(UserLesson).where(UserLesson.user_id == user_id, UserLesson.lesson_id == lesson_id)
    )
    ul = result.scalar_one_or_none()
    if ul is None:
        ul = UserLesson(user_id=user_id, lesson_id=lesson_id)
    ul.completed_at = date.today().isoformat()
    ul.score = score
    ul.time_spent = time_spent
    db.add(ul)

    user = await db.get(User, user_id)
    if user:
        user.xp += max(10, score)
        _update_streak(user)
    await db.commit()


async def get_lesson_content(db: AsyncSession, lesson_id: int):
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        return None
    content = json.loads(lesson.content_json) if lesson.content_json else {}
    return {
        "id": lesson.id,
        "title": lesson.title,
        "level": lesson.level,
        "unit": lesson.unit,
        "lesson_type": lesson.lesson_type,
        "content": content,
    }


async def get_lesson_list(db: AsyncSession, user_id: int):
    result = await db.execute(select(Lesson).order_by(Lesson.level, Lesson.sort_order))
    lessons = result.scalars().all()

    result = await db.execute(select(UserLesson.lesson_id).where(UserLesson.user_id == user_id))
    completed_ids = set(row[0] for row in result.all())

    return [
        {
            "id": l.id,
            "title": l.title,
            "level": l.level,
            "unit": l.unit,
            "lesson_type": l.lesson_type,
            "completed": l.id in completed_ids,
        }
        for l in lessons
    ]


async def get_grammar_points(db: AsyncSession, level: Optional[str] = None):
    query = select(GrammarPoint).order_by(GrammarPoint.level, GrammarPoint.sort_order)
    if level:
        query = query.where(GrammarPoint.level == level)
    result = await db.execute(query)
    points = result.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "level": p.level,
            "explanation": p.explanation,
            "examples": json.loads(p.examples_json) if p.examples_json else [],
        }
        for p in points
    ]


async def get_conversation_context(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    if not user:
        return None

    result = await db.execute(
        select(Word.spanish).join(UserWord, Word.id == UserWord.word_id).where(
            UserWord.user_id == user_id, UserWord.state >= 2
        ).limit(30)
    )
    known_sample = [row[0] for row in result.all()]

    result = await db.execute(
        select(UserLesson.lesson_id).where(UserLesson.user_id == user_id).order_by(UserLesson.completed_at.desc()).limit(3)
    )
    recent_lesson_ids = [row[0] for row in result.all()]
    recent_units = []
    if recent_lesson_ids:
        result = await db.execute(
            select(Lesson.unit).where(Lesson.id.in_(recent_lesson_ids))
        )
        recent_units = list(set(row[0] for row in result.all()))

    result = await db.execute(
        select(GrammarPoint.title).where(GrammarPoint.level <= user.current_level).order_by(GrammarPoint.level, GrammarPoint.sort_order)
    )
    grammar_covered = [row[0] for row in result.all()]

    return {
        "user_id": user.id,
        "level": user.current_level,
        "known_words_count": len(known_sample),
        "known_words_sample": known_sample,
        "recent_units": recent_units,
        "grammar_covered": grammar_covered,
        "streak": user.streak,
    }


async def get_placement_question(index: int):
    if 0 <= index < len(PLACEMENT_QUESTIONS):
        q = PLACEMENT_QUESTIONS[index]
        return {"question_id": index, "spanish": q["spanish"], "options": q["options"]}
    return None


async def submit_placement_answer(answers: list[dict]):
    if not answers:
        return {"assigned_level": "A0", "score": 0, "total_questions": 0}

    correct = 0
    max_level = "A0"
    level_order = {"A0": 0, "A1": 1, "A2": 2, "B1": 3, "B2": 4}

    for ans in answers:
        qid = ans.get("question_id", 0)
        chosen = ans.get("chosen_index", -1)
        if 0 <= qid < len(PLACEMENT_QUESTIONS):
            q = PLACEMENT_QUESTIONS[qid]
            if chosen == q["correct_index"]:
                correct += 1
                if level_order.get(q["level_hint"], 0) > level_order.get(max_level, 0):
                    max_level = q["level_hint"]

    score = int((correct / len(PLACEMENT_QUESTIONS)) * 100)
    assigned = "A1" if max_level == "A0" else max_level

    ratio = correct / len(PLACEMENT_QUESTIONS)
    if ratio <= 0.3:
        assigned = "A0"
    elif ratio <= 0.6:
        assigned = max(assigned, "A1") if level_order.get(assigned, 0) <= 1 else "A1"
    elif ratio <= 0.85:
        assigned = max(assigned, "A2") if level_order.get(assigned, 0) <= 2 else "A2"

    return {"assigned_level": assigned, "score": score, "total_questions": len(PLACEMENT_QUESTIONS)}


async def get_stats(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    if not user:
        return None

    progress = await get_user_progress(db, user_id)

    result = await db.execute(
        select(UserWord.state, func.count()).where(UserWord.user_id == user_id).group_by(UserWord.state)
    )
    state_map = {0: "neu", 1: "lernend", 2: "gelernt", 3: "wiederholend"}
    words_by_state = {state_map.get(row[0], str(row[0])): row[1] for row in result.all()}

    return {
        "user_id": user.id,
        "level": user.current_level,
        "xp": user.xp,
        "streak": user.streak,
        "total_words_learned": user.total_words_learned,
        "words_due_today": progress["words_due_today"],
        "lessons_completed": progress["lessons_completed"],
        "total_lessons": progress["total_lessons"],
        "words_by_state": words_by_state,
        "last_active_date": user.last_active_date,
    }


async def check_level_progression(db: AsyncSession, user_id: int) -> dict | None:
    """Prüft ob der User das aktuelle Level gemeistert hat und aufsteigen kann.
    
    Kriterien:
    - ≥80% der Wörter des aktuellen Levels sind "stabil" (FSRS stability > 21 Tage)
    - Mindestens 3 Lektionen des aktuellen Levels abgeschlossen
    - Mindestens 1 Konversation (vocab source = "conversation") vorhanden
    
    Returns: {"can_advance": bool, "new_level": str, "stats": dict} or None
    """
    user = await db.get(User, user_id)
    if not user:
        return None

    level_order = {"A0": 0, "A1": 1, "A2": 2, "B1": 3, "B2": 4}
    current_idx = level_order.get(user.current_level, 0)
    
    # Count words at current level
    result = await db.execute(
        select(func.count()).select_from(Word).where(Word.level == user.current_level)
    )
    total_words_at_level = result.scalar() or 0
    if total_words_at_level == 0:
        return {"can_advance": False, "current_level": user.current_level, "stats": {}}

    # Count stable words (FSRS stability > 21 days)
    result = await db.execute(
        select(func.count())
        .select_from(UserWord)
        .join(Word, UserWord.word_id == Word.id)
        .where(
            UserWord.user_id == user_id,
            Word.level == user.current_level,
            UserWord.state == 2,
            UserWord.stability > 21,
        )
    )
    stable_words = result.scalar() or 0
    word_pct = stable_words / total_words_at_level * 100 if total_words_at_level else 0

    # Count completed lessons at current level
    result = await db.execute(
        select(func.count())
        .select_from(UserLesson)
        .join(Lesson, UserLesson.lesson_id == Lesson.id)
        .where(
            UserLesson.user_id == user_id,
            Lesson.level == user.current_level,
        )
    )
    lessons_completed = result.scalar() or 0

    # Count conversation-based vocabulary
    result = await db.execute(
        select(func.count()).select_from(UserWord).where(
            UserWord.user_id == user_id,
            UserWord.source == "conversation",
        )
    )
    convos = result.scalar() or 0

    # Count due words (indicates remaining work)
    result = await db.execute(
        select(func.count())
        .select_from(UserWord)
        .join(Word, UserWord.word_id == Word.id)
        .where(
            UserWord.user_id == user_id,
            Word.level == user.current_level,
            UserWord.next_review <= date.today().isoformat(),
        )
    )
    due_words = result.scalar() or 0

    stats = {
        "total_words_at_level": total_words_at_level,
        "stable_words": stable_words,
        "stable_pct": round(word_pct, 1),
        "lessons_completed": lessons_completed,
        "conversation_words": convos,
        "words_due": due_words,
    }

    can_advance = word_pct >= 80 and lessons_completed >= 3

    new_level = None
    if can_advance:
        next_levels = {"A0": "A1", "A1": "A2", "A2": "B1", "B1": "B2", "B2": None}
        new_level = next_levels.get(user.current_level)
        if new_level:
            user.current_level = new_level
            user.xp += 100
            await db.commit()

    return {
        "can_advance": can_advance,
        "current_level": user.current_level,
        "new_level": new_level,
        "stats": stats,
        "next_words": total_words_at_level - stable_words,
        "missing": {
            "words_needed": max(0, int(total_words_at_level * 0.8) - stable_words),
            "lessons_needed": max(0, 3 - lessons_completed),
        },
    }


def _update_streak(user: User):
    today = date.today().isoformat()
    if user.last_active_date == today:
        return
    yesterday = date.today()
    yesterday = yesterday.replace(day=yesterday.day - 1).isoformat()
    if user.last_active_date == yesterday:
        user.streak += 1
    else:
        user.streak = 1
    user.last_active_date = today


async def seed_database(db: AsyncSession):
    result = await db.execute(select(func.count()).select_from(Word))
    if result.scalar() > 0:
        return

    for w in WORDS:
        db.add(Word(**w))

    for l in LESSONS:
        db.add(Lesson(**l))

    for g in GRAMMAR_POINTS:
        db.add(GrammarPoint(**g))

    await db.commit()
