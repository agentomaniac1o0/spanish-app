from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    telegram_id: int
    username: Optional[str]
    current_level: str
    xp: int
    streak: int
    last_active_date: Optional[str]
    total_words_learned: int
    placement_complete: bool
    created_at: Optional[str]


class UserRegister(BaseModel):
    telegram_id: int
    username: Optional[str] = None


class UserProgress(BaseModel):
    user_id: int
    level: str
    xp: int
    streak: int
    total_words_learned: int
    words_due_today: int
    lessons_completed: int
    total_lessons: int


class WordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    spanish: str
    german: str
    word_type: str
    level: str
    unit: str
    example_sentence: Optional[str]
    example_translation: Optional[str]


class UserWordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    word_id: int
    spanish: str
    german: str
    state: int
    stability: float
    difficulty: float
    next_review: Optional[str]


class UserWordReview(BaseModel):
    word_id: int
    rating: int  # 1=Again, 2=Hard, 3=Good, 4=Easy


class PlacementQuestion(BaseModel):
    question_id: int
    spanish: str
    options: list[str]
    correct_index: int
    level_hint: str


class PlacementAnswer(BaseModel):
    question_id: int
    chosen_index: int
    response_time_ms: int


class PlacementResult(BaseModel):
    assigned_level: str
    score: int
    total_questions: int


class LessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    level: str
    unit: str
    lesson_type: str
    content: Optional[dict] = None


class LessonComplete(BaseModel):
    score: int
    time_spent: int


class LessonSummary(BaseModel):
    id: int
    title: str
    level: str
    unit: str
    lesson_type: str
    completed: bool


class GrammarPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    level: str
    explanation: Optional[str]
    examples: Optional[list] = None


class ConversationContext(BaseModel):
    user_id: int
    level: str
    known_words_count: int
    known_words_sample: list[str]
    recent_units: list[str]
    grammar_covered: list[str]
    streak: int


class StatsResponse(BaseModel):
    user_id: int
    level: str
    xp: int
    streak: int
    total_words_learned: int
    words_due_today: int
    lessons_completed: int
    total_lessons: int
    words_by_state: dict[str, int]
    last_active_date: Optional[str]
