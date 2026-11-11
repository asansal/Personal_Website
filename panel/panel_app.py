"""Command center for asansal.com: visits, CV downloads, languages, sections, links and chatbot.

Runs as its own Streamlit app on 127.0.0.1:8502 and is published at panel.asansal.com
through Cloudflare Tunnel, behind Cloudflare Access (only the owner's email gets in).
It only reads the SQLite database that the public site writes (logic/analytics.py).

Local use:  PANEL_LOCAL=1 streamlit run panel/panel_app.py --server.port 8502
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("ANALYTICS_DB", BASE_DIR / "data" / "analytics.db"))

st.set_page_config(page_title="Centro de mando · asansal.com", page_icon="📊", layout="wide")

# --- Access control ------------------------------------------------------------
# Cloudflare Access adds this header after the login. The app also listens only on
# 127.0.0.1, so the header cannot be forged from outside the server.
allowed = ""
try:
    allowed = str(st.secrets.get("PANEL_ALLOWED_EMAIL", "") or "")
except Exception:
    pass
user = st.context.headers.get("Cf-Access-Authenticated-User-Email", "") or ""
if not os.getenv("PANEL_LOCAL"):
    if not user or (allowed and user.lower() != allowed.lower()):
        st.error("Acceso restringido.")
        st.stop()

# --- Look -----------------------------------------------------------------------
ACCENT = "#00d4aa"
MUTED = "#9aa4bf"
st.markdown(
    """<style>
    .block-container { padding-top: 2rem; max-width: 1300px; }
    [data-testid="stMetricValue"] { font-size: 1.9rem; }
    h3 { margin-top: .6rem; }
    </style>""",
    unsafe_allow_html=True,
)

LANG_NAMES = {"es": "Español", "en": "English", "de": "Deutsch", "sv": "Svenska", "nl": "Nederlands", "da": "Dansk"}
VIEW_NAMES = {"home": "Inicio", "experience": "Experiencia", "projects": "Proyectos", "tableau": "Tableau",
              "skills": "Tech stack", "education": "Formación", "contact": "Contacto",
              "privacy": "Privacidad"}
CATEGORY_NAMES = {"ai": "IA y LLMs", "data": "Data", "bio": "Bioinformática"}
TOPIC_NAMES = {"experience": "Experiencia", "projects": "Proyectos", "ai_llm": "IA y LLMs", "skills": "Habilidades",
               "education": "Formación", "languages": "Idiomas", "availability": "Disponibilidad / reubicación",
               "cv_contact": "CV y contacto", "personal": "Personal", "other": "Otros"}
DEVICE_NAMES = {"desktop": "Ordenador", "mobile": "Móvil", "tablet": "Tablet"}


def link_label(target: str) -> str:
    """Readable name for an external link (stored as host + path)."""
    if target == "mailto":
        return "Email"
    host, _, path = target.partition("/")
    host = host.removeprefix("www.")
    parts = [p for p in path.split("/") if p]
    if host == "sextantia.eu":
        return "Sextant IA"
    if host == "lab.asansal.com":
        return "Job Matcher" if parts[:1] == ["job-matcher"] else "lab.asansal.com"
    if host.endswith("linkedin.com"):
        return "LinkedIn"
    if host == "github.com":
        return "GitHub · " + parts[1] if len(parts) > 1 else "GitHub (perfil)"
    if host == "doi.org":
        return "Publicación · DOI " + "/".join(parts)
    if host == "public.tableau.com":
        return "Tableau · " + (parts[2] if len(parts) > 2 and parts[0] in ("views", "app") else "perfil")
    return target


def source_label(value: str) -> str:
    if value.startswith("utm:"):
        return "Campaña · " + value[4:]
    host = value.removeprefix("www.").removeprefix("m.").removeprefix("l.").removeprefix("lm.")
    for key, name in (("linkedin", "LinkedIn"), ("google", "Google"), ("bing", "Bing"), ("duckduckgo", "DuckDuckGo"),
                      ("github", "GitHub"), ("t.co", "X / Twitter"), ("facebook", "Facebook"),
                      ("asansal.com", "lab.asansal.com"), ("sextantia", "Sextant IA")):
        if key in host:
            return name
    return host


# --- Data -----------------------------------------------------------------------
@st.cache_data(ttl=60)
def load(start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame()
    with closing(sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)) as conn:
        events = pd.read_sql("SELECT * FROM events WHERE day BETWEEN ? AND ?", conn, params=(start, end))
        questions = pd.read_sql("SELECT * FROM chat_questions WHERE day BETWEEN ? AND ?", conn, params=(start, end))
    return events, questions


PERIODS = {"Hoy": 0, "7 días": 6, "30 días": 29, "90 días": 89, "1 año": 364}

head_l, head_r = st.columns([3, 2], vertical_alignment="bottom")
with head_l:
    st.title("Centro de mando")
    st.caption("asansal.com · sin cookies; visitantes únicos por día (como Plausible). Datos en UTC.")
with head_r:
    period = st.segmented_control("Periodo", list(PERIODS), default="30 días", label_visibility="collapsed") or "30 días"

today = date.today()
start = today - timedelta(days=PERIODS[period])
prev_end = start - timedelta(days=1)
prev_start = prev_end - timedelta(days=PERIODS[period])

events, questions = load(start.isoformat(), today.isoformat())
prev_events, prev_questions = load(prev_start.isoformat(), prev_end.isoformat())

if events.empty and questions.empty:
    st.info("Todavía no hay datos en este periodo. Aparecerán en cuanto alguien visite la web.")
    st.stop()

humans = events[events["name"] != "bot"]
prev_humans = prev_events[prev_events["name"] != "bot"] if not prev_events.empty else prev_events


def of(df: pd.DataFrame, name: str) -> pd.DataFrame:
    return df[df["name"] == name] if not df.empty else df


def unique_visitors(df: pd.DataFrame) -> int:
    """Sum of daily unique visitors (the visitor id changes every day by design)."""
    return 0 if df.empty else int(df.drop_duplicates(["day", "visitor"]).shape[0])


def delta(now: int, before: int) -> str | None:
    if before == 0:
        return None
    return f"{(now - before) / before:+.0%}"


# --- KPIs -------------------------------------------------------------------------
kpis = [
    ("Visitantes únicos", unique_visitors(of(humans, "visit")), unique_visitors(of(prev_humans, "visit"))),
    ("Visitas", len(of(humans, "visit")), len(of(prev_humans, "visit"))),
    ("Descargas del CV", len(of(humans, "cv_download")), len(of(prev_humans, "cv_download"))),
    ("Preguntas al chatbot", len(questions), len(prev_questions)),
    ("Clics a otras webs", len(of(humans, "link_click")), len(of(prev_humans, "link_click"))),
]
for col, (label, now, before) in zip(st.columns(len(kpis)), kpis):
    col.metric(label, f"{now:,}".replace(",", "."), delta(now, before) if period != "Hoy" else None,
               help="Comparado con el periodo anterior de la misma duración")


# --- Chart helpers ----------------------------------------------------------------
def ranked_bars(counts: pd.Series, label: str, value: str = "Visitantes", height_per_row: int = 30) -> None:
    """Horizontal bars, largest first, one hue (a single series needs no legend)."""
    if counts.empty:
        st.caption("Sin datos en este periodo.")
        return
    df = counts.rename_axis(label).reset_index(name=value).sort_values(value, ascending=False)
    top = float(df[value].max()) or 1.0
    base = alt.Chart(df).encode(
        y=alt.Y(f"{label}:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=260, labelColor="#e6e9f2", ticks=False, domain=False),
                scale=alt.Scale(paddingInner=0.35)),
        # headroom on the right so the value labels are never clipped
        x=alt.X(f"{value}:Q", title=None, axis=None, scale=alt.Scale(domain=[0, top * 1.18])),
        tooltip=[alt.Tooltip(f"{label}:N"), alt.Tooltip(f"{value}:Q")],
    )
    bars = base.mark_bar(color=ACCENT, cornerRadiusEnd=4)
    text = base.mark_text(align="left", dx=6, color="#e6e9f2").encode(text=f"{value}:Q")
    st.altair_chart((bars + text).properties(height=max(70, height_per_row * len(df) + 10)), width="stretch")


def per_day(df: pd.DataFrame, value: str, unique: bool = True) -> None:
    days = pd.date_range(start, today, freq="D").strftime("%Y-%m-%d")
    if df.empty:
        series = pd.Series(0, index=days)
    elif unique:
        series = df.drop_duplicates(["day", "visitor"]).groupby("day").size().reindex(days, fill_value=0)
    else:
        series = df.groupby("day").size().reindex(days, fill_value=0)
    data = series.rename_axis("Día").reset_index(name=value)
    data["Día"] = pd.to_datetime(data["Día"])
    chart = alt.Chart(data).mark_bar(color=ACCENT, cornerRadiusEnd=3, width=alt.RelativeBandSize(0.7)).encode(
        x=alt.X("yearmonthdate(Día):T", title=None, axis=alt.Axis(format="%d %b", labelColor=MUTED, grid=False)),
        y=alt.Y(f"{value}:Q", title=None, axis=alt.Axis(labelColor=MUTED, tickMinStep=1, gridOpacity=0.15)),
        tooltip=[alt.Tooltip("yearmonthdate(Día):T", title="Día", format="%a %d %b %Y"), alt.Tooltip(f"{value}:Q")],
    )
    st.altair_chart(chart.properties(height=220), width="stretch")


def visitors_by(df: pd.DataFrame, column: str, names: dict | None = None) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=int)
    counts = df.drop_duplicates(["day", "visitor", column]).groupby(column).size()
    return counts.rename(index=lambda k: (names or {}).get(k, k) or "—")


# --- Audience -----------------------------------------------------------------------
st.subheader("Visitantes por día")
per_day(of(humans, "visit"), "Visitantes")

visits = of(humans, "visit")
col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.markdown("**Idioma con el que entran**")
    ranked_bars(visitors_by(visits, "lang", LANG_NAMES), "Idioma")
    changes = of(humans, "lang_change")
    if not changes.empty:
        st.markdown("**Cambian el idioma a**")
        ranked_bars(visitors_by(changes, "value", LANG_NAMES), "Idioma")
with col2:
    st.markdown("**Países**")
    ranked_bars(visitors_by(visits, "country").head(12), "País")
with col3:
    st.markdown("**Dispositivo**")
    ranked_bars(visitors_by(visits, "device", DEVICE_NAMES), "Dispositivo")
    st.markdown("**De dónde llegan**")
    sources = of(humans, "source")
    direct = visits["visitor"].nunique() - sources["visitor"].nunique() if not visits.empty else 0
    src = visitors_by(sources.assign(value=sources["value"].map(source_label)), "value") if not sources.empty else pd.Series(dtype=int)
    if direct > 0:
        src = pd.concat([src, pd.Series({"Directo / desconocido": direct})])
    ranked_bars(src, "Fuente")

st.divider()

# --- Content ----------------------------------------------------------------------
col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.markdown("**Secciones visitadas**")
    ranked_bars(visitors_by(of(humans, "view")[lambda d: d["value"] != "home"], "value", VIEW_NAMES), "Sección")
    st.markdown("**Categorías de proyectos abiertas**")
    ranked_bars(visitors_by(of(humans, "project_category"), "value", CATEGORY_NAMES), "Categoría")
with col2:
    st.markdown("**Descargas del CV por idioma**")
    cv = of(humans, "cv_download")
    ranked_bars(cv["value"].map(LANG_NAMES).value_counts() if not cv.empty else pd.Series(dtype=int), "CV", "Descargas")
    st.markdown("**Desde qué sección se descarga**")
    ranked_bars(cv["view"].map(lambda v: VIEW_NAMES.get(v, v)).value_counts() if not cv.empty else pd.Series(dtype=int),
                "Sección", "Descargas")
with col3:
    st.markdown("**Clics a otras webs** (+1 por clic)")
    links = of(humans, "link_click")
    ranked_bars(links["value"].map(link_label).value_counts() if not links.empty else pd.Series(dtype=int),
                "Enlace", "Clics")

st.divider()

# --- Chatbot ----------------------------------------------------------------------
st.subheader("Chatbot")
typed = questions[questions["source"] == "typed"] if not questions.empty else questions
predefined = questions[questions["source"] == "predefined"] if not questions.empty else questions
gemini_calls = questions[questions["cached"] == 0] if not questions.empty else questions

c = st.columns(5)
c[0].metric("Preguntas escritas", len(typed))
c[1].metric("Sugerencias pulsadas", len(predefined), help="Las 3 preguntas sugeridas. Se responden desde la caché.")
c[2].metric("Sin respuesta en la base", int((typed["answered"] == 0).sum()) if not typed.empty else 0,
            help="Preguntas que la base de conocimiento no cubría: ideas para ampliarla")
c[3].metric("Llamadas a Gemini", len(gemini_calls))
tokens = int(gemini_calls[["input_tokens", "output_tokens"]].fillna(0).sum().sum()) if not gemini_calls.empty else 0
c[4].metric("Tokens", f"{tokens:,}".replace(",", "."))

col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown("**De qué preguntan** (preguntas escritas)")
    ranked_bars(typed["topic"].map(lambda t: TOPIC_NAMES.get(t, t)).value_counts() if not typed.empty else pd.Series(dtype=int),
                "Tema", "Preguntas")
with col2:
    st.markdown("**Sugerencias pulsadas**")
    ranked_bars(predefined["question"].value_counts() if not predefined.empty else pd.Series(dtype=int),
                "Sugerencia", "Clics", height_per_row=34)

if not typed.empty:
    st.markdown("**Preguntas escritas**")
    topics = ["Todos"] + [TOPIC_NAMES.get(t, t) for t in typed["topic"].value_counts().index]
    f1, f2 = st.columns([2, 1])
    chosen = f1.selectbox("Tema", topics, label_visibility="collapsed")
    only_missing = f2.toggle("Solo sin respuesta")
    table = typed.assign(Tema=typed["topic"].map(lambda t: TOPIC_NAMES.get(t, t)))
    if chosen != "Todos":
        table = table[table["Tema"] == chosen]
    if only_missing:
        table = table[table["answered"] == 0]
    table = table.sort_values("ts", ascending=False).assign(
        Fecha=lambda d: pd.to_datetime(d["ts"]).dt.strftime("%d/%m %H:%M"),
        Idioma=lambda d: d["lang"].map(LANG_NAMES),
        Respondida=lambda d: d["answered"].map({1: "Sí", 0: "No"}),
    )[["Fecha", "question", "Tema", "Respondida", "Idioma"]].rename(columns={"question": "Pregunta"})
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"Pregunta": st.column_config.TextColumn(width="large")})

st.divider()

# --- Protection -------------------------------------------------------------------
st.subheader("Protección")
bots = of(events, "bot")
c = st.columns(5)
c[0].metric("Bots descartados", len(bots), help="Visitas de rastreadores y vistas previas de enlaces; no cuentan como visitas")
c[1].metric("Límites alcanzados", len(of(humans, "chat_limit")), help="Visitantes que llegaron a 5 (o 10) preguntas")
c[2].metric("Verificaciones superadas", len(of(humans, "captcha_ok")))
c[3].metric("Verificaciones fallidas", len(of(humans, "captcha_fail")))
c[4].metric("Errores de Gemini", len(of(humans, "chat_error")) + len(of(humans, "chat_daily_cap")),
            help="Errores de la API y veces que se alcanzó el tope diario global")
if not bots.empty:
    with st.expander("Últimos bots detectados"):
        st.dataframe(bots.sort_values("ts", ascending=False)[["ts", "value"]].head(50)
                     .rename(columns={"ts": "Fecha", "value": "Navegador"}), hide_index=True, width="stretch")
