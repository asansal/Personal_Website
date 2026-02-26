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

    # Crear lista de opciones para el selectbox
    lang_options = {f"{info['flag']} {info['name']}": code for code, info in languages.items()}
    # Obtener el nombre de la opción actual
    current_lang_name = next(
        (name for name, code in lang_options.items() if code == st.session_state.lang),
        list(lang_options.keys())[0]  # Fallback
    )

    selected_lang_name = st.selectbox(
        "Select a language",
        options=list(lang_options.keys()),
        index=list(lang_options.keys()).index(current_lang_name),
        label_visibility="collapsed",
    )

    selected_lang_code = lang_options[selected_lang_name]

    if selected_lang_code != st.session_state.lang:
        st.session_state.lang = selected_lang_code
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
    st.subheader(texts.get("cv_download_text", "Download CV"))

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

st.divider()

# Value Proposition section
value_prop_data = texts.get("value_proposition", {})
with st.container():
    st.header(value_prop_data.get("title", "Value Proposition"))
    points = value_prop_data.get("points", [])
    if points:
        num_cols = min(len(points), 4)
        cols = st.columns(num_cols)
        for i, point in enumerate(points):
            with cols[i % num_cols]:
                st.subheader(point.get('title', ''))
                st.write(point.get("description", ""))

st.divider()

# Skills section
skills_data = texts.get("skills_section", {})
with st.container():
    st.header(skills_data.get("title", "Technical Skills"))
    categories = skills_data.get("categories", [])
    if categories:
        num_cols = min(len(categories), 2)
        cols = st.columns(num_cols)
        for i, category in enumerate(categories):
            with cols[i % num_cols]:
                st.subheader(category.get('name', ''))
                for item in category.get("items", []):
                    st.markdown(f"- {item}")

st.divider()

# Experience section
exp_data = texts.get("experience_section", {})
with st.container():
    st.header(exp_data.get("title", "Experience"))
    for item in exp_data.get("items", []):
        with st.expander(f"**{item.get('role')}** at **{item.get('company')}** | {item.get('period')}", expanded=True):
            st.markdown(f"_{item.get('location')}_ - _{item.get('type')}_")
            st.markdown(item.get("description", ""))
            st.markdown(f"**Stack:** `{'`, `'.join(item.get('stack', []))}`")

st.divider()

# Education section
education_data = texts.get("education_section", {})
with st.container():
    st.header(education_data.get("title", "Education"))
    for item in education_data.get("items", []):
        with st.expander(f"**{item.get('degree')}** - {item.get('institution')} ({item.get('year')})", expanded=False):
            st.markdown(f"_{item.get('location')}_ - _{item.get('type')}_")
            if item.get("highlights"):
                for highlight in item.get("highlights", []):
                    st.markdown(f"- {highlight}")
st.divider()

# Projects section
projects_data = texts.get("projects_section", {})
with st.container():
    st.header(projects_data.get("title", "Projects"))
    project_items = projects_data.get("items", [])
    if project_items:
        project_titles = [item.get("title", f"Project {i+1}") for i, item in enumerate(project_items)]
        tabs = st.tabs(project_titles)

        for tab, item in zip(tabs, project_items):
            with tab:
                st.markdown(f"##### {item.get('type')} - {item.get('year')}")
                st.write(item.get("description"))
                st.markdown(f"**Tech:** `{'`, `'.join(item.get('tech', []))}`")
                if item.get("highlights"):
                    st.markdown("<h6>Highlights:</h6>", unsafe_allow_html=True)
                    for highlight in item.get("highlights", []):
                        st.markdown(f"- {highlight}")
                if item.get("link"):
                    st.markdown(f"🔗 [View on GitHub]({item.get('link')})")
st.divider()

# Publications section
pubs_data = texts.get("publications_section", {})
with st.container():
    st.header(pubs_data.get("title", "Publications"))
    for item in pubs_data.get("items", []):
        with st.expander(f"**{item.get('title')}**", expanded=False):
            st.markdown(f"_{item.get('authors')}_")
            st.markdown(f"**{item.get('journal')}** ({item.get('year')})")
            st.write(item.get("description", ""))
            if item.get("doi"):
                st.markdown(f"🔗 [View Publication (DOI: {item.get('doi')})](https://doi.org/{item.get('doi')})")
st.divider()

# Certifications section
cert_data = texts.get("certifications_section", {})
with st.container():
    st.header(cert_data.get("title", "Certifications"))

    # Languages
    lang_data = cert_data.get("languages", {})
    if lang_data:
        st.subheader(lang_data.get("title", "Languages"))
        lang_items = lang_data.get("items", [])
        if lang_items:
            cols = st.columns(len(lang_items))
            for i, item in enumerate(lang_items):
                with cols[i]:
                    st.metric(label=item.get('language'), value=item.get('level'), delta=item.get('proficiency', None))

    st.markdown("---") # Visual separator

    # Technical Certifications
    tech_cert_data = cert_data.get("certifications", {})
    if tech_cert_data:
        st.subheader(tech_cert_data.get("title", "Technical Certifications"))
        for item in tech_cert_data.get("items", []):
            st.markdown(f"- **{item.get('name')}** - _{item.get('issuer')}_ ({item.get('year')})")
st.divider()

# Contact Section
contact_data = texts.get("contact_section", {})
with st.container():
    st.header(contact_data.get("title", "Contact"))
    st.subheader(contact_data.get("cta"))
    st.write(contact_data.get("description"))

    availability = contact_data.get("availability", "")
    if availability:
        st.info(f"{availability}2026.")

    socials = contact_data.get("contact_methods", {})
    if socials:
        copy_feedback_text = texts.get("email_copied_feedback", "Copied!")
        js = f"""
        <script>
        function copyToClipboard(text, feedbackId) {{
            navigator.clipboard.writeText(text).then(function() {{
                var feedback = document.getElementById(feedbackId);
                if (feedback) {{
                    feedback.innerText = `{copy_feedback_text}`;
                    feedback.style.display = 'inline';
                    setTimeout(function(){{ feedback.style.display = 'none'; }}, 2000);
                }}
            }}, function(err) {{
                console.error('Could not copy text: ', err);
            }});
        }}
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)

        links_html_parts = []
        email_tooltip = texts.get('copy_email_tooltip', 'Copy email to clipboard')
        for key, value in socials.items():
            if key == "email":
                html = f'<a href="#" onclick="copyToClipboard(\'{value}\', \'copy-feedback-contact\'); return false;" class="social-link" title="{email_tooltip}">{key.capitalize()}</a>'
                links_html_parts.append(html)
            else:
                html = f'<a href="{value}" target="_blank" class="social-link">{key.capitalize()}</a>'
                links_html_parts.append(html)

        feedback_html = '<span id="copy-feedback-contact" style="display:none; color:green; margin-left:10px;"></span>'
        links_html = " | ".join(links_html_parts)
        st.markdown(f'<div class="social-links-container">{links_html}{feedback_html}</div>', unsafe_allow_html=True)

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
