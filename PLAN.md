# Spanish Learning App — Projektplan

## Konzept

Professionelles Spanisch-Lernprogramm, nutzbar via Telegram-Chat mit **Hermes als KI-Lehrer**.
Hybrid-Ansatz: strukturierte Lektionen + freie Konversations-Praxis.
Adaptiver Einstieg per Einstufungstest. Spaced Repetition (FSRS) für Vokabeln.

## Architektur

```
Telegram User
    │
    ▼
Telegram Bot API
    │
    ▼
┌─────────────────────────────────────────────┐
│  ai-agents VM 101                            │
│                                               │
│  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Telegram Bot      │  │ Spanish Backend   │  │
│  │ (python-telegram-  │  │ (FastAPI :8100)   │  │
│  │  bot, systemd)    │  │ SQLite + FSRS     │  │
│  └──────┬───────────┘  └────────┬─────────┘  │
│         │                       │             │
│         │  ┌────────────────────┘             │
│         │  │                                  │
│         ▼  ▼                                  │
│  ┌──────────────┐                              │
│  │ LLM Router    │                              │
│  │ OpenRouter    │                              │
│  │ DeepSeek V4   │                              │
│  └──────────────┘                              │
└─────────────────────────────────────────────┘
         │
         │ (SSH: Konversations-Modus)
         ▼
┌─────────────────────────────────────────────┐
│  Hermes LXC 105                              │
│  ┌──────────────────────────────────────┐    │
│  │ Spanisch-Lehrer Skill                 │    │
│  │ - Konversationspartner                │    │
│  │ - Fehlerkorrektur                     │    │
│  │ - Grammatik-Erklärungen               │    │
│  └──────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## Technologie-Stack

| Schicht | Technologie | Begründung |
|---------|-------------|-----------|
| Backend | FastAPI (async) | Vorhanden auf VM 101, bewährt im Trading-App |
| ORM | SQLAlchemy 2.0 + aiosqlite | Gleicher Stack wie Trading-Backend |
| DB | SQLite | Einfach, keine separate DB, reicht für Single-User |
| SRS | FSRS v5 | Moderner Anki-Nachfolger, mathematisch fundiert |
| Bot | python-telegram-bot (async) | Beste async Telegram-Bibliothek |
| LLM | OpenRouter DeepSeek V4 Flash | Gleicher Provider wie Hermes |
| Deployment | systemd user unit | Gleiches Muster wie trading-backend |

## Phasen

### Phase 1: Backend + Curriculum (Kern)

- [ ] FastAPI-Service auf Port 8100
- [ ] SQLite-Datenmodell (users, words, user_words, lessons, user_lessons, grammar)
- [ ] FSRS-Algorithmus (scheduler + review)
- [ ] Curriculum-Seed-Daten (~500 Wörter, 30+ Lektionen, 20+ Grammatik-Punkte)
- [ ] API: User-Erstellung, Lektionen, Vokabel-Review, Fortschritt
- [ ] Einstufungstest-Logik (adaptiv, 10 Fragen)
- [ ] systemd-Unit `spanish-backend.service`

### Phase 2: Telegram Bot

- [ ] Bot mit python-telegram-bot
- [ ] State-Machine für Konversations-Flows (Einstufungstest, Lektion, Review)
- [ ] Inline-Keyboard für SRS-Bewertungen (Again/Hard/Good/Easy)
- [ ] Kommandos: /start, /leccion, /review, /gramatica, /hablar, /progreso, /help
- [ ] systemd-Unit `spanish-bot.service`

### Phase 3: Hermes-Integration

- [ ] Hermes-Skill für Spanisch-Lehrer-Rolle
- [ ] SSH-Bridge: Bot → Hermes für Konversations-Modus
- [ ] Kontext-Weitergabe (Level, bekannte Wörter, letzte Themen)
- [ ] Automatische Vokabel-Aufnahme aus Konversationen

## Datenmodell

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
| unit | TEXT | Thematische Einheit (z.B. "restaurant", "travel") |
| example_sentence | TEXT | Beispielsatz auf Spanisch |
| example_translation | TEXT | Beispielsatz auf Deutsch |

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

### lessons
| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | INTEGER PK | Lektions-ID |
| title | TEXT | Titel (z.B. "Im Restaurant bestellen") |
| level | TEXT | Schwierigkeitsgrad |
| unit | TEXT | Thematische Einheit |
| lesson_type | TEXT | vocab, grammar, dialogue, mixed |
| sort_order | INTEGER | Reihenfolge innerhalb Unit |
| content_json | TEXT | JSON: Übungen, Dialoge, Erklärungen |

### user_lessons
| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| user_id | INTEGER FK | User |
| lesson_id | INTEGER FK | Lektion |
| completed_at | TEXT | Abschlussdatum |
| score | INTEGER | Ergebnis (0-100) |
| time_spent | INTEGER | Bearbeitungszeit in Sekunden |

### grammar_points
| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | INTEGER PK | Grammatik-ID |
| title | TEXT | Titel (z.B. "Ser vs Estar") |
| level | TEXT | Schwierigkeitsgrad |
| explanation | TEXT | Erklärung auf Deutsch |
| examples_json | TEXT | JSON: Beispielsätze Spanisch+Deutsch |
| sort_order | INTEGER | Lernreihenfolge |

## API-Endpoints (Phase 1)

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| POST | /api/users/register | Telegram-User anlegen |
| GET | /api/users/{id}/progress | Fortschritt abrufen |
| POST | /api/placement/start | Einstufungstest starten |
| POST | /api/placement/answer | Frage beantworten → nächste Frage/Ergebnis |
| GET | /api/lessons/next | Nächste fällige Lektion |
| GET | /api/lessons/{id} | Lektions-Inhalt abrufen |
| POST | /api/lessons/{id}/complete | Lektion abschließen |
| GET | /api/vocab/due | Fällige SRS-Vokabeln |
| POST | /api/vocab/review | SRS-Bewertung abgeben |
| GET | /api/grammar/{level} | Grammatik-Punkte für Level |
| GET | /api/conversation/context | User-Kontext für Hermes |
| GET | /api/stats/{id} | Lernstatistik (XP, Streak, Wörter) |

## FSRS-Algorithmus

Implementierung des Free Spaced Repetition Scheduler v5:
- Input: User-Bewertung (1=Again, 2=Hard, 3=Good, 4=Easy)
- Parameter: w[0..12] (Default-Weights aus FSRS-Benchmark)
- Berechnet: Stabilität, Schwierigkeit, nächster Review-Termin
- Formel aus: https://github.com/open-spaced-repetition/py-fsrs

## Curriculum (Seed-Daten)

### Levels
- **A0** (Absoluter Anfänger): Alphabet, Zahlen, Farben, Basis-Phrasen
- **A1** (Anfänger): Familie, Einkaufen, Restaurant, Wetter, Uhrzeit
- **A2** (Grundlegende Kenntnisse): Reisen, Beruf, Wohnung, Gesundheit
- **B1** (Fortgeschritten): Nachrichten, Kultur, Meinungen, Vergangenheit
- **B2** (Selbstständig): Diskussionen, Fachthemen, Hypothesen

### Units (30+)
restaurant, shopping, travel, family, weather, home, work, health,
directions, numbers, time, food, clothing, transport, hotel,
emergency, hobbies, sports, nature, technology, culture, news,
emotions, education, banking, phone, appointments, celebrations

### Grammatik (20+ Punkte)
ser/estar, por/para, bestimmte Artikel, unbestimmte Artikel,
Adjektiv-Angleichung, regelmäßige Verben -ar/-er/-ir,
unregelmäßige Verben, hay/estar, gustar, reflexiv,
possessivpronomen, direkte/indirekte Pronomen,
pretérito perfecto/indefinido/imperfecto, futuro simple,
condicional, subjuntivo presente, imperativo, comparativo/superlativo

## Ressourcen VM 101

| Ressource | Status | Spanisch-App Bedarf | Bewertung |
|-----------|--------|---------------------|-----------|
| RAM | 5.2 GiB frei | ~80-120 MB | OK |
| CPU | Intel N97, meist Idle | ~2-5% | OK |
| Disk | 12G frei (89% voll) | ~300 MB | Engpass — Aufräumen nötig |
| Swap | 1.8 GiB frei | — | OK |

**Empfehlung:** VM 101 reicht aus. Kein separater LXC-Container nötig.
Vor Installation ~5 GB aufräumen (alte venvs, Docker-Images, Logs).

## Bot-Kommandos

| Kommando | Funktion |
|----------|----------|
| /start | Registrierung + Einstufungstest starten |
| /leccion | Nächste Lektion beginnen |
| /review | Fällige Vokabeln (SRS) wiederholen |
| /gramatica | Grammatik-Punkt erklärt bekommen |
| /hablar | Freie Konversation mit Hermes starten |
| /progreso | Lernstatistik anzeigen |
| /help | Alle Kommandos anzeigen |

## Konventionen

- Alle Services binden an `100.103.32.107` (Tailscale-IP)
- API-Key-Auth wie Trading-Backend (Middleware, optional)
- Config per `.env` + pydantic-settings
- Kein Docker — systemd user units
- SQLite-DB unter `backend/data/spanish.db`

## Offene Fragen (für Grill-Session)

1. Hermes-Telegram-Gateway zuerst bauen oder Phase 3 als Teil davon?
2. TTS für Aussprache-Übungen? (edge-tts läuft auf Hermes)
3. Mehrere User? (Single-User reicht erstmal)
4. Gamification-Elemente? (Achievements, Leaderboard)
5. Audio-Aufnahmen für Aussprache-Checks?
