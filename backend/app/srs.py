"""
FSRS v5 — Free Spaced Repetition Scheduler

Implementation based on:
https://github.com/open-spaced-repetition/py-fsrs
https://github.com/open-spaced-repetition/fsrs4anki/wiki/FSRSv5

Default weights from FSRS v5 benchmark (optimal for ~90% retention).
"""

import math
from datetime import date, datetime, timedelta


DECAY = -0.5
FACTOR = 19 / 81

DEFAULT_WEIGHTS = [
    0.4072, 1.1829, 3.1262, 15.4722,
    7.2102, 0.5316, 1.0651, 0.0234,
    1.6160, 0.1544, 1.0824, 1.9813,
    0.0953, 0.2975, 2.2042,
]

STATE_NEW = 0
STATE_LEARNING = 1
STATE_REVIEW = 2
STATE_RELEARNING = 3

RATING_AGAIN = 1
RATING_HARD = 2
RATING_GOOD = 3
RATING_EASY = 4


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _date_diff(d1: str, d2: str) -> float:
    try:
        dt1 = datetime.fromisoformat(d1).date()
        dt2 = datetime.fromisoformat(d2).date()
        return (dt2 - dt1).days
    except (ValueError, TypeError):
        return 0.0


def initial_stability(rating: int) -> float:
    if rating == RATING_AGAIN:
        return 0.0
    return max(0.1, _clamp(DEFAULT_WEIGHTS[rating - 2], 0.1, 36500.0))


def initial_difficulty(rating: int) -> float:
    d = _clamp(DEFAULT_WEIGHTS[4] - (rating - 3) * DEFAULT_WEIGHTS[5], 1.0, 10.0)
    return d


def _mean_reversion(init: float, current: float) -> float:
    return DEFAULT_WEIGHTS[7] * init + (1 - DEFAULT_WEIGHTS[7]) * current


def next_difficulty(d: float, rating: int) -> float:
    delta_d = -DEFAULT_WEIGHTS[6] * (rating - 3.0)
    d_prime = d + delta_d
    d_prime = _mean_reversion(initial_difficulty(RATING_GOOD), d_prime)
    return _clamp(d_prime, 1.0, 10.0)


def next_stability(d: float, s: float, rating: int):
    hard_penalty = DEFAULT_WEIGHTS[15] if rating == RATING_HARD else 1.0
    easy_bonus = DEFAULT_WEIGHTS[15] if rating == RATING_EASY else 1.0

    s = s * (1 + FACTOR * (11 - d) * (s ** DECAY) * (math.exp(DEFAULT_WEIGHTS[8]) * (1 - easy_bonus) - 1))

    if rating == RATING_AGAIN:
        s = s * DEFAULT_WEIGHTS[9] * math.exp(DEFAULT_WEIGHTS[10] * (11 - d)) * (s ** -DECAY)
    elif rating == RATING_HARD:
        s = s * DEFAULT_WEIGHTS[9] * math.exp(DEFAULT_WEIGHTS[10] * (11 - d)) * (s ** -DECAY) * hard_penalty

    s = _clamp(s, 0.01, 36500.0)
    return s


def next_forget_stability(d: float, s: float):
    return DEFAULT_WEIGHTS[11] * (d ** -DECAY) * ((s + 1) ** DECAY) - 1


def next_recall_stability(d: float, s: float, rating: int):
    if rating == RATING_AGAIN:
        return next_forget_stability(d, s)
    return next_stability(d, s, rating)


def next_state(old_state: int, rating: int) -> int:
    if old_state == STATE_NEW:
        if rating == RATING_AGAIN:
            return STATE_LEARNING
        return STATE_REVIEW
    if old_state == STATE_LEARNING:
        if rating in (RATING_AGAIN, RATING_HARD):
            return STATE_LEARNING
        if rating == RATING_GOOD:
            return STATE_REVIEW
        return STATE_REVIEW
    if old_state == STATE_REVIEW:
        if rating == RATING_AGAIN:
            return STATE_RELEARNING
        return STATE_REVIEW
    if old_state == STATE_RELEARNING:
        if rating in (RATING_AGAIN, RATING_HARD):
            return STATE_RELEARNING
        if rating == RATING_GOOD:
            return STATE_REVIEW
        return STATE_REVIEW
    return STATE_REVIEW


def schedule_review(state: int, stability: float, difficulty: float,
                    elapsed_days: float, scheduled_days: float,
                    rating: int, review_date_str: str):
    if rating == RATING_AGAIN:
        reps = 0
        lapses = 1
    else:
        reps = 1
        lapses = 0

    new_state = next_state(state, rating)

    if state == STATE_NEW:
        new_difficulty = initial_difficulty(rating)
        new_stability = initial_stability(rating)
    elif rating == RATING_AGAIN:
        new_difficulty = next_difficulty(difficulty, rating)
        new_stability = next_forget_stability(difficulty, stability)
    else:
        new_difficulty = next_difficulty(difficulty, rating)
        new_stability = next_recall_stability(difficulty, stability, rating)

    interval = max(1, round(new_stability * 9.0 * (1.0 / (new_difficulty ** 2.0))))

    try:
        review_date = datetime.fromisoformat(review_date_str).date()
    except (ValueError, TypeError):
        review_date = date.today()

    next_review = review_date + timedelta(days=interval)

    return {
        "state": new_state,
        "stability": round(new_stability, 4),
        "difficulty": round(new_difficulty, 4),
        "elapsed_days": float(interval),
        "scheduled_days": float(interval),
        "reps": reps,
        "lapses": lapses,
        "last_review": review_date_str,
        "next_review": next_review.isoformat(),
    }


def seeding_card(word_id: int) -> dict:
    today = date.today()
    return {
        "word_id": word_id,
        "state": STATE_NEW,
        "stability": 0.0,
        "difficulty": 0.0,
        "elapsed_days": 0.0,
        "scheduled_days": 0.0,
        "reps": 0,
        "lapses": 0,
        "last_review": None,
        "next_review": today.isoformat(),
    }
