import streamlit as st
import html as _html
import os
from logic.chatbot import load_knowledge_base, inject_chatbot_popup, initialize_chatbot, query_gemini
from logic.utils import (
    load_css,
    load_localization,
    load_config,
    get_img_as_base64,
    read_pdf_byte_stream,
)

# --- LANGUAGE SELECTION & LOCALIZATION ---
languages = load_config()
if "lang" not in st.session_state:
    st.session_state.lang = "es"  # Default language

texts = load_localization(st.session_state.lang)
if not texts:
    st.error(f"Could not load localization file for '{st.session_state.lang}'. Please ensure 'locales/{st.session_state.lang}.json' exists.")
    st.stop()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title=texts.get("seo", {}).get("meta_title", "Alejandro Sánchez | Portfolio"),
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",  # ← sidebar abierta por defecto
)

# --- STYLES ---
load_css("assets/css/style.css")

# --- CHATBOT INITIALIZATION ---
GENAI_API_KEY = initialize_chatbot()
if not GENAI_API_KEY:
    st.stop()

# ─────────────────────────────────────────────────────────────────
# CHAT BRIDGE: procesa mensajes pendientes del popup antes del render
# ─────────────────────────────────────────────────────────────────
knowledge_base_text = load_knowledge_base()

if st.session_state.get("__cb_pending__") and knowledge_base_text:
    pending_msg = st.session_state["__cb_pending__"]
    bot_response = query_gemini(pending_msg, knowledge_base_text)
    st.session_state["__cb_response__"] = bot_response
    st.session_state["__cb_resp_id__"] = st.session_state.get("__cb_resp_id__", 0) + 1
    # Limpiar el pending para no re-procesar en el próximo rerun
    st.session_state["__cb_pending__"] = ""

# --- SIDEBAR ---
with st.sidebar:
    # ── Selector de idioma (arriba del todo) ──────────────────────
    st.subheader("🌐 Idioma / Language")
    lang_cols = st.columns(len(languages))
    for i, (lang_code, lang_info) in enumerate(languages.items()):
        if lang_cols[i].button(
            f"{lang_info['flag']} {lang_info['name']}",
            key=f"lang_btn_{lang_code}",
            use_container_width=True,
        ):
            st.session_state.lang = lang_code
            st.rerun()

    st.divider()

    # ── Perfil ─────────────────────────────────────────────────────
    profile_data = texts.get("profile", {})
    img_b64 = get_img_as_base64("assets/images/profile.png")
    st.markdown(
        f'<div class="profile-pic-container"><img class="profile-pic" src="data:image/png;base64,{img_b64}"></div>',
        unsafe_allow_html=True,
    )
    st.title(profile_data.get("name", ""))
    st.write(profile_data.get("role", ""))
    st.write(f"📍 {profile_data.get('location', '')}")

    socials = profile_data.get("socials", {})
    social_links_html = "".join(
        [f'<a href="{link}" target="_blank" class="social-link">{icon.capitalize()}</a>' for icon, link in socials.items()]
    )
    st.markdown(f'<div class="social-links-container">{social_links_html}</div>', unsafe_allow_html=True)

    st.divider()

    # ── Descarga de CVs según idioma ───────────────────────────────
    st.subheader(texts.get("chatbot_config", {}).get("cv_download_text", "Download CV"))

    cvs = {
        "en": [
            {"label": "CV Data Scientist (EN)", "path": "assets/files/CV_Data_Science_EN_2026_Alejandro_Sanchez.pdf"},
            {"label": "CV Data Analyst (EN)",   "path": "assets/files/CV_Data_Analyst_EN_2026_Alejandro_Sanchez.pdf"},
        ],
        "es": [
            # Si tienes CVs en español, añádelos aquí.
            # Mientras tanto usamos los ingleses como fallback.
            {"label": "CV Data Scientist (EN)", "path": "assets/files/CV_Data_Science_EN_2026_Alejandro_Sanchez.pdf"},
            {"label": "CV Data Analyst (EN)",   "path": "assets/files/CV_Data_Analyst_EN_2026_Alejandro_Sanchez.pdf"},
        ],
        "de": [
            {"label": "CV Data Scientist (DE)", "path": "assets/files/CV_DE_Data_Science_2026_Alejandro_Sanchez.pdf"},
        ],
    }

    # Usa el idioma seleccionado; si no hay entrada, cae a inglés
    cv_lang = st.session_state.lang if st.session_state.lang in cvs else "en"
    for cv in cvs.get(cv_lang, []):
        pdf_bytes = read_pdf_byte_stream(cv["path"])
        if pdf_bytes:
            st.download_button(
                label=f"📄 {cv['label']}",
                data=pdf_bytes,
                file_name=os.path.basename(cv["path"]),
                mime="application/octet-stream",
                use_container_width=True,
            )

# --- MAIN CONTENT ---
st.title(texts.get("profile", {}).get("tagline", ""))
st.subheader(texts.get("profile", {}).get("subtitle", ""))
st.divider()

# About section
about_data = texts.get("about", {})
with st.container():
    st.header(about_data.get("title", "About Me"))
    st.write(about_data.get("text_long", ""))

# Experience section
exp_data = texts.get("experience_section", {})
with st.container():
    st.header(exp_data.get("title", "Experience"))
    for item in exp_data.get("items", []):
        with st.expander(f"**{item.get('role')}** at **{item.get('company')}** | {item.get('period')}", expanded=True):
            st.markdown(f"_{item.get('location')}_ - _{item.get('type')}_")
            st.markdown(item.get("description", ""))
            st.markdown(f"**Stack:** `{'`, `'.join(item.get('stack', []))}`")

# Projects section
projects_data = texts.get("projects_section", {})
with st.container():
    st.header(projects_data.get("title", "Projects"))
    for item in projects_data.get("items", []):
        st.subheader(item.get("title"))
        st.markdown(f"**{item.get('type')}** - {item.get('year')}")
        st.write(item.get("description"))
        st.markdown(f"**Tech:** `{'`, `'.join(item.get('tech', []))}`")
        if item.get("link"):
            st.markdown(f"[View Project]({item.get('link')})")
        st.divider()

# ─────────────────────────────────────────────────────────────────
# CHAT BRIDGE: input oculto que el popup JS escribe para hacer rerun
# ─────────────────────────────────────────────────────────────────
# El popup JS detecta este input por su aria-label y lo escribe
# antes de simular Enter → Streamlit hace rerun → Python llama a Gemini
# → la respuesta aparece en el div oculto → JS la lee y la muestra.
cb_input_val = st.text_input(
    "__cb_input__",
    key="__cb_pending__",
    label_visibility="collapsed",
)

# Div oculto con la última respuesta del bot (el JS lo lee con polling)
resp_id   = st.session_state.get("__cb_resp_id__", 0)
resp_text = _html.escape(st.session_state.get("__cb_response__", ""))
st.markdown(
    f'<div id="cb-py-response" data-id="{resp_id}" style="display:none">{resp_text}</div>',
    unsafe_allow_html=True,
)

# --- CHATBOT POPUP INJECTION ---
if knowledge_base_text:
    bot_config = texts.get("chatbot_config", {})
    inject_chatbot_popup(bot_config, knowledge_base_text, GENAI_API_KEY)