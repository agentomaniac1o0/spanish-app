"""
Spanish Learning Telegram Bot — @spanishdudebot
State machine for guided lessons, SRS reviews, translation exercises, and Hermes conversation.
"""
import os
import re
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, ContextTypes,
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://100.91.254.59:8100")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── State machine ────────────────────────────────────────────────────────────
USER_STATES: dict[int, dict] = {}


def _api(method: str, path: str, body: dict | None = None) -> dict | None:
    url = f"{BACKEND_URL}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, timeout=10)
        elif method == "POST":
            r = httpx.post(url, json=body, timeout=10)
        else:
            return None
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


# ── Fuzzy translation check ─────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Normalize text for fuzzy comparison: lowercase, strip accents, trim."""
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u", "Ü": "u", "Ñ": "n",
        "¿": "", "¡": "", "?": "", "!": "", ".": "", ",": "",
    }
    t = text.lower().strip()
    for k, v in replacements.items():
        t = t.replace(k, v)
    return " ".join(t.split())


def _check_translation(user_input: str, correct_answer: str) -> tuple[bool, str]:
    """Check if user translation matches expected answer. Returns (is_correct, feedback)."""
    norm_input = _normalize(user_input)
    norm_correct = _normalize(correct_answer)
    
    if norm_input == norm_correct:
        return True, ""

    # Handle alternative correct answers (| separated in correct_answer)
    alternatives = [a.strip() for a in correct_answer.split("|")]
    for alt in alternatives:
        if _normalize(alt) == norm_input:
            return True, ""

    # Partial match: user forgot/misspelled article
    input_parts = set(norm_input.split())
    correct_parts = set(norm_correct.split())
    if correct_parts.issubset(input_parts) or len(correct_parts & input_parts) >= len(correct_parts) * 0.8:
        return False, f"Fast! Richtig wäre: *{correct_answer}*"

    return False, f"❌ Nicht ganz. Die Antwort ist: *{correct_answer}*"


# ── Commands ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    resp = _api("POST", "/api/users/register", {
        "telegram_id": uid, "username": username,
    })
    if resp:
        USER_STATES[uid] = {
            "state": "idle", "user_id": resp["id"],
            "level": resp["current_level"], "data": {}, "step": 0, "score": 0,
        }
        if not resp.get("placement_complete"):
            await _start_placement(update, uid, resp["id"])
            return

    await update.message.reply_text(
        f"¡Hola {username}! 🇪🇸\n\n"
        f"Dein Level: *{resp['current_level']}*\n"
        f"Streak: {resp['streak']} Tage 🔥\n\n"
        f"/leccion — Neue Lektion\n"
        f"/review — Vokabeln wiederholen\n"
        f"/gramatica — Grammatik lernen\n"
        f"/hablar — Spanisch sprechen\n"
        f"/progreso — Fortschritt\n"
        f"/help — Hilfe",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Spanisch-Lehrer Bot*\n\n"
        "/start — Start/Registrierung\n"
        "/leccion — Geführte Lektion (SRS-Warmup → Übersetzen → Grammatik)\n"
        "/review — Fällige Vokabeln üben (Übersetzen + SRS)\n"
        "/gramatica — Grammatik von Hermes erklärt\n"
        "/hablar — Freies Spanisch-Gespräch\n"
        "/progreso — Lernstatistik\n"
        "/help — Diese Hilfe\n\n"
        "✏️ Bei Übersetzungen: Einfach die Antwort tippen! "
        "Artikel sind wichtig (el/la/los/las). "
        "Akzente (á,é,í,ó,ú,ñ) sind optional.",
        parse_mode="Markdown",
    )


async def progreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    if not user:
        await update.message.reply_text("Bitte zuerst /start")
        return

    stats = _api("GET", f"/api/users/{user['user_id']}/stats")
    if not stats:
        await update.message.reply_text("Statistik nicht verfügbar.")
        return

    await update.message.reply_text(
        f"📊 *Deine Lernstatistik*\n\n"
        f"Niveau: *{stats.get('level', '?')}*\n"
        f"Wörter gelernt: *{stats.get('total_words', 0)}*\n"
        f"XP: *{stats.get('xp', 0)}*\n"
        f"Streak: 🔥 *{stats.get('streak', 0)} Tage*\n"
        f"Reviews fällig: *{stats.get('due_words', 0)}*\n"
        f"Lektionen absolviert: *{stats.get('lessons_completed', 0)}*",
        parse_mode="Markdown",
    )


