# Spanish Learning App — Projektplan (v2, gegrillt 2026-06-05)

## Konzept

Professionelles Spanisch-Lernprogramm, nutzbar via Telegram-Chat mit **Hermes als KI-Lehrer**.
Hybrid-Ansatz: strukturierte Lektionen + freie Konversations-Praxis.
Adaptiver Einstieg per Einstufungstest. Spaced Repetition (FSRS) für Vokabeln.

## Architektur (aktualisiert)

```
Telegram User
    │
    ▼
Telegram Bot API
    │
    ▼
┌──────────────────────────────────────────────┐
│  LXC 106 — spanish-app (2 GB RAM, 40 GB)     │
│  Tailscale: <neue IP> :8100                   │
│                                                │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Telegram Bot      │  │ Spanish Backend   │   │
│  │ (python-telegram-  │  │ (FastAPI :8100)   │   │
│  │  bot, systemd)    │  │ SQLite + FSRS v5  │   │
│  └──────┬───────────┘  └────────┬─────────┘   │
│         │                       │              │
└─────────┼───────────────────────┼──────────────┘
          │                       │
          │ HTTP (Hermes GW)      │ HTTP (Tailscale)
          ▼                       ▼
┌────────────────────┐  ┌──────────────────────────────────┐
│  Hermes LXC 105    │  │  Backend API (von Hermes genutzt) │
│  Spanisch-Lehrer   │  │  GET  /api/vocab/due             │
│  Skill (LLM-Kopf)  │  │  POST /api/vocab/review          │
│  · Konversation    │  │  POST /api/vocab/add (Konv.)     │
│  · Grammatik live  │  │  GET  /api/users/{id}/context    │
│  · Fehlerkorrektur │  │  GET  /api/grammar/{level}       │
└────────────────────┘  └──────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  VM 101 — ai-agents (Entwicklung + Deployment)            │
│  ~/spanish-app/ → rsync → LXC 106                        │
└──────────────────────────────────────────────────────────┘
```

## Entscheidungen (Grill-Session 2026-06-05)

| Thema | Entscheidung |
|-------|-------------|
| **Backend-Standort** | LXC 106 (nicht VM 101) |
| **Bot-Standort** | LXC 106 (zusammen mit Backend) |
| **LLM-Provider** | Hermes (LXC 105) macht alle LLM-Calls |
| **Backend-Rolle** | Reiner Datenspeicher + FSRS-Engine, kein LLM |
| **Content-Strategie** | Gemischt: Vokabeln/Lektionen statisch, Grammatik/Dialoge dynamisch von Hermes |
| **Hermes-Anbindung** | Hermes Gateway HTTP API (nicht SSH) |
| **FSRS-Eigentümer** | Backend (Source of Truth), Hermes ruft API |
| **Deployment** | rsync VM 101 → LXC 106 |
| **Bildgenerierung** | Dual-Use: DreamShaper LCM → App (komprimiert) + Stock (4x-UltraSharp, 9 MP+, Nextcloud) |
| **Stock-Konvention** | 9 MP Minimum (Adobe Stock: 4 MP) |
| **LXC 106** | 2 GB RAM, 40 GB Disk, Debian, Tailscale |
| **Single-User** | Ja (Dan), skalierbar später |
| **Audio (TTS)** | edge-tts auf Hermes, per Wort + Beispielsatz |

## Technologie-Stack

| Schicht | Technologie | Begründung |
|---------|-------------|-----------|
| Backend | FastAPI (async) | Bewährt im Trading-App |
| ORM | SQLAlchemy 2.0 + aiosqlite | Gleicher Stack wie Trading-Backend |
| DB | SQLite | Einfach, reicht für Single-User |
| SRS | FSRS v5 | Moderner Anki-Nachfolger |
| Bot | python-telegram-bot (async) | Beste async Telegram-Bibliothek |
| LLM | Hermes (OpenRouter DeepSeek V4 Flash) | Hermes hat LLM-Infra bereits |
| Deployment | systemd units | Kein Docker nötig |
| Bilder | RunPod Serverless + ComfyUI v2 | DreamShaper + 4x-UltraSharp |

