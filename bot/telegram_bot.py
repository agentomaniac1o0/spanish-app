"""
Spanish Learning Telegram Bot.

Uses python-telegram-bot for async conversation handling.
Connects to the Spanish Backend API for lesson/vocab data.
Uses OpenRouter for AI-powered explanations and conversation practice.
"""

import json
import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

from bot.config import (
    BACKEND_URL,
    BACKEND_API_KEY,
    TELEGRAM_BOT_TOKEN,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)

USER_STATES: dict[int, dict] = {}


async def api_request(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {}
        if BACKEND_API_KEY:
            headers["X-API-Key"] = BACKEND_API_KEY
        url = f"{BACKEND_URL}{path}"
        resp = await client.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()


async def llm_chat(messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800,
            },
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await api_request("POST", "/api/users/register", json={
        "telegram_id": user.id,
        "username": user.username or "",
    })

    text = (
        f"Hola {user.first_name}!\n\n"
        "Willkommen bei deinem Spanisch-Lernprogramm.\n\n"
        "*/leccion* - Naechste Lektion starten\n"
        "*/review* - Faellige Vokabeln wiederholen\n"
        "*/gramatica* - Grammatik erklaert bekommen\n"
        "*/hablar* - Freie Konversation ueben\n"
        "*/progreso* - Lernstatistik anzeigen\n"
        "*/help* - Alle Kommandos"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Lektion starten", callback_data="cmd_leccion"),
        InlineKeyboardButton("Vokabeln", callback_data="cmd_review"),
    ], [
        InlineKeyboardButton("Fortschritt", callback_data="cmd_progreso"),
        InlineKeyboardButton("Einstufungstest", callback_data="cmd_placement"),
    ]])

    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)


async def leccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = await api_request("GET", f"/api/lessons/next?user_id={user.id}")

    if isinstance(data, dict) and "detail" in data:
        await update.message.reply_text(data["detail"])
        return

    title = data.get("title", "Lektion")
    content = data.get("content", {})
    lesson_type = content.get("type", "vocab")
    intro = content.get("intro", "")

    msg = f"*{title}*\n\n{intro}\n\n"

    if lesson_type == "dialogue":
        scenes = content.get("scenes", [])
        for s in scenes:
            msg += f"*{s['speaker']}:* {s['spanish']}\n_{s['german']}_\n\n"

    elif lesson_type == "vocab":
        words = content.get("words", [])
        for w in words:
            msg += f"- *{w['spanish']}* - {w['german']}\n"

    elif lesson_type == "grammar":
        examples = content.get("examples", [])
        for ex in examples:
            msg += f"- {ex['spanish']}\n  _{ex['german']}_ ({ex.get('tense', '')})\n\n"

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Fertig", callback_data=f"complete|{data['id']}"),
        InlineKeyboardButton("Erklaeren", callback_data=f"explain|{data['id']}"),
    ]])

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    words = await api_request("GET", f"/api/vocab/due?user_id={user.id}&limit=5")

    if not words:
        await update.message.reply_text("Keine faelligen Vokabeln! Gut gemacht.")
        return

    word = words[0]
    user_state = USER_STATES.setdefault(user.id, {})
    user_state["review_queue"] = words
    user_state["review_index"] = 0

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Wieder (1)", callback_data="rate_1"),
        InlineKeyboardButton("Schwer (2)", callback_data="rate_2"),
        InlineKeyboardButton("Gut (3)", callback_data="rate_3"),
        InlineKeyboardButton("Leicht (4)", callback_data="rate_4"),
    ]])

    await update.message.reply_text(
        f"*{word['spanish']}*\n\n_({word['german']})_\n\nWie gut kanntest du das Wort?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


async def gramatica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    progress = await api_request("GET", f"/api/users/{user.id}/progress")
    level = progress.get("level", "A0")

    points = await api_request("GET", f"/api/conversation/grammar?level={level}")
    if not points:
        await update.message.reply_text("Keine Grammatik-Punkte fuer dein Level gefunden.")
        return

    p = points[0]
    msg = f"*{p['title']}* ({p['level']})\n\n{p.get('explanation', '')}\n\n"

    examples = p.get("examples", [])
    if examples:
        msg += "*Beispiele:*\n"
        for ex in examples[:3]:
            msg += f"- {ex['spanish']}\n  _{ex['german']}_\n\n"

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Naechster Punkt", callback_data="grammar_next"),
    ]])

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def hablar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context_data = await api_request("GET", f"/api/conversation/context?user_id={user.id}")

    level = context_data["level"]
    known = ", ".join(context_data["known_words_sample"][:10])

    system_prompt = (
        f"Du bist ein freundlicher Spanisch-Lehrer. Dein Schueler ist auf Level {level}.\n"
        f"Bekannte Woerter: {known}.\n"
        "Regeln:\n"
        "- Sprich NUR Spanisch, es sei denn der Schueler fragt explizit auf Deutsch.\n"
        f"- Passe dein Vokabular an Level {level} an.\n"
        "- Wenn der Schueler einen Fehler macht, korrigiere ihn sanft und erklaere die Regel.\n"
        "- Stelle Fragen, um die Konversation am Laufen zu halten.\n"
        "- Halte Saetze kurz und klar."
    )

    user_state = USER_STATES.setdefault(user.id, {})
    user_state["conversation_mode"] = True
    user_state["conversation_history"] = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "Hola! Soy tu profesor de espanol. De que quieres hablar hoy? (Du kannst auf Deutsch oder Spanisch antworten)"},
    ]

    await update.message.reply_text(
        "*Konversations-Modus aktiviert!*\n\n"
        "Hola! Soy tu profesor de espanol. De que quieres hablar hoy?\n"
        "_Schreibe /stop um den Modus zu verlassen._",
        parse_mode=ParseMode.MARKDOWN,
    )


