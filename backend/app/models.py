from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    current_level = Column(String, default="A0")
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_active_date = Column(String)
    total_words_learned = Column(Integer, default=0)
    placement_complete = Column(Boolean, default=False)
    created_at = Column(String)


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spanish = Column(String, nullable=False)
    german = Column(String, nullable=False)
    word_type = Column(String, default="noun")
    level = Column(String, default="A0")
    unit = Column(String, default="general")
    example_sentence = Column(Text)
    example_translation = Column(Text)


class UserWord(Base):
    __tablename__ = "user_words"

    user_id = Column(Integer, primary_key=True)
    word_id = Column(Integer, primary_key=True)
    state = Column(Integer, default=0)
    stability = Column(Float, default=0.0)
    difficulty = Column(Float, default=0.0)
    elapsed_days = Column(Float, default=0.0)
    scheduled_days = Column(Float, default=0.0)
    reps = Column(Integer, default=0)
    lapses = Column(Integer, default=0)
    last_review = Column(String)
    next_review = Column(String)
    source = Column(String, default="lesson")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    level = Column(String, default="A0")
    unit = Column(String, default="general")
    lesson_type = Column(String, default="vocab")
    sort_order = Column(Integer, default=0)
    content_json = Column(Text)


class UserLesson(Base):
    __tablename__ = "user_lessons"

    user_id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, primary_key=True)
    completed_at = Column(String)
    score = Column(Integer)
    time_spent = Column(Integer)


class GrammarPoint(Base):
    __tablename__ = "grammar_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    level = Column(String, default="A0")
    explanation = Column(Text)
    examples_json = Column(Text)
    sort_order = Column(Integer, default=0)
