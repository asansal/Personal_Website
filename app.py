import streamlit as st
import streamlit.components.v1 as components
import os
import html as _html

# --- PAGE CONFIGURATION ---
# ¡IMPORTANTE! set_page_config DEBE ser el primer comando de Streamlit.
st.set_page_config(
    page_title="Alejandro Sánchez | Portfolio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


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

# ── SPA Router State ───────────────────────────────────────────
HOME_VIEW = "home"
if "current_view" not in st.session_state:
    st.session_state.current_view = HOME_VIEW

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

# --- STYLES ---
load_css("assets/css/style.css")

# --- CHATBOT INITIALIZATION ---
GENAI_API_KEY = initialize_chatbot()
if not GENAI_API_KEY:
    st.warning("⚠️ Chatbot no disponible: API key no configurada. El resto de la web funciona con normalidad.")
    # App is not stopped — the chatbot is a secondary feature

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
    # ── Language Selector ──────────────────────────────────────────
    st.subheader("Idioma / Language")

    # Create list of options for the selectbox
    lang_options = {f"{info['flag']} {info['name']}": code for code, info in languages.items()}
    # Get the name of the current option
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

    # ── Profile ────────────────────────────────────────────────────
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
    st.markdown(f'<div class="social-links">{social_links_html}</div>', unsafe_allow_html=True)

    # ── Availability Badge ─────────────────────────────────────────
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

    # ── CV Download ────────────────────────────────────────────────
    # Map languages to their respective CV files
    cv_files = {
        "es": "assets/files/CV_ES_Alejandro_Sanchez.pdf",
        "en": "assets/files/CV_EN_Alejandro_Sanchez.pdf",
        "de": "assets/files/CV_DE_Alejandro_Sanchez.pdf",
    }

    # Use the selected language; if not available in the mapping, fallback to English
    cv_lang = st.session_state.lang if st.session_state.lang in cv_files else "en"
    cv_path = cv_files[cv_lang]

    pdf_bytes = read_pdf_byte_stream(cv_path)
    if pdf_bytes:
        st.download_button(
            label=texts.get("cv_download_text", "Download CV"),
            data=pdf_bytes,
            file_name=os.path.basename(cv_path),
            mime="application/octet-stream",
            width='stretch',
        )


# --- NAVIGATION HELPERS ---
nav_data = texts.get("navigation", {})


def go_to(view: str) -> None:
    """on_click callback: changes the active view before the rerun, so a single click is enough."""
    st.session_state.current_view = view


def render_back_button(position: str) -> None:
    """Renders the '🔙 Volver al Inicio' button. `position` keeps widget keys unique (top/bottom)."""
    with st.container(key=f"back-nav-{position}"):
        st.button(
            nav_data.get("back_home", "🔙 Volver al Inicio"),
            key=f"back_home_{position}",
            on_click=go_to,
            args=(HOME_VIEW,),
        )


def scroll_to_top(view: str) -> None:
    """Streamlit keeps the scroll position between reruns; reset it when the view changes.
    The view name is embedded in the HTML so the iframe only re-executes on navigation."""
    components.html(
        f"""<script>
        // view: {view}
        const main = window.parent.document.querySelector('section.stMain, [data-testid="stMain"]');
        if (main) {{ main.scrollTo({{top: 0, behavior: 'instant'}}); }}
        window.parent.scrollTo({{top: 0, behavior: 'instant'}});
        </script>""",
        height=0,
    )


def tech_badges(items: list) -> str:
    return f"`{'`, `'.join(items)}`" if items else ""


# --- VIEWS ---

def render_home() -> None:
    profile = texts.get("profile", {})
    st.title(profile.get("tagline", ""))
    st.markdown(f'<p class="home-subtitle">{profile.get("subtitle", "")}</p>', unsafe_allow_html=True)
    st.caption(nav_data.get("home_hint", ""))

    cards = nav_data.get("cards", {})

    def card_label(view: str) -> str:
        card = cards.get(view, {})
        # Bold title + paragraph break → two <p> inside the button (styled in style.css)
        return f"{card.get('icon', '')} **{card.get('title', view)}**\n\n{card.get('subtitle', '')}"

    # Bento layout: each row is a list of (view, relative width)
    bento_rows = [
        [("story", 2), ("experience", 1)],
        [("projects", 1), ("skills", 1), ("education", 1)],
        [("achievements", 1), ("contact", 2)],
    ]

    with st.container(key="bento-grid"):
        for row in bento_rows:
            cols = st.columns([width for _, width in row], gap="medium")
            for col, (view, _) in zip(cols, row):
                with col:
                    st.button(
                        card_label(view),
                        key=f"bento_{view}",
                        on_click=go_to,
                        args=(view,),
                        width="stretch",
                    )


def render_story() -> None:
    about = texts.get("about", {})
    st.header(about.get("title", "My Story"))
    st.markdown(f'<p class="story-lead">{about.get("lead", "")}</p>', unsafe_allow_html=True)

    for chapter in about.get("chapters", []):
        with st.container(border=True):
            st.markdown(f"#### {chapter.get('icon', '')} {chapter.get('title', '')}")
            st.caption(chapter.get("period", ""))
            st.write(chapter.get("text", ""))

    if about.get("closing"):
        st.markdown(f'<p class="story-closing">{about.get("closing")}</p>', unsafe_allow_html=True)

    st.divider()

    value_prop = texts.get("value_proposition", {})
    st.header(value_prop.get("title", "Value Proposition"))
    points = value_prop.get("points", [])
    if points:
        num_cols = min(len(points), 4)
        cols = st.columns(num_cols)
        for i, point in enumerate(points):
            with cols[i % num_cols]:
                st.subheader(point.get("title", ""))
                st.write(point.get("description", ""))


def render_experience() -> None:
    exp_data = texts.get("experience_section", {})
    st.header(exp_data.get("title", "Experience"))
    st.write(exp_data.get("intro", ""))

    # ── Featured: Sextant IA (in production) ──────────────────────
    featured = exp_data.get("featured", {})
    if featured:
        with st.container(border=True, key="featured-experience"):
            st.markdown(f'<span class="featured-badge">{featured.get("badge", "")}</span>', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 2])
            with col1:
                st.subheader(featured.get("company", ""))
                st.markdown(f"**{featured.get('role')}** | {featured.get('period')}")
                st.markdown(f"_{featured.get('location')}_ — _{featured.get('type')}_")
                st.write(featured.get("story", ""))
                st.success(featured.get("production_note", ""))
                st.markdown(f"**{featured.get('impact_title', '')}**")
                for item in featured.get("impact", []):
                    st.markdown(f"- {item}")
                st.markdown(f"**Stack:** {tech_badges(featured.get('stack', []))}")
                if featured.get("link"):
                    st.link_button(featured.get("link_label", "Sextant IA"), featured["link"])
            with col2:
                if featured.get("image"):
                    st.image(featured["image"], width="stretch")

    # ── Career path ───────────────────────────────────────────────
    for item in exp_data.get("items", []):
        with st.expander(f"**{item.get('role')}** · **{item.get('company')}** | {item.get('period')}", expanded=True):
            st.markdown(f"_{item.get('location')}_ — _{item.get('type')}_")
            st.write(item.get("story", ""))
            for achievement in item.get("impact", []):
                st.markdown(f"- {achievement}")
            st.markdown(f"**Stack:** {tech_badges(item.get('stack', []))}")


