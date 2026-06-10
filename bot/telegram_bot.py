"""
Spanish Learning Telegram Bot — @spanishdudebot
"""
import asyncio
import logging
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, ContextTypes,
)

from image_gen import generate_word_image, word_image_exists

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
    except Exception as e:
        logger.error("API call failed: %s %s — %s", method, url, e)
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
    ctx = _api("GET", f"/api/users/{user_id}/context")
    words = ctx.get("due_words", []) if ctx else []
    if len(words) < count:
        needed = count - len(words)
        resp = _api("POST", "/api/vocab/assign", {
            "user_id": user_id, "level": level, "count": needed,
        })
        if resp and resp.get("words"):
            words.extend(resp["words"])
    return words[:count]


def _load_review_words(user_id: int, level: str) -> list[dict]:
    """Load words for /review: due words + previously failed words, filtered by level, no new assignments."""
    ctx = _api("GET", f"/api/users/{user_id}/context")
    due = ctx.get("due_words", []) if ctx else []

    max_level = "A1" if level in ("A0", "A1") else "A2"
    failed = _api("GET", f"/api/vocab/failed?user_id={user_id}&max_level={max_level}&limit=15")
    failed = failed if failed else []

    word_ids = set()
    words = []
    for w in due + failed:
        wid = w.get("word_id", 0)
        if wid and wid not in word_ids:
            word_ids.add(wid)
            words.append(w)

    if not words:
        due_all = _api("GET", f"/api/vocab/due?user_id={user_id}&limit=10")
        if due_all:
            words = due_all

    return words[:10]


def _get_picture_words(words: list[dict]) -> list[dict]:
    """Return words that will trigger picture mode (every 3rd starting from index 2)."""
    return [w for i, w in enumerate(words) if i > 1 and i % 3 == 0]


async def _build_lesson_plan(update: Update, uid: int, user_id: int, level: str) -> dict | None:
    """Load words and pre-generate any missing images. Show progress in chat."""
    words = _load_words(user_id, level, 10)
    if not words:
        return None

    picture_words = _get_picture_words(words)
    missing = [w for w in picture_words if w.get("word_id") and not word_image_exists(w["word_id"])]

    if missing:
        msg = await update.message.reply_text(
            f"🎨 *Erstelle Bilder...* (0/{len(missing)})",
            parse_mode="Markdown")
        for i, w in enumerate(missing):
            try:
                await msg.edit_text(
                    f"🎨 *Erstelle Bilder...* ({i+1}/{len(missing)})\n"
                    f"_Zeichne: {w['spanish']} — {w.get('german','')}_",
                    parse_mode="Markdown")
                ok = await asyncio.to_thread(
                    generate_word_image, w["word_id"], w["spanish"], w.get("german", ""),
                    upload_stock=True)
                if not ok:
                    logger.warning("Bild fehlgeschlagen: %s (%d)", w["spanish"], w["word_id"])
            except Exception as e:
                logger.error("Bild-Generierung abgebrochen: %s", e)
        await msg.edit_text("✅ *Bilder fertig!* Los geht's!", parse_mode="Markdown")

    return {"words": words, "picture_words": picture_words, "missing": missing}


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
        "🔊 Audio: Button neben der Antwort drücken",
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

    plan = await _build_lesson_plan(update, uid, u["user_id"], u["level"])
    if not plan:
        await update.message.reply_text("Keine Wörter verfügbar. Bitte warte auf Curriculum-Update.")
        return

    words = plan["words"]
    due_words = words[:5]

    u["state"] = "lesson_warmup"
    u["data"] = {"due_words": due_words, "lesson_words": words}
    u["step"] = 0; u["score"] = 0

    await update.message.reply_text(
        f"📚 *Lektion ({u['level']})*\n\n"
        f"1️⃣ SRS-Warmup: {len(due_words)} Wörter\n"
        f"2️⃣ Übersetzen: {len(words)} Wörter\n\n"
        f"Los geht's!", parse_mode="Markdown")

    units = set(w.get("unit", "") for w in words if w.get("unit"))
    if units:
        unit_name = list(units)[0]
        try:
            img_data = httpx.get(f"{BACKEND_URL}/static/units/unit_{unit_name}.jpg", timeout=5).content
            await update.message.reply_photo(img_data, caption=f"📖 Unit: {unit_name}")
        except Exception as e:
            logger.warning("Unit image load failed: %s", e)

    await _send_srs(update, uid)


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = USER_STATES.get(uid)
    if not u:
        await update.message.reply_text("Bitte zuerst /start"); return

    words = _load_review_words(u["user_id"], u["level"])
    if not words:
        await update.message.reply_text("🎉 Keine Vokabeln fällig! ¡Muy bien!\n\nNutze /leccion für neue Wörter.")
        return

    u["state"] = "review"
    u["data"] = {"lesson_words": words}
    u["step"] = 0; u["score"] = 0

    await update.message.reply_text(
        f"📚 *{len(words)} Vokabeln zum Üben!*\n"
        f"✏️ Schreib die Übersetzung.\n"
        f"🔊 Tipp: Audio-Button neben der Antwort drücken.",
        parse_mode="Markdown")

    units = set(w.get("unit", "") for w in words if w.get("unit"))
    if units:
        unit_name = list(units)[0]
        try:
            img_data = httpx.get(f"{BACKEND_URL}/static/units/unit_{unit_name}.jpg", timeout=5).content
            await update.message.reply_photo(img_data, caption=f"📖 Unit: {unit_name}")
        except Exception as e:
            logger.warning("Unit image load failed: %s", e)

    await _send_translation(update, uid)


