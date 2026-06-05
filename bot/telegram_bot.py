"""
Spanish Learning Telegram Bot — @spanishdudebot
"""
import os, re, json, httpx, random
from dotenv import load_dotenv
load_dotenv()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, ContextTypes,
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://100.91.254.59:8100")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

USER_STATES: dict[int, dict] = {}


def _api(method: str, path: str, body: dict | None = None) -> dict | None:
    url = f"{BACKEND_URL}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, timeout=10)
        else:
            r = httpx.post(url, json=body, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def _normalize(text: str) -> str:
    reps = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n",
            "Á":"a","É":"e","Í":"i","Ó":"o","Ú":"u","Ü":"u","Ñ":"n",
            "¿":"","¡":"","?":"","!":"",",":"",".":""}
    t = text.lower().strip()
    for k,v in reps.items():
        t = t.replace(k,v)
    return " ".join(t.split())


def _check_translation(user_input: str, correct: str) -> tuple[bool, str]:
    ni = _normalize(user_input)
    for alt in correct.split("|"):
        if _normalize(alt.strip()) == ni:
            return True, ""
    return False, f"Fast! Richtig: *{correct}*"


def _load_words(user_id: int, level: str, count: int = 10) -> list[dict]:
    """Load words for a user from backend. Auto-assigns new words if needed."""
    # First try getting due words
    ctx = _api("GET", f"/api/users/{user_id}/context")
    words = []
    if ctx:
        words = ctx.get("due_words", [])
    if words:
        return words[:count]

    # No due words — assign new words from curriculum
    resp = _api("POST", "/api/vocab/assign", {
        "user_id": user_id, "level": level, "count": count,
    })
    if resp and resp.get("words"):
        return resp["words"]
    return []


# ── Commands ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    resp = _api("POST", "/api/users/register", {
        "telegram_id": uid, "username": username,
    })
    if not resp:
        await update.message.reply_text("Fehler bei Registrierung.")
        return

    USER_STATES[uid] = {
        "state": "idle", "user_id": resp["id"],
        "level": resp["current_level"], "data": {}, "step": 0, "score": 0,
    }
    if not resp.get("placement_complete"):
        await _start_placement(update, uid, resp["id"])
        return

    await update.message.reply_text(
        f"¡Hola {username}! 🇪🇸\n\nLevel: *{resp['current_level']}*\n\n"
        "/leccion — Neue Lektion\n/review — Wiederholen\n"
        "/gramatica — Grammatik\n/hablar — Sprechen\n/progreso — Fortschritt",
        parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Spanisch-Lehrer*\n\n"
        "/leccion — Lektion (SRS → Übersetzen)\n"
        "/review — Fällige Vokabeln üben\n"
        "/gramatica — Grammatik\n"
        "/hablar — Konversation\n"
        "/progreso — Statistik\n\n"
        "✏️ Übersetzen: Einfach die Antwort tippen!\n"
        "🔊 Jede Vokabel hat ein Audio (Muttersprachler)",
        parse_mode="Markdown")


async def progreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = USER_STATES.get(uid)
    if not user:
        await update.message.reply_text("Bitte zuerst /start"); return

    stats = _api("GET", f"/api/users/{user['user_id']}/stats")
    if not stats:
        await update.message.reply_text("Statistik nicht verfügbar."); return

    await update.message.reply_text(
        f"📊 *Statistik*\n\nNiveau: *{stats.get('level','?')}*\n"
        f"Wörter: *{stats.get('total_words',0)}*\n"
        f"XP: *{stats.get('xp',0)}*\n"
        f"Streak: 🔥 *{stats.get('streak',0)} Tage*\n"
        f"Fällig: *{stats.get('due_words',0)}*\n"
        f"Lektionen: *{stats.get('lessons_completed',0)}*",
        parse_mode="Markdown")


# ── Placement (MC) ──────────────────────────────────────────────────────────

PLACEMENT_QUESTIONS = [
    {"q":"Was heißt 'Haus' auf Spanisch?","o":["casa","perro","rojo","agua"],"a":0},
    {"q":"Übersetze: 'Ich bin müde.'","o":["Estoy cansado","Soy cansado","Tengo cansado","Hay cansado"],"a":0},
    {"q":"Was bedeutet 'ayer'?","o":["heute","morgen","gestern","jetzt"],"a":2},
    {"q":"Welcher Satz ist korrekt?","o":["El casa es grande","La casa es grande","Los casa es grande","Las casa grande"],"a":1},
    {"q":"'Ich habe gegessen.'","o":["He comido","Estoy comer","Voy a comer","Comí ayer"],"a":0},
    {"q":"Por vs Para — Unterschied?","o":["keiner","por=Grund, para=Zweck","por=Ort, para=Zeit","por=Vergangenheit, para=Zukunft"],"a":1},
    {"q":"'Wenn ich Zeit hätte, würde ich reisen.'","o":["Si tengo tiempo, viajo","Si tuviera tiempo, viajaría","Si tenía tiempo, viajaba","Si tendré tiempo, viajaré"],"a":1},
    {"q":"Was ist 'ojalá'?","o":["Hoffentlich","Leider","Vielleicht","Sicher"],"a":0},
]