def render_projects() -> None:
    projects_data = texts.get("projects_section", {})
    st.header(projects_data.get("title", "Projects"))
    st.write(projects_data.get("intro", ""))
    labels = projects_data.get("labels", {})

    project_items = projects_data.get("items", [])
    if project_items:
        tabs = st.tabs([item.get("title", f"Project {i+1}") for i, item in enumerate(project_items)])
        for tab, item in zip(tabs, project_items):
            with tab:
                st.markdown(f"##### {item.get('type')} - {item.get('year')}")
                for field in ("challenge", "approach", "result"):
                    if item.get(field):
                        st.markdown(f"**{labels.get(field, field.capitalize())}:** {item.get(field)}")
                st.markdown(f"**Tech:** {tech_badges(item.get('tech', []))}")
                if item.get("link"):
                    st.markdown(f"[{item.get('link_label', labels.get('link', 'GitHub'))}]({item.get('link')})")


def render_skills() -> None:
    skills_data = texts.get("skills_section", {})
    st.header(skills_data.get("title", "Technical Skills"))
    st.write(skills_data.get("intro", ""))
    categories = skills_data.get("categories", [])
    if categories:
        num_cols = min(len(categories), 2)
        cols = st.columns(num_cols)
        for i, category in enumerate(categories):
            with cols[i % num_cols]:
                with st.container(border=True):
                    st.subheader(category.get("name", ""))
                    st.caption(category.get("why", ""))
                    for item in category.get("items", []):
                        st.markdown(f"- {item}")