async def progreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = await api_request("GET", f"/api/conversation/stats?user_id={user.id}")

    emoji_level = {"A0": "-", "A1": "-", "A2": "-", "B1": "-", "B2": "-"}
    level_emoji = emoji_level.get(stats["level"], ">>")

    msg = f"{level_emoji} *Dein Fortschritt*\n\n"
    msg += f"Level: *{stats['level']}*\n"
    msg += f"XP: *{stats['xp']}*\n"
    msg += f"Streak: *{stats['streak']}* Tage\n"
    msg += f"Gelernte Woerter: *{stats['total_words_learned']}*\n"
    msg += f"Faellig heute: *{stats['words_due_today']}*\n"
    msg += f"Lektionen: *{stats['lessons_completed']}* / {stats['total_lessons']}\n\n"

    ws = stats.get("words_by_state", {})
    msg += f"Neu: {ws.get('neu', 0)} | Lernend: {ws.get('lernend', 0)} | Gelernt: {ws.get('gelernt', 0)}\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Spanisch-Lernprogramm*\n\n"
        "*/leccion* - Naechste Lektion starten\n"
        "*/review* - Faellige Vokabeln (SRS)\n"
        "*/gramatica* - Grammatik erklaert\n"
        "*/hablar* - Freie Konversation\n"
        "*/progreso* - Lernstatistik\n"
        "*/test* - Einstufungstest\n"
        "*/stop* - Konversation beenden",
        parse_mode=ParseMode.MARKDOWN,
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state = USER_STATES.get(update.effective_user.id, {})
    user_state.clear()
    await update.message.reply_text("Modus beendet. /leccion oder /review zum Weitermachen.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    if data.startswith("cmd_"):
        cmd = data[4:]
        if cmd == "leccion":
            await leccion(update, context)
        elif cmd == "review":
            await review(update, context)
        elif cmd == "progreso":
            await progreso(update, context)
        elif cmd == "placement":
            await query.message.reply_text("Einstufungstest: /test")
        return

    if data.startswith("rate_"):
        rating = int(data.split("_")[1])
        user_state = USER_STATES.get(user.id, {})
        queue = user_state.get("review_queue", [])
        idx = user_state.get("review_index", 0)

        if idx < len(queue):
            word = queue[idx]
            await api_request("POST", f"/api/vocab/review?user_id={user.id}", json={
                "word_id": word["word_id"],
                "rating": rating,
            })

            idx += 1
            user_state["review_index"] = idx

            if idx < len(queue):
                next_word = queue[idx]
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("Wieder (1)", callback_data="rate_1"),
                    InlineKeyboardButton("Schwer (2)", callback_data="rate_2"),
                    InlineKeyboardButton("Gut (3)", callback_data="rate_3"),
                    InlineKeyboardButton("Leicht (4)", callback_data="rate_4"),
                ]])
                await query.edit_message_text(
                    f"*{next_word['spanish']}*\n\n_({next_word['german']})_\n\nWie gut kanntest du das Wort?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                )
            else:
                await query.edit_message_text("Review fertig! Gut gemacht.")
                user_state.pop("review_queue", None)
                user_state.pop("review_index", None)

        return

    if data.startswith("complete|"):
        lesson_id = int(data.split("|")[1])
        await api_request("POST", f"/api/lessons/{lesson_id}/complete?user_id={user.id}", json={
            "score": 100,
            "time_spent": 120,
        })
        await query.edit_message_text(query.message.text + "\n\n*Lektion abgeschlossen!*", parse_mode=ParseMode.MARKDOWN)

    if data.startswith("explain|"):
        lesson_id = int(data.split("|")[1])
        lesson = await api_request("GET", f"/api/lessons/{lesson_id}")
        content = lesson.get("content", {})

        messages = [
            {"role": "system", "content": "Du bist ein hilfreicher Spanisch-Lehrer. Erklaere die folgende Lektion auf Deutsch."},
            {"role": "user", "content": f"Erklaere diese Spanisch-Lektion: {json.dumps(content, ensure_ascii=False)}"},
        ]
        explanation = await llm_chat(messages)
        await query.message.reply_text(explanation)

    if data == "grammar_next":
        await gramatica(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_state = USER_STATES.get(user.id, {})

    if user_state.get("conversation_mode"):
        user_msg = update.message.text
        history = user_state.get("conversation_history", [])
        history.append({"role": "user", "content": user_msg})

        await update.message.chat.send_action("typing")
        reply = await llm_chat(history)
        history.append({"role": "assistant", "content": reply})
        user_state["conversation_history"] = history[-12:]

        await update.message.reply_text(reply)


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leccion", leccion))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("gramatica", gramatica))
    app.add_handler(CommandHandler("hablar", hablar))
    app.add_handler(CommandHandler("progreso", progreso))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Spanish bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