# ── Placement test (MC is fine for diagnostics) ─────────────────────────────

PLACEMENT_QUESTIONS = [
    {"q": "Was heißt 'Haus' auf Spanisch?", "opts": ["casa", "perro", "rojo", "agua"], "ans": 0, "lvl": "A0"},
    {"q": "Übersetze: 'Ich bin müde.'", "opts": ["Estoy cansado", "Soy cansado", "Tengo cansado", "Hay cansado"], "ans": 0, "lvl": "A1"},
    {"q": "Was bedeutet 'ayer'?", "opts": ["heute", "morgen", "gestern", "jetzt"], "ans": 2, "lvl": "A1"},
    {"q": "Welcher Satz ist korrekt?", "opts": ["El casa es grande", "La casa es grande", "Los casa es grande", "Las casa grande"], "ans": 1, "lvl": "A0"},
    {"q": "Übersetze: 'Ich habe gegessen.'", "opts": ["He comido", "Estoy comer", "Voy a comer", "Comí ayer"], "ans": 0, "lvl": "A2"},
    {"q": "Was ist der Unterschied zwischen 'por' und 'para'?", "opts": ["keiner", "por=Grund, para=Zweck", "por=Ort, para=Zeit", "por=Vergangenheit, para=Zukunft"], "ans": 1, "lvl": "A2"},
    {"q": "Übersetze: 'Wenn ich Zeit hätte, würde ich reisen.'", "opts": ["Si tengo tiempo, viajo", "Si tuviera tiempo, viajaría", "Si tenía tiempo, viajaba", "Si tendré tiempo, viajaré"], "ans": 1, "lvl": "B1"},
    {"q": "Was ist 'ojalá'?", "opts": ["Hoffentlich", "Leider", "Vielleicht", "Sicher"], "ans": 0, "lvl": "B1"},
]

async def _start_placement(update: Update, uid: int, backend_uid: int):
    USER_STATES[uid]["state"] = "placement"
    USER_STATES[uid]["step"] = 0
    USER_STATES[uid]["score"] = 0
    await _send_placement_question(update, uid)


async def _send_placement_question(update_or_query, uid: int):
    step = USER_STATES[uid]["step"]
    if step >= len(PLACEMENT_QUESTIONS):
        await _finish_placement(update_or_query, uid)
        return

    q = PLACEMENT_QUESTIONS[step]
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"place_{step}_{i}")]
        for i, opt in enumerate(q["opts"])
    ]
    text = f"📝 Frage {step + 1}/8\n\n{q['q']}"
    
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update_or_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def _finish_placement(update_or_query, uid: int):
    user = USER_STATES[uid]
    score = user["score"]
    pct = score / 8 * 100
    if pct >= 85: level = "B1"
    elif pct >= 60: level = "A2"
    elif pct >= 30: level = "A1"
    else: level = "A0"

    user["level"] = level
    user["state"] = "idle"

    msg = f"✅ Einstufungstest: *{level}* ({score}/8)\n\nStarte mit /leccion!"
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(msg, parse_mode="Markdown")


# ── Lektion flow: SRS → Übersetzen ──────────────────────────────────────────

async def leccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    if not user:
        await update.message.reply_text("Bitte zuerst /start")
        return

    # Get next lesson from backend
    lesson = _api("GET", f"/api/lessons/next?user_id={user['user_id']}")
    if not lesson:
        await update.message.reply_text("Keine neue Lektion. Nutze /review für Wiederholungen!")
        return

    # Get due words for warmup
    due_words = []
    ctx = _api("GET", f"/api/users/{user['user_id']}/context")
    if ctx:
        due_words = ctx.get("due_words", [])

    user["state"] = "lesson_warmup"
    user["data"] = {"due_words": due_words, "lesson": lesson}
    user["step"] = 0
    user["score"] = 0

    parts = []
    if due_words:
        parts.append(f"🔄 {len(due_words)} fällige Vokabeln warmup")
    parts.append(f"📖 *{lesson.get('title', 'Lektion')}* ({lesson.get('level', '?')})")
    parts.append("✏️ Übersetzungs-Übungen")
    
    await update.message.reply_text(
        f"📚 Lektion startet!\n\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(parts)),
        parse_mode="Markdown",
    )

    if due_words:
        await _send_srs(update, uid)
    else:
        user["state"] = "lesson_translate"
        user["step"] = 0
        await _load_translation_words(update, uid)


