import streamlit as st
import os
import html as _html
from logic.chatbot import (
    load_knowledge_base,
    initialize_chatbot,
    inject_chatbot_popup,
    query_gemini,
)
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

# ── Chatbot Session State ──────────────────────────────────────
if "chatbot_query_id" not in st.session_state:
    st.session_state.chatbot_query_id = 0
if "chatbot_response" not in st.session_state:
    st.session_state.chatbot_response = ""
if "cb_input" not in st.session_state:
    st.session_state.cb_input = ""

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
    st.warning("⚠️ Chatbot no disponible: API key no configurada. El resto de la web funciona con normalidad.")
    # No se detiene la app — el chatbot es un feature secundario

# --- SEO META DESCRIPTION ---
seo_data = texts.get("seo", {})
meta_desc = seo_data.get("meta_description", "")
keywords = ", ".join(seo_data.get("keywords", []))
if meta_desc:
    st.markdown(
        f'<meta name="description" content="{meta_desc}">'
        f'<meta name="keywords" content="{keywords}">',
        unsafe_allow_html=True,
    )

# --- SIDEBAR ---
with st.sidebar:
    # ── Selector de idioma (arriba del todo) ──────────────────────
    st.subheader("Idioma / Language")

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
    st.write(profile_data.get('location', ''))

    socials = profile_data.get("socials", {})
    social_links_html = ""
    for icon, link in socials.items():
        href = f"mailto:{link}" if icon == "email" else link
        target = "" if icon == "email" else 'target="_blank"'
        social_links_html += f'<a href="{href}" {target} class="social-link">{icon.capitalize()}</a>'
    st.markdown(f'<div class="social-links-container">{social_links_html}</div>', unsafe_allow_html=True)

    # ── Badge de disponibilidad (estilo sutil) ─────────────────────
    availability_text = profile_data.get("availability", "")
    if availability_text:
        st.markdown(
            f'<div style="margin-top:10px;">'
            f'<span style="background:#1F7033;color:#9DCCA9;padding:3px 9px;border-radius:4px;font-size:0.75em;letter-spacing:0.02em;">'
            f'&#9679; {availability_text}'
            f'</span></div>',
            unsafe_allow_html=True,
        )

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
                label=cv['label'],
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
    # Ordenar por periodo descendente (full-time primero, luego freelance/capstone)
    exp_items = sorted(
        exp_data.get("items", []),
        key=lambda x: x.get("period", "").split(" - ")[-1],
        reverse=True,
    )
    for item in exp_items:
        with st.expander(f"**{item.get('role')}** at **{item.get('company')}** | {item.get('period')}", expanded=True):
            st.markdown(f"_{item.get('location')}_ — _{item.get('type')}_")
            st.markdown(item.get("description", ""))
            st.markdown(f"**Stack:** `{'`, `'.join(item.get('stack', []))}`")
            achievements = item.get("achievements", [])
            if achievements:
                st.markdown("**Logros principales:**")
                for achievement in achievements:
                    st.markdown(f"- {achievement}")

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
                    st.markdown(f"[Ver en GitHub]({item.get('link')})")
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
                    st.markdown(f"[Ver publicación (DOI: {item.get('doi')})](https://doi.org/{item.get('doi')})")
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
                    # delta_color="off" elimina la flecha verde/roja que no tiene sentido semántico
                    st.metric(
                        label=item.get('language'),
                        value=item.get('level'),
                        delta=item.get('proficiency', None),
                        delta_color="off",
                    )

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
        st.markdown(
            f'<div style="margin:12px 0;">'
            f'<span style="background:#1F7033;color:#9DCCA9;padding:6px 14px;border-radius:6px;font-size:0.9em;display:inline-block;">'
            f'&#9679; {availability}'
            f'</span></div>',
            unsafe_allow_html=True,
        )

    socials = contact_data.get("contact_methods", {})
    if socials:
        copy_feedback_text = texts.get("email_copied_feedback", "¡Copiado!")
        email_tooltip = texts.get('copy_email_tooltip', 'Copiar email al portapapeles')

        # JS robusto con fallback execCommand para entornos sin HTTPS o sin Clipboard API
        js = f"""
        <script>
        function copyEmailRobust(text, feedbackId) {{
            function showFeedback() {{
                var feedback = document.getElementById(feedbackId);
                if (feedback) {{
                    feedback.innerText = '{copy_feedback_text}';
                    feedback.style.display = 'inline';
                    setTimeout(function() {{ feedback.style.display = 'none'; }}, 2500);
                }}
            }}
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(showFeedback, function() {{
                    fallbackCopy(text, showFeedback);
                }});
            }} else {{
                fallbackCopy(text, showFeedback);
            }}
        }}
        function fallbackCopy(text, callback) {{
            var textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            try {{ document.execCommand('copy'); if (callback) callback(); }}
            catch (e) {{ console.error('Copy failed:', e); }}
            document.body.removeChild(textarea);
        }}
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)

        links_html_parts = []
        for key, value in socials.items():
            if key == "email":
                html = (
                    f'<a href="mailto:{value}" '
                    f'onclick="copyEmailRobust(\'{value}\', \'copy-feedback-contact\'); return true;" '
                    f'class="social-link" title="{email_tooltip}">'
                    f'{key.capitalize()}</a>'
                )
                links_html_parts.append(html)
            else:
                html = f'<a href="{value}" target="_blank" class="social-link">{key.capitalize()}</a>'
                links_html_parts.append(html)

        feedback_html = '<span id="copy-feedback-contact" style="display:none; color:green; margin-left:10px; font-weight:bold;"></span>'
        links_html = " | ".join(links_html_parts)
        # Centrado y con separador superior
        st.markdown(
            f'<div style="text-align:center; margin-top:24px; padding-top:20px; border-top:1px solid #e0e0e0;">'
            f'{links_html}{feedback_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

st.divider()

# --- CHATBOT BACKEND BRIDGE & POPUP ---
if GENAI_API_KEY:
    # This section handles the logic for receiving a query from the frontend JS,
    # calling the Gemini backend, and storing the response for the JS to poll.
    def handle_chatbot_query():
        if st.session_state.cb_input:
            user_query = st.session_state.cb_input
            st.session_state.cb_input = ""

            kb_text = load_knowledge_base()
            response = query_gemini(user_query, kb_text, lang=st.session_state.lang)  # ← añadir lang

            st.session_state.chatbot_query_id += 1
            st.session_state.chatbot_response = response

    # Hidden input widget that the JS popup writes to. The on_change callback
    # triggers the Python logic to run.
    st.text_input(
        "__cb_input__",
        key="cb_input",
        on_change=handle_chatbot_query,
        label_visibility="collapsed",
    )

    # Hidden div that holds the response from Python. JS polls this element
    # for changes to its 'data-id' attribute to know when a new response is ready.
    # We use html.escape to prevent potential XSS issues from the LLM response.
    st.markdown(
        f'<div id="cb-py-response" data-id="{st.session_state.chatbot_query_id}">'
        f'{_html.escape(st.session_state.chatbot_response)}</div>',
        unsafe_allow_html=True,
    )

    # Cargar la base de conocimiento y la configuración del bot
    knowledge_base_text = load_knowledge_base()
    bot_config = texts.get("chatbot_config", {})

    # Inyectar el HTML/JS del popup del chatbot
    inject_chatbot_popup(
        bot_config=bot_config,
        kb_text=knowledge_base_text,
        api_key=GENAI_API_KEY,
    )
