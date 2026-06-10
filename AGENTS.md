# spanish-app — AGENTS.md

## Overview

Spanish learning app with AI teacher via Telegram. Hybrid: structured lessons + free conversation practice with Hermes. Adaptive placement test, FSRS spaced repetition.

## Architecture

- **Backend:** FastAPI on VM 101, port 8100, systemd user unit
- **Bot:** python-telegram-bot on VM 101, systemd user unit
- **DB:** SQLite via SQLAlchemy 2.0 + aiosqlite
- **AI:** OpenRouter DeepSeek V4 Flash (same as Hermes)
- **Hermes:** LXC 105, SSH bridge for conversation mode

## Code Conventions

| Sprach | Skill | Wann laden |
|--------|-------|------------|
| Python (Backend) | `/python-conventions` | FastAPI, async SQLAlchemy, Pydantic v2 |
| | `/code-quality` | Nach jeder Code-Generierung |
| Tests | `/testing-conventions` | pytest für Bot + Backend |

## Project Layout

```
spanish-app/
├── PLAN.md                 # Full project plan + architecture
├── AGENTS.md               # This file
├── backend/
│   ├── pyproject.toml      # Python project config
│   ├── alembic.ini         # DB migrations config
│   ├── data/               # SQLite DB directory
│   ├── app/
│   │   ├── main.py         # FastAPI app, middleware, routers
│   │   ├── config.py       # pydantic-settings (.env)
│   │   ├── database.py     # Async engine + session
│   │   ├── models.py       # SQLAlchemy ORM models
│   │   ├── schemas.py      # Pydantic v2 schemas
│   │   ├── crud.py         # Database operations
│   │   ├── srs.py          # FSRS v5 algorithm
│   │   ├── curriculum.py   # Seed data (words, lessons, grammar)
│   │   └── routers/
│   │       ├── users.py
│   │       ├── lessons.py
│   │       ├── vocab.py
│   │       ├── placement.py
│   │       └── conversation.py
│   └── tests/
│       └── test_api.py
├── bot/
│   ├── telegram_bot.py     # Main bot handler
│   ├── states.py           # Conversation state machine
│   ├── keyboards.py        # Inline keyboards
│   └── config.py           # Bot token, backend URL
└── deploy/
    ├── spanish-backend.service
    └── spanish-bot.service
```

## Patterns (follow trading-app conventions)

- Async SQLAlchemy 2.0 with `async_sessionmaker`
- `Base.metadata.create_all` on startup for dev
- Alembic for production migrations
- Pydantic v2 schemas with `from_attributes=True`
- API key middleware (optional, pattern from trading-backend)
- `Depends(get_db)` for session injection
- Config via `pydantic-settings.BaseSettings` reading `.env`
- Bind to Tailscale IP `100.103.32.107` only

## FSRS Implementation

Free Spaced Repetition Scheduler v5.
Default weights from py-fsrs benchmark.
States: 0=New, 1=Learning, 2=Review, 3=Relearning.
Ratings: 1=Again, 2=Hard, 3=Good, 4=Easy.

## env vars

| Variable | Purpose | Default |
|----------|---------|---------|
| `SPANISH_DATABASE_URL` | SQLite path | `sqlite+aiosqlite:///./data/spanish.db` |
| `SPANISH_API_KEY` | API key (optional) | `""` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required |
| `OPENROUTER_API_KEY` | LLM API key | Required |
| `HERMES_SSH_HOST` | Hermes SSH host | `192.168.0.144` |
| `HERMES_SSH_USER` | Hermes SSH user | `hermes` |

## Deployment (LXC 106)

- **Host:** `spanish-app` LXC 106 (192.168.0.130, Tailscale 100.91.254.59)
- **Code path:** `/opt/spanish-app/` (deployed via scp from VM 101 `~/spanish-app/`)
- **Systemd units (system):** `spanish-backend.service`, `spanish-bot.service`
- **Backend URL in bot:** `http://100.91.254.59:8100` (Tailscale)
- **Restart:** `ssh root@192.168.0.130 systemctl restart spanish-bot`

## Known Issues

- **Phase 3 (Hermes live-Grammatik + Konversation):** `/gramatica` und `/hablar` sind Platzhalter
- **4 Unit-Bilder fehlen:** 28/32 Units illustriert

## Session-Log: 2026-06-10

### Picture Mode, Audio, Lesson Scaffold & Review — 5 Bugfixes
- **Picture Mode Bug**: Bild passte nicht zum abgefragten Wort. Jetzt: wort-spezifische Bilder aus `static/words/word_{id}.jpg`, Fallback auf Unit-Bild
- **Lesson Scaffold**: `_build_lesson_plan()` erstellt vor Lektionsstart Gerüst: lädt Wörter, identifiziert Picture-Mode-Wörter, prüft ob Bilder existieren
- **Image Pre-Generation**: Fehlende Bilder werden vor der Lektion per ComfyUI/RunPod generiert (DreamShaper8 LCM), mit Fortschrittsanzeige im Chat
- **Audio Bug**: Kein Auto-Send mehr. Inline-Button `🔊 Audio` statt automatischem Audio-Send. Telegram playlistet einzelne Audios nicht
- **Review Filter**: `/review` lädt nur due+failed Wörter, nie neue. Gefiltert nach User-Level (A0/A1 für Beginner). `_load_review_words()` implementiert
- **Stock Images**: `image_gen.py` generiert Wortbilder via RunPod Serverless (DreamShaper8, 768×768), Two-Pass Upscale → 9.4 MP Stock-PNG → Nextcloud `Home Lab/Spanish App/Wortbilder/`
- **Backend**: Neuer `GET /api/vocab/failed` Endpoint (crud.py + vocab.py) für häufig falsch beantwortete Wörter
- **Deployed**: LXC 106, beide Services laufen sauber
