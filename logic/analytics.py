"""Cookieless visit analytics, chatbot limits and chatbot answer cache (SQLite).

Golden rule: measuring must never break the site. Every public function catches its
own errors and only logs a warning.

Privacy: the visitor is identified by a hash of (daily random salt + IP + browser).
The salt is kept for two days and then deleted, so after that nobody (not even with
access to the server) can work out which IP was behind a visitor id. The IP itself
is never stored. A returning visitor counts as new on another day, as in Plausible.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
import streamlit as st

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("ANALYTICS_DB", BASE_DIR / "data" / "analytics.db"))

# --- Chatbot limits (per visitor IP and day) ---
TYPED_LIMIT = int(os.getenv("CHAT_TYPED_LIMIT", 5))         # free-text questions without verification
VERIFIED_LIMIT = int(os.getenv("CHAT_VERIFIED_LIMIT", 10))   # after passing the Turnstile "not a robot" check
GLOBAL_DAILY_CAP = int(os.getenv("CHAT_DAILY_CAP", 300))     # Gemini calls per day, whole site (cost guard)
MAX_QUESTION_CHARS = 500
EVENT_RETENTION_DAYS = 400

# Automated browsers and link previews (WhatsApp, LinkedIn…): not visits
BOT_UA = re.compile(
    r"bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|discord|slack|"
    r"linkedin|curl|wget|python-requests|python-urllib|httpx|aiohttp|go-http|okhttp|java/|"
    r"headless|lighthouse|monitor|uptime|pingdom|scan|phantom|selenium|puppeteer|playwright",
    re.I,
)
TABLET_UA = re.compile(r"iPad|Tablet|Android(?!.*Mobile)", re.I)
MOBILE_UA = re.compile(r"Mobi|iPhone|iPod|Android", re.I)

SCHEMA = """
CREATE TABLE IF NOT EXISTS salts (day TEXT PRIMARY KEY, salt TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY, ts TEXT NOT NULL, day TEXT NOT NULL, visitor TEXT NOT NULL,
    name TEXT NOT NULL, value TEXT DEFAULT '', lang TEXT DEFAULT '', country TEXT DEFAULT '',
    device TEXT DEFAULT '', view TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_events_day_name ON events (day, name);
CREATE TABLE IF NOT EXISTS chat_questions (
    id INTEGER PRIMARY KEY, ts TEXT NOT NULL, day TEXT NOT NULL, visitor TEXT NOT NULL,
    lang TEXT DEFAULT '', question TEXT NOT NULL, topic TEXT DEFAULT 'other',
    answered INTEGER DEFAULT 1, source TEXT DEFAULT 'typed', cached INTEGER DEFAULT 0,
    input_tokens INTEGER, output_tokens INTEGER
);
CREATE INDEX IF NOT EXISTS ix_chat_day ON chat_questions (day);
CREATE TABLE IF NOT EXISTS chat_cache (
    key TEXT PRIMARY KEY, lang TEXT, question TEXT, answer TEXT NOT NULL,
    topic TEXT DEFAULT 'other', created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_usage (
    day TEXT NOT NULL, ip_key TEXT NOT NULL, typed INTEGER DEFAULT 0, verified INTEGER DEFAULT 0,
    PRIMARY KEY (day, ip_key)
);
"""

_initialized = False


def _connect() -> sqlite3.Connection:
    global _initialized
    conn = sqlite3.connect(DB_PATH, timeout=5)
    if not _initialized:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        cutoff = (date.today() - timedelta(days=EVENT_RETENTION_DAYS)).isoformat()
        # Retention promised on the privacy page: events and questions ~13 months,
        # per-IP chatbot counters two days (like the salts)
        conn.execute("DELETE FROM events WHERE day < ?", (cutoff,))
        conn.execute("DELETE FROM chat_questions WHERE day < ?", (cutoff,))
        conn.execute("DELETE FROM chat_usage WHERE day < ?", ((date.today() - timedelta(days=2)).isoformat(),))
        conn.commit()
        _initialized = True
    return conn


def _now() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    return now.isoformat(timespec="seconds"), now.date().isoformat()


def _salt(conn: sqlite3.Connection, day: str) -> str:
    row = conn.execute("SELECT salt FROM salts WHERE day = ?", (day,)).fetchone()
    if row:
        return row[0]
    salt = secrets.token_hex(32)
    conn.execute("INSERT OR IGNORE INTO salts (day, salt) VALUES (?, ?)", (day, salt))
    old = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    # Once a day (when the new salt is created): apply the retention periods
    conn.execute("DELETE FROM salts WHERE day < ?", (old,))
    conn.execute("DELETE FROM chat_usage WHERE day < ?", (old,))
    cutoff = (date.fromisoformat(day) - timedelta(days=EVENT_RETENTION_DAYS)).isoformat()
    conn.execute("DELETE FROM events WHERE day < ?", (cutoff,))
    conn.execute("DELETE FROM chat_questions WHERE day < ?", (cutoff,))
    conn.commit()
    return conn.execute("SELECT salt FROM salts WHERE day = ?", (day,)).fetchone()[0]


def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


# --- Visitor context ---

def _header(name: str) -> str:
    try:
        value = st.context.headers.get(name, "")
        return value if isinstance(value, str) else ""
    except Exception:
        return ""


def client_ip() -> str:
    """Real visitor IP. Cloudflare sends it in CF-Connecting-IP (trustworthy only if the
    origin is reachable through Cloudflare alone: tunnel or firewall)."""
    ip = _header("Cf-Connecting-Ip") or _header("X-Forwarded-For").split(",")[0].strip()
    if not ip:
        try:
            ip = st.context.ip_address
            ip = ip if isinstance(ip, str) else ""
        except Exception:
            ip = ""
    return ip or "unknown"


def _device(ua: str) -> str:
    if TABLET_UA.search(ua):
        return "tablet"
    if MOBILE_UA.search(ua):
        return "mobile"
    return "desktop"


def _context() -> dict:
    """Visitor data computed once per session and kept in session_state."""
    ctx = st.session_state.get("_analytics")
    today = _now()[1]
    if ctx and ctx.get("day") == today:
        return ctx
    ua = _header("User-Agent")
    ip = client_ip()
    with closing(_connect()) as conn:
        salt = _salt(conn, today)
    ctx = {
        "day": today,
        "visitor": _hash(salt, ip, ua),
        "ip_key": _hash(salt, ip),
        "country": _header("Cf-Ipcountry")[:2].upper(),
        "device": _device(ua),
        "is_bot": not ua or bool(BOT_UA.search(ua)),
        "bot_ua": ua[:80],
    }
    st.session_state["_analytics"] = ctx
    return ctx


def track(name: str, value: str = "") -> None:
    """Record one event for the current visitor. Bots are not recorded."""
    try:
        ctx = _context()
        if ctx["is_bot"]:
            return
        ts, day = _now()
        with closing(_connect()) as conn:
            conn.execute(
                "INSERT INTO events (ts, day, visitor, name, value, lang, country, device, view) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, day, ctx["visitor"], name, str(value)[:300], st.session_state.get("lang", ""),
                 ctx["country"], ctx["device"], st.session_state.get("current_view", "")),
            )
            conn.commit()
    except Exception as exc:  # never break the page
        logger.warning("analytics: could not record %s: %s", name, exc)


def track_visit() -> None:
    """Once per session: a visit (plus the campaign source if the link carried utm_source)."""
    if st.session_state.get("_visit_tracked"):
        return
    st.session_state["_visit_tracked"] = True
    try:
        ctx = _context()
        if ctx["is_bot"]:
            ts, day = _now()
            with closing(_connect()) as conn:
                conn.execute(
                    "INSERT INTO events (ts, day, visitor, name, value) VALUES (?, ?, ?, 'bot', ?)",
                    (ts, day, ctx["visitor"], ctx["bot_ua"]),
                )
                conn.commit()
            return
        track("visit")
        utm = st.query_params.get("utm_source", "")
        if utm:
            track("source", f"utm:{utm}")
    except Exception as exc:
        logger.warning("analytics: could not record visit: %s", exc)


def handle_client_event(raw: str) -> None:
    """Events sent by the browser through the hidden bridge input: 'kind\\tvalue|counter'."""
    try:
        payload = raw.rsplit("|", 1)[0]
        kind, _, value = payload.partition("\t")
        if kind == "link" and value:
            track("link_click", value)
        elif kind == "ref" and value:
            track("source", value)
    except Exception as exc:
        logger.warning("analytics: bad client event %r: %s", raw[:80], exc)


# --- Chatbot: limits, cache and question log ---

def chat_status() -> dict:
    """Free-text questions used today by this IP and whether it passed the check."""
    try:
        ctx = _context()
        with closing(_connect()) as conn:
            row = conn.execute(
                "SELECT typed, verified FROM chat_usage WHERE day = ? AND ip_key = ?",
                (ctx["day"], ctx["ip_key"]),
            ).fetchone()
            calls = conn.execute(
                "SELECT COUNT(*) FROM chat_questions WHERE day = ? AND cached = 0", (ctx["day"],)
            ).fetchone()[0]
        typed, verified = row if row else (0, 0)
        return {"typed": typed, "verified": bool(verified), "global_calls": calls}
    except Exception as exc:
        logger.warning("analytics: chat_status failed: %s", exc)
        return {"typed": 0, "verified": False, "global_calls": 0}


def register_typed_question() -> None:
    try:
        ctx = _context()
        with closing(_connect()) as conn:
            conn.execute(
                "INSERT INTO chat_usage (day, ip_key, typed) VALUES (?, ?, 1) "
                "ON CONFLICT (day, ip_key) DO UPDATE SET typed = typed + 1",
                (ctx["day"], ctx["ip_key"]),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("analytics: register_typed_question failed: %s", exc)


def mark_verified() -> None:
    try:
        ctx = _context()
        with closing(_connect()) as conn:
            conn.execute(
                "INSERT INTO chat_usage (day, ip_key, verified) VALUES (?, ?, 1) "
                "ON CONFLICT (day, ip_key) DO UPDATE SET verified = 1",
                (ctx["day"], ctx["ip_key"]),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("analytics: mark_verified failed: %s", exc)


def log_question(question: str, topic: str, answered: bool, source: str, cached: bool,
                 input_tokens: int | None = None, output_tokens: int | None = None) -> None:
    try:
        ctx = _context()
        if ctx["is_bot"]:
            return
        ts, day = _now()
        with closing(_connect()) as conn:
            conn.execute(
                "INSERT INTO chat_questions (ts, day, visitor, lang, question, topic, answered, source, "
                "cached, input_tokens, output_tokens) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, day, ctx["visitor"], st.session_state.get("lang", ""), question[:MAX_QUESTION_CHARS],
                 topic, int(answered), source, int(cached), input_tokens, output_tokens),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("analytics: log_question failed: %s", exc)


def cache_key(lang: str, question: str, knowledge: str) -> str:
    """Changes whenever the question, the language or the knowledge base changes."""
    return hashlib.sha256(f"{lang}\n{question}\n{knowledge}".encode()).hexdigest()


def cached_answer(key: str) -> tuple[str, str] | None:
    try:
        with closing(_connect()) as conn:
            row = conn.execute("SELECT answer, topic FROM chat_cache WHERE key = ?", (key,)).fetchone()
        return (row[0], row[1]) if row else None
    except Exception as exc:
        logger.warning("analytics: cache read failed: %s", exc)
        return None


def store_answer(key: str, lang: str, question: str, answer: str, topic: str) -> None:
    try:
        with closing(_connect()) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO chat_cache (key, lang, question, answer, topic, created) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (key, lang, question, answer, topic, _now()[0]),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("analytics: cache write failed: %s", exc)


# --- Cloudflare Turnstile ("not a robot" check) ---

def _secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, ""))


def turnstile_site_key() -> str:
    return _secret("TURNSTILE_SITE_KEY")


def verify_turnstile(token: str) -> bool:
    secret = _secret("TURNSTILE_SECRET_KEY")
    if not secret or not token:
        return False
    try:
        resp = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": secret, "response": token, "remoteip": client_ip()},
            timeout=8,
        )
        return bool(resp.json().get("success"))
    except Exception as exc:
        logger.warning("turnstile: verification request failed: %s", exc)
        return False