async def _start_placement(update: Update, uid: int, backend_uid: int):
    USER_STATES[uid].update({"state":"placement","step":0,"score":0})
    await _send_placement_question(update, uid)

async def _send_placement_question(update_or_query, uid: int):
    step = USER_STATES[uid]["step"]
    if step >= len(PLACEMENT_QUESTIONS):
        await _finish_placement(update_or_query, uid); return

    q = PLACEMENT_QUESTIONS[step]
    kb = [[InlineKeyboardButton(o, callback_data=f"pl_{step}_{i}")] for i,o in enumerate(q["o"])]
    text = f"📝 Frage {step+1}/8\n\n{q['q']}"
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update_or_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def _finish_placement(update_or_query, uid: int):
    u = USER_STATES[uid]
    pct = u["score"]/8*100
    if pct >= 85: level = "B1"
    elif pct >= 60: level = "A2"
    elif pct >= 30: level = "A1"
    else: level = "A0"
    u["level"] = level; u["state"] = "idle"
    msg = f"✅ Einstufungstest: *{level}* ({u['score']}/8)\n\nStarte mit /leccion!"
    if hasattr(update_or_query,'message'):
        await update_or_query.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(msg, parse_mode="Markdown")


# ── Lektion + Review (shared translation engine) ────────────────────────────

async def leccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = USER_STATES.get(uid)
    if not u:
        await update.message.reply_text("Bitte zuerst /start"); return

    words = _load_words(u["user_id"], u["level"], 10)
    if not words:
        await update.message.reply_text("Keine Wörter verfügbar. Bitte warte auf Curriculum-Update.")
        return

    # Split: first 5 for SRS warmup, all 10 for translation
    due_words = words[:5]

    u["state"] = "lesson_warmup"
    u["data"] = {"due_words": due_words, "lesson_words": words}
    u["step"] = 0; u["score"] = 0

    await update.message.reply_text(
        f"📚 Lektion ({u['level']})\n\n"
        f"1️⃣ SRS-Warmup: {len(due_words)} Wörter\n"
        f"2️⃣ Übersetzen: {len(words)} Wörter\n\n"
        f"Los geht's!", parse_mode="Markdown")

    await _send_srs(update, uid)


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = USER_STATES.get(uid)
    if not u:
        await update.message.reply_text("Bitte zuerst /start"); return

    words = _load_words(u["user_id"], u["level"], 10)
    if not words:
        await update.message.reply_text("🎉 Keine Vokabeln fällig! ¡Muy bien!\n\nNutze /leccion für neue Wörter.")
        return

    u["state"] = "review"
    u["data"] = {"lesson_words": words}
    u["step"] = 0; u["score"] = 0

    await update.message.reply_text(
        f"📚 {len(words)} Vokabeln zum Üben!\n✏️ Schreib die Übersetzung.\n"
        f"🔊 Tipp: Jede Vokabel kommt mit Audio.",
        parse_mode="Markdown")
    u["state"] = "review"
    await _send_translation(update, uid)


