"""
Spanish Learning Telegram Bot — @spanishdudebot
State machine for guided lessons, SRS reviews, and Hermes conversation handoff.
"""
import os
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, ContextTypes,
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://100.91.254.59:8100")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── State machine ────────────────────────────────────────────────────────────
# Per-user state tracked in memory. Keys: telegram user_id.
# Each state: {
#   "state": str,        # "idle", "placement", "lesson_warmup", "lesson_vocab",
#                         # "lesson_grammar", "review", "conversation"
#   "user_id": int,      # Backend user ID
#   "level": str,        # A0–B2
#   "data": dict,        # Current lesson/vocab data
#   "step": int,         # Current step in flow
#   "score": int,        # Running score
# }
USER_STATES: dict[int, dict] = {}


def _api(method: str, path: str, body: dict | None = None) -> dict | None:
    """Call the Spanish Backend API."""
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


# ── Commands ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register user and show welcome."""
    uid = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    # Register via backend
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
        "/leccion — Geführte Lektion (Warmup → Vokabeln → Grammatik → Konversation)\n"
        "/review — Fällige Vokabeln (SRS)\n"
        "/gramatica — Grammatik von Hermes erklärt\n"
        "/hablar — Freies Spanisch-Gespräch\n"
        "/progreso — Lernstatistik\n"
        "/help — Diese Hilfe",
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


# ── Placement test ──────────────────────────────────────────────────────────

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
    text = f"📝 Frage {step + 1}/{len(PLACEMENT_QUESTIONS)}\n\n{q['q']}"
    
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update_or_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def _finish_placement(update_or_query, uid: int):
    user = USER_STATES[uid]
    score = user["score"]
    total = len(PLACEMENT_QUESTIONS)
    pct = score / total * 100

    if pct >= 85: level = "B1"
    elif pct >= 60: level = "A2"
    elif pct >= 30: level = "A1"
    else: level = "A0"

    user["level"] = level
    user["state"] = "idle"

    # Update backend
    _api("POST", "/api/placement/answer", {
        "user_id": user["user_id"],
        "score": score,
        "total": total,
        "level": level,
    })

    msg = f"✅ Einstufungstest abgeschlossen!\n\nDein Niveau: *{level}*\n({score}/{total} richtig)"
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(msg, parse_mode="Markdown")


# ── Lektion flow ────────────────────────────────────────────────────────────

async def leccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    if not user:
        await update.message.reply_text("Bitte zuerst /start")
        return

    # Get next lesson from backend
    lesson = _api("GET", f"/api/lessons/next?user_id={user['user_id']}")
    if not lesson:
        await update.message.reply_text("Keine neue Lektion verfügbar. Nutze /review für Wiederholungen!")
        return

    user["state"] = "lesson_warmup"
    user["data"] = lesson
    user["step"] = 0

    await update.message.reply_text(
        f"📖 *{lesson['title']}*\nLevel: {lesson['level']} | Unit: {lesson['unit']}\n\n"
        f"Die Lektion hat 3 Teile:\n1️⃣ Warmup (SRS-Review)\n2️⃣ Neue Vokabeln\n3️⃣ Grammatik\n\n"
        f"Lass uns starten! 🚀",
        parse_mode="Markdown",
    )
    # Start warmup
    await _start_warmup(update, uid)


async def _start_warmup(update: Update, uid: int):
    user = USER_STATES[uid]
    user["state"] = "lesson_warmup"
    user["step"] = 0

    due = _api("GET", f"/api/users/{user['user_id']}/context")
    due_words = due.get("due_words", []) if due else []

    if not due_words:
        user["state"] = "lesson_vocab"
        await update.message.reply_text("Keine fälligen Reviews — direkt zu neuen Vokabeln! 📝")
        return

    user["data"]["due_words"] = due_words
    await _send_warmup_word(update, uid)


async def _send_warmup_word(update: Update, uid: int):
    user = USER_STATES[uid]
    step = user["step"]
    words = user["data"].get("due_words", [])

    if step >= len(words):
        user["state"] = "lesson_vocab"
        user["step"] = 0
        await update.message.reply_text(
            f"✅ Warmup abgeschlossen! ({len(words)} Vokabeln)\n\nJetzt: Neue Vokabeln lernen!",
        )
        return

    word = words[step]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Again", callback_data=f"srs_{word['id']}_1"),
         InlineKeyboardButton("🟠 Hard", callback_data=f"srs_{word['id']}_2")],
        [InlineKeyboardButton("🟢 Good", callback_data=f"srs_{word['id']}_3"),
         InlineKeyboardButton("🔵 Easy", callback_data=f"srs_{word['id']}_4")],
    ])
    await update.message.reply_text(
        f"🔄 Review {step + 1}/{len(words)}\n\n*{word['spanish']}*",
        reply_markup=keyboard, parse_mode="Markdown",
    )


# ── SRS review ──────────────────────────────────────────────────────────────

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    if not user:
        await update.message.reply_text("Bitte zuerst /start")
        return

    due = _api("GET", f"/api/users/{user['user_id']}/context")
    due_words = due.get("due_words", []) if due else []

    if not due_words:
        await update.message.reply_text("🎉 Keine fälligen Vokabeln! Alles im Griff.")
        return

    user["state"] = "review"
    user["step"] = 0
    user["data"]["due_words"] = due_words
    await update.message.reply_text(f"📚 {len(due_words)} fällige Vokabeln. Los geht's!")
    await _send_warmup_word(update, uid)


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
    _, word_id_str, rating_str = data.split("_")
    word_id = int(word_id_str)
    rating = int(rating_str)

    user = USER_STATES[uid]
    if user.get("user_id"):
        _api("POST", "/api/vocab/review", {
            "user_id": user["user_id"],
            "word_id": word_id,
            "rating": rating,
        })

    user["step"] += 1
    if user["state"] == "lesson_warmup":
        await _send_warmup_word(query, uid)
    elif user["state"] == "review":
        await _send_warmup_word(query, uid)


# ── Conversation / Grammar via Hermes (skeleton) ────────────────────────────

async def hablar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Konversations-Modus*\n\n"
        "Schreib mir auf Spanisch und ich korrigiere dich! "
        "Hermes (dein KI-Spanischlehrer) übernimmt gleich.\n\n"
        "_Phase 3: Hermes-Integration folgt in Kürze._",
        parse_mode="Markdown",
    )


async def gramatica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    level = user["level"] if user else "A1"

    grammar = _api("GET", f"/api/grammar/{level}")
    if grammar and isinstance(grammar, list) and grammar:
        g = grammar[0]
        await update.message.reply_text(
            f"📖 *{g['title']}* ({level})\n\n{g['explanation']}\n\n"
            f"Mehr Grammatik: Hermes erklärt live in Kürze!",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "Grammatik-Erklärungen folgen in Phase 3 via Hermes!",
        )


# ── Text handler ────────────────────────────────────────────────────────────

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    if not text:
        return

    # Check for Spanish text in conversation mode
    user = USER_STATES.get(uid)
    if user and user.get("state") == "conversation":
        await update.message.reply_text(
            f"📝 _Deine Nachricht:_ {text}\n\n"
            "_Hermes-Konversation folgt in Phase 3._",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "Nutze /help um die Kommandos zu sehen.",
        )


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("leccion", leccion))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("gramatica", gramatica))
    app.add_handler(CommandHandler("hablar", hablar))
    app.add_handler(CommandHandler("progreso", progreso))

    # Callbacks (inline keyboard)
    app.add_handler(CallbackQueryHandler(on_callback))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    app.run_polling()


if __name__ == "__main__":
    main()