async def _send_srs(update_or_query, uid: int):
    """SRS warmup: show word, ask for difficulty rating."""
    user = USER_STATES[uid]
    step = user["step"]
    words = user["data"].get("due_words", [])

    if step >= len(words):
        user["state"] = "lesson_translate"
        user["step"] = 0
        msg = "✅ Warmup fertig!\n\nJetzt: ✏️ Übersetzen — schreib die spanische Übersetzung!"
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(msg)
        else:
            await update_or_query.edit_message_text(msg)
        await _load_translation_words(update_or_query, uid)
        return

    word = words[step]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Again", callback_data=f"srs_{word.get('word_id',0)}_{uid}_1"),
         InlineKeyboardButton("🟠 Hard", callback_data=f"srs_{word.get('word_id',0)}_{uid}_2")],
        [InlineKeyboardButton("🟢 Good", callback_data=f"srs_{word.get('word_id',0)}_{uid}_3"),
         InlineKeyboardButton("🔵 Easy", callback_data=f"srs_{word.get('word_id',0)}_{uid}_4")],
    ])
    text = f"🔄 {step + 1}/{len(words)}\n\n*{word['spanish']}*\n_{word['german']}_"
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def _load_translation_words(update_or_query, uid: int):
    """Load new words from the lesson for translation practice."""
    user = USER_STATES[uid]
    lesson = user["data"].get("lesson", {})
    level = lesson.get("level", user["level"])

    # Get words from backend API for this lesson
    words_resp = _api("GET", f"/api/lessons/{lesson.get('id', 0)}?user_id={user['user_id']}")
    if words_resp and words_resp.get("content"):
        content = words_resp["content"]
        word_list = content.get("words", [])
    else:
        word_list = []

    if not word_list:
        # Fallback: get due words for translation practice
        ctx = _api("GET", f"/api/users/{user['user_id']}/context")
        word_list = []
        if ctx:
            for w in ctx.get("due_words", []):
                word_list.append({"spanish": w["spanish"], "german": w["german"], "id": w.get("word_id", 0)})

    import random
    random.shuffle(word_list)
    user["data"]["new_words"] = word_list[:8]