async def _send_srs(update_or_query, uid: int):
    u = USER_STATES[uid]
    step = u["step"]
    words = u["data"].get("due_words", [])

    if step >= len(words):
        # Move to translation phase
        u["state"] = "lesson_translate" if u["state"] == "lesson_warmup" else "review"
        u["step"] = 0
        msg = "✅ Warmup fertig!\n\n✏️ Jetzt übersetzen!"
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(msg)
        else:
            await update_or_query.edit_message_text(msg)
        await _send_translation(update_or_query, uid)
        return

    w = words[step]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 🔴 Again", callback_data=f"srs_{w.get('word_id',0)}_{uid}_1"),
         InlineKeyboardButton("2 🟠 Hard", callback_data=f"srs_{w.get('word_id',0)}_{uid}_2")],
        [InlineKeyboardButton("3 🟢 Good", callback_data=f"srs_{w.get('word_id',0)}_{uid}_3"),
         InlineKeyboardButton("4 🔵 Easy", callback_data=f"srs_{w.get('word_id',0)}_{uid}_4")],
    ])
    text = (f"🔄 SRS {step+1}/{len(words)}\n\n*{w['spanish']}*\n_{w.get('german','')}_\n\n"
            f"Wie gut kanntest du das Wort?\n"
            f"(Falls Buttons nicht gehen: 1-4 tippen)")

    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def _send_translation(update_or_query, uid: int):
    u = USER_STATES[uid]
    step = u["step"]
    words = u["data"].get("lesson_words", [])

    if step >= len(words):
        u["state"] = "idle"
        msg = (f"🎉 Abgeschlossen!\n\nRichtig: *{u['score']}/{len(words)}*\n\n"
               f"/leccion — Nächste Lektion\n/review — Wiederholen\n/progreso — Fortschritt")
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update_or_query.edit_message_text(msg, parse_mode="Markdown")
        return

    w = words[step]
    direction = "ES_DE" if step > 0 and step % 4 == 0 else "DE_ES"
    u["data"]["_cur"] = w
    u["data"]["_dir"] = direction

    if direction == "DE_ES":
        prompt = f"✏️ {step+1}/{len(words)}\n\nWie heißt *\"{w.get('german','')}\"* auf Spanisch?"
    else:
        prompt = f"✏️ {step+1}/{len(words)}\n\nWas bedeutet *\"{w.get('spanish','')}\"*?"

    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(prompt, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    else:
        await update_or_query.edit_message_text(prompt, parse_mode="Markdown")


# ── Text handler: SRS numbers + translation answers ─────────────────────────

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""
    if not text: return

    u = USER_STATES.get(uid)
    if not u:
        await update.message.reply_text("Bitte /start"); return

    state = u.get("state", "")

    # SRS number fallback (1-4)
    if state == "lesson_warmup" and text in ("1","2","3","4"):
        w = u["data"].get("due_words", [])
        step = u["step"]
        if step < len(w):
            rating = int(text)
            wid = w[step].get("word_id", 0)
            if u.get("user_id") and wid:
                _api("POST", "/api/vocab/review", {"user_id": u["user_id"], "word_id": wid, "rating": rating})
            u["step"] += 1
            await _send_srs(update, uid)
        return

    # Translation answer
    if state in ("lesson_translate", "review"):
        w = u["data"].get("_cur", {})
        direction = u["data"].get("_dir", "DE_ES")

        if direction == "DE_ES":
            correct = w.get("spanish", "")
            ok, fb = _check_translation(text, correct)
        else:
            correct = w.get("german", "")
            ok, fb = _check_translation(text, correct)

        if ok:
            u["score"] += 1
            await update.message.reply_text(f"✅ ¡Correcto! ({u['score']}/{u['step']+1})", parse_mode="Markdown")
            wid = w.get("word_id") or w.get("id", 0)
            if u.get("user_id") and wid:
                _api("POST", "/api/vocab/review", {"user_id": u["user_id"], "word_id": wid, "rating": 4})
        else:
            await update.message.reply_text(f"❌ {fb}", parse_mode="Markdown")

        # Send audio AFTER answer (reinforcement)
        wid = w.get("word_id") or w.get("id", 0)
        if wid:
            try:
                await update.message.reply_audio(
                    f"{BACKEND_URL}/static/audio/{wid}.mp3",
                    title=w.get('spanish',''),
                    caption=f"🔊 {w.get('spanish','')}"
                )
            except Exception:
                pass

        u["step"] += 1
        await _send_translation(update, uid)
        return

    # Conversation / fallback
    if state == "conversation":
        await update.message.reply_text("💬 Hermes-Konversation folgt in Phase 3.")
    else:
        await update.message.reply_text("Nutze /help für Kommandos.")


# ── Callback handler ─────────────────────────────────────────────────────────

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    data = query.data

    if data.startswith("pl_"):
        _, step, ans = data.split("_")
        if PLACEMENT_QUESTIONS[int(step)]["a"] == int(ans):
            USER_STATES[uid]["score"] += 1
        USER_STATES[uid]["step"] = int(step) + 1
        await _send_placement_question(query, uid)

    elif data.startswith("srs_"):
        _, wid, uid_str, rating = data.split("_")
        word_id = int(wid)
        r = int(rating)
        u = USER_STATES.get(uid)
        if u and u.get("user_id"):
            _api("POST", "/api/vocab/review", {"user_id": u["user_id"], "word_id": word_id, "rating": r})
        u["step"] += 1
        await _send_srs(query, uid)


# ── Grammar / Conversation placeholders ─────────────────────────────────────

async def gramatica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = USER_STATES.get(uid)
    level = u["level"] if u else "A1"
    g = _api("GET", f"/api/grammar/{level}")
    if g and isinstance(g, list) and g:
        g = g[0]
        ex = "\n".join(f"• {e['spanish']} — {e['german']}" for e in g.get("examples",[]))
        await update.message.reply_text(f"📖 *{g['title']}*\n\n{g['explanation']}\n\n{ex}", parse_mode="Markdown")
    else:
        await update.message.reply_text("Grammatik via Hermes folgt in Phase 3!")

async def hablar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💬 Hermes-Konversation folgt in Phase 3!")


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