async def _send_srs(update_or_query, uid: int):
    u = USER_STATES[uid]
    step = u["step"]
    words = u["data"].get("due_words", [])

    if step >= len(words):
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
        total = len(words)
        msg = (f"🎉 *Abgeschlossen!*\n\nRichtig: *{u['score']}/{total}*\n\n"
               f"/leccion — Nächste Lektion\n/review — Wiederholen\n/progreso — Fortschritt")
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update_or_query.edit_message_text(msg, parse_mode="Markdown")
        return

    w = words[step]
    direction = "ES_DE" if step > 0 and step % 4 == 0 else "DE_ES"
    picture_mode = step > 1 and step % 3 == 0

    u["data"]["_cur"] = w
    u["data"]["_dir"] = direction
    u["data"]["_pic"] = picture_mode

    if picture_mode:
        prompt = f"🖼️ {step+1}/{len(words)}\n\n¿Qué ves en esta imagen?\n_Beschreibe auf Spanisch was du siehst!_"
    elif direction == "DE_ES":
        prompt = f"✏️ {step+1}/{len(words)}\n\nWie heißt *\"{w.get('german','')}\"* auf Spanisch?"
    else:
        prompt = f"✏️ {step+1}/{len(words)}\n\nWas bedeutet *\"{w.get('spanish','')}\"*?"

    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(prompt, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    else:
        await update_or_query.edit_message_text(prompt, parse_mode="Markdown")

    # Send word-specific image for picture mode
    if picture_mode:
        wid = w.get("word_id", 0)
        unit = w.get("unit", "")
        img_sent = False
        if wid:
            try:
                img_url = f"{BACKEND_URL}/static/words/word_{wid}.jpg"
                img_data = httpx.get(img_url, timeout=5).content
                if hasattr(update_or_query, 'message'):
                    await update_or_query.message.reply_photo(img_data, caption="🇪🇸 ¡Descríbeme esta imagen!")
                else:
                    await update_or_query.message.reply_photo(img_data, caption="🇪🇸 ¡Descríbeme esta imagen!")
                img_sent = True
            except Exception as e:
                logger.warning("Word image not found for %d: %s", wid, e)
        if not img_sent and unit:
            try:
                img_data = httpx.get(f"{BACKEND_URL}/static/units/unit_{unit}.jpg", timeout=5).content
                if hasattr(update_or_query, 'message'):
                    await update_or_query.message.reply_photo(img_data, caption="🇪🇸 ¡Descríbeme esta imagen! (Unit)")
                else:
                    await update_or_query.message.reply_photo(img_data, caption="🇪🇸 ¡Descríbeme esta imagen! (Unit)")
            except Exception as e:
                logger.warning("Unit image fallback failed: %s", e)


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
        is_picture = u["data"].get("_pic", False)

        if is_picture:
            correct = w.get("spanish", "")
            ok, fb = _check_translation(text, correct)
            wid = w.get("word_id") or w.get("id", 0)
            if ok:
                u["score"] += 1
                if u.get("user_id") and wid:
                    _api("POST", "/api/vocab/review", {"user_id": u["user_id"], "word_id": wid, "rating": 4})
                kb = _audio_button(wid)
                await update.message.reply_text(
                    f"🖼️ ¡Correcto! ({u['score']}/{u['step']+1})",
                    reply_markup=kb)
            else:
                kb = _audio_button(wid)
                await update.message.reply_text(
                    f"🖼️ Fast! Richtig: *{correct}* — _\"{w.get('german', '')}\"_\n"
                    f"Deine Antwort: {text}",
                    reply_markup=kb, parse_mode="Markdown")
        elif direction == "DE_ES":
            correct = w.get("spanish", "")
            ok, fb = _check_translation(text, correct)
        else:
            correct = w.get("german", "")
            ok, fb = _check_translation(text, correct)

        if not is_picture:
            wid = w.get("word_id") or w.get("id", 0)
            if ok:
                u["score"] += 1
                if u.get("user_id") and wid:
                    _api("POST", "/api/vocab/review", {"user_id": u["user_id"], "word_id": wid, "rating": 4})
                kb = _audio_button(wid)
                await update.message.reply_text(
                    f"✅ ¡Correcto! ({u['score']}/{u['step']+1})",
                    reply_markup=kb)
            else:
                if u.get("user_id") and wid:
                    _api("POST", "/api/vocab/review", {"user_id": u["user_id"], "word_id": wid, "rating": 1})
                w_copy = dict(w)
                w_copy["_retry"] = w.get("_retry", 0) + 1
                if w_copy["_retry"] <= 2:
                    u["data"]["lesson_words"].append(w_copy)
                kb = _audio_button(wid)
                await update.message.reply_text(f"❌ {fb}", reply_markup=kb, parse_mode="Markdown")

        u["step"] += 1
        await _send_translation(update, uid)
        return

    # Conversation / fallback
    if state == "conversation":
        await update.message.reply_text("💬 Hermes-Konversation folgt in Phase 3.")
    else:
        await update.message.reply_text("Nutze /help für Kommandos.")


def _audio_button(word_id: int) -> InlineKeyboardMarkup | None:
    if not word_id:
        return None
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔊 Audio", callback_data=f"audio_{word_id}")
    ]])


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

    elif data.startswith("audio_"):
        word_id = int(data.split("_")[1])
        await query.edit_message_reply_markup(reply_markup=None)
        try:
            audio_url = f"{BACKEND_URL}/static/audio/{word_id}.mp3"
            audio_data = httpx.get(audio_url, timeout=5).content
            u = USER_STATES.get(uid)
            w = u["data"].get("_cur", {}) if u else {}
            await query.message.reply_audio(
                audio_data,
                title=w.get('spanish',''),
                caption=f"🔊 {w.get('spanish','')}",
                filename=f"{w.get('spanish','')}.mp3"
            )
        except Exception as e:
            logger.warning("Audio button failed: %s", e)


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


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = USER_STATES.get(uid)
    if u:
        u["state"] = "idle"
        u["step"] = 0
        u["data"] = {}
    await update.message.reply_text(
        "⏹️ *Lektion beendet.*\n\n"
        "Dein Fortschritt wurde gespeichert.\n"
        "/leccion — Neue Lektion\n"
        "/review — Wiederholen\n"
        "/progreso — Statistik",
        parse_mode="Markdown")


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
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.run_polling()

if __name__ == "__main__":
    main()