async def _send_translation(update_or_query, uid: int):
    """Send next translation exercise (DE → ES)."""
    user = USER_STATES[uid]
    step = user["step"]
    words = user["data"].get("new_words", [])

    if step >= len(words):
        user["state"] = "idle"
        total = user["score"]
        msg = (
            f"🎉 Lektion abgeschlossen!\n\n"
            f"Richtig: *{total}/{len(words)}*\n\n"
            f"Neue Vokabeln sind jetzt in deinem SRS-Lernplan.\n"
            f"/leccion — Nächste Lektion\n"
            f"/review — Wiederholen\n"
            f"/progreso — Fortschritt"
        )
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update_or_query.edit_message_text(msg, parse_mode="Markdown")
        return

    word = words[step]
    # 80% of the time: DE→ES (harder, better for learning)
    # 20% of the time: ES→DE (easier, recognition)
    direction = "DE_ES"
    if step > 0 and step % 5 == 0:
        direction = "ES_DE"

    user["data"]["current_word"] = word
    user["data"]["direction"] = direction

    if direction == "DE_ES":
        prompt = f"✏️ {step + 1}/{len(words)}\n\nWie heißt *\"{word['german']}\"* auf Spanisch?"
    else:
        prompt = f"✏️ {step + 1}/{len(words)}\n\nWas bedeutet *\"{word['spanish']}\"*?"

    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(prompt, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    else:
        await update_or_query.edit_message_text(prompt, parse_mode="Markdown")

    # Send audio with native speaker voice
    word_id = word.get("id") or word.get("word_id")
    if word_id:
        audio_url = f"{BACKEND_URL}/static/audio/{word_id}.mp3"
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_audio(audio_url, title=word['spanish'])
        else:
            await update_or_query.message.reply_audio(audio_url, title=word['spanish'])


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Review mode: translation exercises for all due words."""
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    if not user:
        await update.message.reply_text("Bitte zuerst /start")
        return

    ctx = _api("GET", f"/api/users/{user['user_id']}/context")
    due_words = ctx.get("due_words", []) if ctx else []

    if not due_words:
        await update.message.reply_text("🎉 Keine fälligen Vokabeln! ¡Muy bien!")
        return

    user["state"] = "review"
    user["data"]["new_words"] = [
        {"spanish": w["spanish"], "german": w["german"], "id": w.get("word_id", 0)}
        for w in due_words
    ]
    user["step"] = 0
    user["score"] = 0
    await update.message.reply_text(f"📚 {len(due_words)} Vokabeln zum Üben!\n✏️ Schreib die Übersetzung:")
    await _send_translation(update, uid)


# ── Text handler: translation answers ────────────────────────────────────────

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    if not text:
        return

    user = USER_STATES.get(uid)
    if not user:
        await update.message.reply_text("Bitte /start für die Registrierung.")
        return

    state = user.get("state", "")
    
    if state in ("lesson_translate", "review"):
        await _handle_translation_answer(update, uid, text)
    elif state == "conversation":
        await update.message.reply_text("💬 _Hermes-Konversation folgt in Phase 3._", parse_mode="Markdown")
    else:
        await update.message.reply_text("Nutze /help um die Kommandos zu sehen.")


async def _handle_translation_answer(update: Update, uid: int, text: str):
    user = USER_STATES[uid]
    word = user["data"].get("current_word", {})
    direction = user["data"].get("direction", "DE_ES")
    
    if direction == "DE_ES":
        correct = word.get("spanish", "")
        is_correct, feedback = _check_translation(text, correct)
    else:
        correct = word.get("german", "")
        is_correct, feedback = _check_translation(text, correct)

    if is_correct:
        user["score"] += 1
        await update.message.reply_text(f"✅ ¡Correcto! ({user['score']}/{user['step'] + 1})", parse_mode="Markdown")
        # Record to SRS
        if user.get("user_id") and word.get("id"):
            _api("POST", "/api/vocab/review", {
                "user_id": user["user_id"],
                "word_id": word.get("id", 0),
                "rating": 4,  # Easy — user translated correctly
            })
    else:
        await update.message.reply_text(feedback, parse_mode="Markdown")

    user["step"] += 1
    await _send_translation(update, uid)


# ── Callback handler ─────────────────────────────────────────────────────────

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    data = query.data

    if data.startswith("place_"):
        await _handle_placement(query, uid, data)
    elif data.startswith("srs_"):
        await _handle_srs(query, uid, data)


async def _handle_placement(query, uid: int, data: str):
    _, step_str, ans_str = data.split("_")
    step = int(step_str)
    answer = int(ans_str)
    correct = PLACEMENT_QUESTIONS[step]["ans"]

    user = USER_STATES[uid]
    if answer == correct:
        user["score"] += 1
    user["step"] = step + 1
    await _send_placement_question(query, uid)


async def _handle_srs(query, uid: int, data: str):
    _, word_id_str, state_uid_str, rating_str = data.split("_")
    word_id = int(word_id_str)
    rating = int(rating_str)

    user = USER_STATES.get(uid)
    if user and user.get("user_id"):
        _api("POST", "/api/vocab/review", {
            "user_id": user["user_id"],
            "word_id": word_id,
            "rating": rating,
        })

    user["step"] += 1
    await _send_srs(query, uid)


# ── Conversation / Grammar placeholders ──────────────────────────────────────

async def hablar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Konversations-Modus*\n\n"
        "Schreib mir auf Spanisch! Hermes (dein KI-Lehrer) "
        "wird dich bald korrigieren und mit dir sprechen.\n\n"
        "_Phase 3 folgt in Kürze._",
        parse_mode="Markdown",
    )


async def gramatica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    level = user["level"] if user else "A1"

    grammar = _api("GET", f"/api/grammar/{level}")
    if grammar and isinstance(grammar, list) and grammar:
        g = grammar[0]
        examples = ""
        if g.get("examples"):
            for ex in g["examples"]:
                examples += f"• *{ex['spanish']}* — {ex['german']}\n"
        await update.message.reply_text(
            f"📖 *{g['title']}* ({level})\n\n{g['explanation']}\n\n"
            f"{examples}\n"
            f"_Mehr live-Grammatik via Hermes folgt in Phase 3._",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("Grammatik via Hermes folgt in Phase 3!")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("leccion", leccion))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("gramatica", gramatica))
    app.add_handler(CommandHandler("hablar", hablar))
    app.add_handler(CommandHandler("progreso", progreso))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    app.run_polling()


if __name__ == "__main__":
    main()