## Phasen

### Phase 1: Backend + Curriculum (Kern) ✅

- [x] FastAPI-Service auf Port 8100
- [x] SQLite-Datenmodell (users, words, user_words, lessons, user_lessons, grammar)
- [x] FSRS-Algorithmus (scheduler + review)
- [x] Curriculum-Seed-Daten (122 Wörter → muss auf 500+ erweitert werden)
- [x] API: User-Erstellung, Lektionen, Vokabel-Review, Fortschritt
- [x] Einstufungstest-Logik (adaptiv, 10 Fragen)
- [ ] systemd-Unit `spanish-backend.service` (angepasst für LXC 106)

### Phase 2: Telegram Bot

- [ ] Bot mit python-telegram-bot
- [ ] State-Machine für Konversations-Flows (Einstufungstest, Lektion, Review)
- [ ] Inline-Keyboard für SRS-Bewertungen (Again/Hard/Good/Easy)
- [ ] Kommandos: /start, /leccion, /review, /gramatica, /hablar, /progreso, /help
- [ ] systemd-Unit `spanish-bot.service` (angepasst für LXC 106)

### Phase 3: Hermes-Integration

- [ ] Hermes-Skill für Spanisch-Lehrer-Rolle (Konversation + Grammatik live)
- [ ] HTTP-Bridge: Bot → Hermes Gateway API für Konversations-Modus
- [ ] Kontext-Weitergabe (Level, bekannte Wörter, letzte Themen)
- [ ] Automatische Vokabel-Aufnahme aus Konversationen (POST /api/vocab/add)
- [ ] Alten `spanish-adaptive` Skill + Cron entfernen

### Phase 4: Content-Erweiterung

- [ ] Curriculum 122 → 500+ Wörter mit image_prompt + example_sentences
- [ ] Unit-Stimmungsbilder per ComfyUI generieren
- [ ] Audio (edge-tts) für alle Vokabeln + Beispielsätze

## Lern-Flow (Täglicher Zyklus)

```
09:00  Telegram-Opener → "Buenos días! Zeit für Spanisch ☀️"
         │
         ▼ [Button: "Lektion starten"]
  ┌──────────────┐
  │ 1. WARMUP    │  5 fällige FSRS-Vokabeln (Inline: 🔴/🟠/🟢/🔵)
  │    ~2 Min    │  Again / Hard / Good / Easy
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ 2. LEKTION   │  Neue Unit (10 Wörter) mit Bildern
  │    ~5 Min    │  · Bild + spanisches Wort
  │              │  · Bild + deutsches Wort → spanisch tippen
  │              │  · Audio (TTS) → nachsprechen
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ 3. GRAMMATIK │  Hermes erklärt 1 Grammatik-Punkt (dynamisch)
  │    ~3 Min    │  + 2-3 Übungssätze (Lückentext)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ 4. KONVERS.  │  Hermes: freies Gespräch mit neuen Wörtern
  │    ~5 Min    │  Neue Vokabeln → automatisch in FSRS
  └──────────────┘
         │
         ▼  [Statistik: +12 Wörter, 85% korrekt, Streak 7🔥]
```

## Datenmodell (unverändert)

### users
| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | INTEGER PK | User-ID |
| telegram_id | INTEGER UNIQUE | Telegram User ID |
| username | TEXT | Telegram @username |
| current_level | TEXT | A0, A1, A2, B1, B2 |
| xp | INTEGER | Erfahrungspunkte |
| streak | INTEGER | Tage in Folge aktiv |
| last_active_date | TEXT | Letzte Aktivität (ISO-Datum) |
| total_words_learned | INTEGER | Gelernte Wörter gesamt |
| placement_complete | BOOL | Einstufungstest abgeschlossen? |
| created_at | TEXT | Registrierungsdatum |