def render_education() -> None:
    education_data = texts.get("education_section", {})
    st.header(education_data.get("title", "Education"))
    st.write(education_data.get("intro", ""))
    for item in education_data.get("items", []):
        with st.expander(f"**{item.get('degree')}** - {item.get('institution')} ({item.get('year')})", expanded=False):
            st.markdown(f"_{item.get('location')}_ - _{item.get('type')}_")
            for highlight in item.get("highlights", []):
                st.markdown(f"- {highlight}")

    st.divider()

    pubs_data = texts.get("publications_section", {})
    st.header(pubs_data.get("title", "Publications"))
    st.write(pubs_data.get("intro", ""))
    for item in pubs_data.get("items", []):
        with st.expander(f"**{item.get('title')}**", expanded=False):
            st.markdown(f"_{item.get('authors')}_")
            st.markdown(f"**{item.get('journal')}** ({item.get('year')})")
            st.write(item.get("description", ""))
            if item.get("doi"):
                st.markdown(f"[{pubs_data.get('link_label', 'DOI')} (DOI: {item.get('doi')})](https://doi.org/{item.get('doi')})")


def render_achievements() -> None:
    st.header(texts.get("achievements_section", {}).get("title", "Achievements"))

    # Hackathons
    hackathons_data = texts.get("hackathons_section", {})
    st.subheader(hackathons_data.get("title", "Hackathons"))
    for item in hackathons_data.get("items", []):
        with st.expander(f"**{item.get('name')}** | {item.get('position')} — {item.get('date')}", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"_{item.get('organizer')}_")
                st.write(item.get("description", ""))
                st.markdown(f"**Stack:** {tech_badges(item.get('stack', []))}")
            with col2:
                if item.get("image"):
                    st.image(item.get("image"), width="stretch")

    st.divider()

    cert_data = texts.get("certifications_section", {})

    # Technical Certifications
    tech_cert_data = cert_data.get("certifications", {})
    if tech_cert_data:
        st.subheader(tech_cert_data.get("title", "Technical Certifications"))
        for item in tech_cert_data.get("items", []):
            st.markdown(f"- **{item.get('name')}** - _{item.get('issuer')}_ ({item.get('year')})")

    # Languages
    lang_data = cert_data.get("languages", {})
    if lang_data:
        st.subheader(lang_data.get("title", "Languages"))
        lang_items = lang_data.get("items", [])
        if lang_items:
            cols = st.columns(len(lang_items))
            for i, item in enumerate(lang_items):
                with cols[i]:
                    st.markdown(f"#### {item.get('language')}")
                    st.markdown(f"_{item.get('level')}_ **({item.get('proficiency')})**")


def render_contact() -> None:
    contact_data = texts.get("contact_section", {})
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

        # Robust JS with fallback execCommand for environments without HTTPS or Clipboard API
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
        # Centered and with top separator
        st.markdown(
            f'<div style="text-align:center; margin-top:24px; padding-top:20px; border-top:1px solid #e0e0e0;">'
            f'{links_html}{feedback_html}'
            f'</div>',
            unsafe_allow_html=True,
        )


VIEWS = {
    "story": render_story,
    "experience": render_experience,
    "projects": render_projects,
    "skills": render_skills,
    "education": render_education,
    "achievements": render_achievements,
    "contact": render_contact,
}

# --- MAIN CONTENT (SPA ROUTER) ---
# Unknown views (e.g. stale session state) fall back to Home.
if st.session_state.current_view not in VIEWS:
    st.session_state.current_view = HOME_VIEW

current_view = st.session_state.current_view
scroll_to_top(current_view)

if current_view == HOME_VIEW:
    render_home()
else:
    render_back_button("top")
    VIEWS[current_view]()
    st.divider()
    render_back_button("bottom")

# --- CHATBOT BACKEND BRIDGE & POPUP ---
if GENAI_API_KEY:
    # This section handles the logic for receiving a query from the frontend JS,
    # calling the Gemini backend, and storing the response for the JS to poll.
    def handle_chatbot_query():
        if st.session_state.cb_input:
            user_query = st.session_state.cb_input
            st.session_state.cb_input = ""

            kb_text = load_knowledge_base()

            # --- NUEVO: Inyectar contexto dinámico sobre el CV ---
            kb_text += (
                f"\n\n[INSTRUCCIÓN DINÁMICA DE LA INTERFAZ]: La página está actualmente "
                f"en el idioma '{st.session_state.lang}'. Si el usuario te solicita mi CV o currículum, "
                f"NO intentes generar enlaces. En su lugar, indícale amablemente que puede descargarlo "
                f"haciendo clic en el botón 'Descargar CV' que se encuentra en el menú lateral izquierdo de la pantalla. "
                f"Ese botón ya le proporcionará automáticamente el CV en el idioma correcto."
            )

            response = query_gemini(user_query, kb_text, lang=st.session_state.lang)

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

    # Load knowledge base and bot config
    knowledge_base_text = load_knowledge_base()
    bot_config = texts.get("chatbot_config", {})

    # Inject chatbot popup HTML/JS
    inject_chatbot_popup(
        bot_config=bot_config,
        kb_text=knowledge_base_text,
        api_key=GENAI_API_KEY,
    )