### words
| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | INTEGER PK | Wort-ID |
| spanish | TEXT | Spanisches Wort/Phrase |
| german | TEXT | Deutsche Übersetzung |
| word_type | TEXT | noun, verb, adjective, phrase |
| level | TEXT | A0, A1, A2, B1, B2 |
| unit | TEXT | Thematische Einheit |
| gender | TEXT | m/f/n (für Nomen) |
| example_sentence | TEXT | Beispielsatz auf Spanisch |
| example_translation | TEXT | Beispielsatz auf Deutsch |
| image_prompt | TEXT | Prompt für Bild-Generierung |
| audio_url | TEXT | TTS-Audio URL (generiert) |

### user_words (FSRS-Parameter pro User+Wort)
| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| user_id | INTEGER FK | User |
| word_id | INTEGER FK | Wort |
| state | INTEGER | FSRS State (0=New, 1=Learning, 2=Review, 3=Relearning) |
| stability | REAL | FSRS Stabilität |
| difficulty | REAL | FSRS Schwierigkeit |
| elapsed_days | REAL | Tage seit letzter Review |
| scheduled_days | REAL | Geplantes Intervall |
| reps | INTEGER | Anzahl Wiederholungen |
| lapses | INTEGER | Anzahl Vergessens-Ereignisse |
| last_review | TEXT | Letzte Review (ISO-Datum) |
| next_review | TEXT | Nächste fällige Review |
| source | TEXT | "lesson" oder "conversation" |

### lessons, user_lessons, grammar_points — unverändert

## API-Endpoints

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| POST | /api/users/register | Telegram-User anlegen |
| GET | /api/users/{id}/progress | Fortschritt abrufen |
| GET | /api/users/{id}/context | User-Kontext für Hermes |
| POST | /api/placement/start | Einstufungstest starten |
| POST | /api/placement/answer | Frage beantworten |
| GET | /api/lessons/next | Nächste fällige Lektion |
| GET | /api/lessons/{id} | Lektions-Inhalt abrufen |
| POST | /api/lessons/{id}/complete | Lektion abschließen |
| GET | /api/vocab/due | Fällige SRS-Vokabeln |
| POST | /api/vocab/review | SRS-Bewertung abgeben |
| POST | /api/vocab/add | Neues Wort aus Konversation hinzufügen |
| GET | /api/grammar/{level} | Grammatik-Punkte für Level (Cache) |
| GET | /api/stats/{id} | Lernstatistik (XP, Streak, Wörter) |

## Bot-Kommandos

| Kommando | Funktion |
|----------|----------|
| /start | Registrierung + Einstufungstest starten |
| /leccion | Geführter Flow: Warmup → Lektion → Grammatik → Konversation |
| /review | Nur fällige Vokabeln (SRS) |
| /gramatica | Grammatik live von Hermes |
| /hablar | Freie Konversation mit Hermes |
| /progreso | Lernstatistik anzeigen |
| /help | Alle Kommandos |

## Konventionen

- Alle Services binden an Tailscale-IP des LXC 106
- API-Key-Auth wie Trading-Backend (optional)
- Config per `.env` + pydantic-settings
- systemd units auf LXC 106
- SQLite-DB unter `backend/data/spanish.db`
- Deployment: rsync von VM 101 zu LXC 106
- Bilder Dual-Use: App (lokal komprimiert) + Stock (Nextcloud /Hermes-HL/ai-pics-stockversion/)

## Curriculum

### Levels
- **A0** (Absoluter Anfänger): Alphabet, Zahlen, Farben, Basis-Phrasen
- **A1** (Anfänger): Familie, Einkaufen, Restaurant, Wetter, Uhrzeit
- **A2** (Grundlegende Kenntnisse): Reisen, Beruf, Wohnung, Gesundheit
- **B1** (Fortgeschritten): Nachrichten, Kultur, Meinungen, Vergangenheit
- **B2** (Selbstständig): Diskussionen, Fachthemen, Hypothesen

### Units (25+)
restaurant, shopping, travel, family, weather, home, work, health,
directions, numbers, time, food, clothing, transport, hotel,
emergency, hobbies, sports, nature, technology, culture, news,
emotions, education, banking

### Grammatik (dynamisch von Hermes)
20+ Punkte als Seed-Themen, Erklärungen live generiert.
