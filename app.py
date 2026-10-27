import streamlit as st
import streamlit.components.v1 as components
import os
import re
import html as _html

# --- PAGE CONFIGURATION ---
# ¡IMPORTANTE! set_page_config DEBE ser el primer comando de Streamlit.
st.set_page_config(
    page_title="Alejandro Sánchez | Portfolio",
    page_icon="assets/images/profile_avatar.jpg",
    layout="wide",
    initial_sidebar_state="auto",  # expanded on desktop, collapsed on mobile
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
    st.warning("Chatbot no disponible: API key no configurada. El resto de la web funciona con normalidad.")
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

# --- SOCIAL ICONS (inline SVG brand logos) ---
SOCIAL_ICONS = {
    "linkedin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 2.062 0 0 1 0 4.125zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    "github": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>',
    "email": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>',
}
SOCIAL_NAMES = {"linkedin": "LinkedIn", "github": "GitHub", "email": "Email"}

# --- SIDEBAR ---
with st.sidebar:
    # ── Language Selector ──────────────────────────────────────────
    # Create list of options for the selectbox
    lang_options = {info["name"]: code for code, info in languages.items()}
    # Get the name of the current option
    current_lang_name = next(
        (name for name, code in lang_options.items() if code == st.session_state.lang),
        list(lang_options.keys())[0]  # Fallback
    )

    selected_lang_name = st.selectbox(
        "Idioma / Language",
        options=list(lang_options.keys()),
        index=list(lang_options.keys()).index(current_lang_name),
        label_visibility="collapsed",
    )

    selected_lang_code = lang_options[selected_lang_name]

    if selected_lang_code != st.session_state.lang:
        st.session_state.lang = selected_lang_code
        st.rerun()

    # ── Profile card: photo, name, socials and availability in one block ──
    # (a single HTML block keeps the spacing under control so the sidebar fits one screen)
    profile_data = texts.get("profile", {})
    img_b64 = get_img_as_base64("assets/images/profile_avatar.jpg")

    # Icon-only brand logos (the accessible name lives in aria-label/title)
    socials = profile_data.get("socials", {})
    social_links_html = ""
    for icon, link in socials.items():
        href = f"mailto:{link}" if icon == "email" else link
        target = "" if icon == "email" else 'target="_blank" rel="noopener"'
        name = SOCIAL_NAMES.get(icon, icon.capitalize())
        social_links_html += (
            f'<a href="{href}" {target} class="social-icon" title="{name}" aria-label="{name}">'
            f'{SOCIAL_ICONS.get(icon, name)}</a>'
        )

    availability_text = profile_data.get("availability", "")
    availability_html = (
        f'<div class="availability-badge"><span class="availability-dot"></span>{availability_text}</div>'
        if availability_text else ""
    )

    st.markdown(
        f'<div class="profile-card">'
        f'<img class="profile-pic" src="data:image/jpeg;base64,{img_b64}" alt="{profile_data.get("name", "")}">'
        f'<div>'
        f'<p class="profile-name">{profile_data.get("name", "")}</p>'
        f'<p class="profile-role">{profile_data.get("role", "")}</p>'
        f'<p class="profile-location">{profile_data.get("location", "")}</p>'
        f'</div>'
        f'<div class="social-icons">{social_links_html}</div>'
        f'{availability_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

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
    """Renders the 'Volver al Inicio' button. `position` keeps widget keys unique (top/bottom)."""
    with st.container(key=f"back-nav-{position}"):
        st.button(
            nav_data.get("back_home", "Volver al Inicio"),
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


def render_link_card(view: str, title: str, hint: str, key: str) -> None:
    """Horizontal card-style button that jumps to another section.
    Styled in style.css via [class*="st-key-link-card"]; the icon depends on `key`."""
    if view not in VIEWS:
        return
    with st.container(key=f"link-card-{key}"):
        st.button(
            f"{title}\n\n{hint}",
            key=f"go_{key}",
            width="stretch",
            on_click=go_to,
            args=(view,),
        )


def tech_badges(items: list) -> str:
    return f"`{'`, `'.join(items)}`" if items else ""


def section_intro(text: str) -> None:
    if text:
        st.markdown(f'<p class="section-intro">{text}</p>', unsafe_allow_html=True)


def tableau_parts(url: str) -> tuple[str, str] | None:
    """(workbook, sheet) from a Tableau Public link (…/viz/<Workbook>/<Sheet>)."""
    match = re.search(r"/(?:viz|views)/([^/?#]+)/([^/?#]+)", url)
    return match.groups() if match else None


def tableau_embed_url(url: str) -> str:
    """Embeddable /views/ URL for a Tableau Public viz link."""
    parts = tableau_parts(url)
    return f"https://public.tableau.com/views/{parts[0]}/{parts[1]}?:showVizHome=no&:embed=true" if parts else ""


def tableau_thumbnail_url(url: str) -> str:
    """Public thumbnail image for a Tableau Public viz link."""
    parts = tableau_parts(url)
    return f"https://public.tableau.com/thumb/views/{parts[0]}/{parts[1]}" if parts else ""


tableau_data = texts.get("tableau_section", {})
# The Tableau card/view only appears once there is something to show
HAS_TABLEAU = bool(tableau_data.get("profile_url") or tableau_data.get("items"))


# --- VIEWS ---

def render_home() -> None:
    profile = texts.get("profile", {})
    with st.container(key="home-hero"):
        st.title(profile.get("tagline", ""))
        st.markdown(f'<p class="home-subtitle">{profile.get("subtitle", "")}</p>', unsafe_allow_html=True)

    cards = nav_data.get("cards", {})

    def card_label(view: str) -> str:
        card = cards.get(view, {})
        # Plain-text label; the icon is drawn by style.css (.st-key-bento_<view>), so it
        # doesn't depend on Streamlit's markdown icon support
        return card.get("title", view)

    # Bento layout: a regular 3-column grid, every card the same size
    views = [view for view in ("experience", "projects", "tableau", "skills", "education", "contact") if view in VIEWS]
    bento_rows = [views[i:i + 3] for i in range(0, len(views), 3)]

    with st.container(key="bento-grid"):
        for row in bento_rows:
            cols = st.columns(3, gap="medium")
            for col, view in zip(cols, row):
                with col:
                    st.button(
                        card_label(view),
                        key=f"bento_{view}",
                        on_click=go_to,
                        args=(view,),
                        width="stretch",
                    )


def render_job(item: dict, key: str) -> None:
    """One job on the timeline: dates on the left, collapsed details on the right.
    `key` selects the job's accent colour in style.css (.st-key-job-<n>)."""
    with st.container(key=key):
        dates_col, detail_col = st.columns([1, 4], gap="small")
        with dates_col:
            st.markdown(
                f'<div class="tl-item"><span class="tl-dot"></span>'
                f'<span class="tl-period">{_html.escape(item.get("period", ""))}</span>'
                f'<span class="tl-type">{_html.escape(item.get("type", ""))}</span></div>',
                unsafe_allow_html=True,
            )
        with detail_col:
            with st.expander(f"**{item.get('role')}** · {item.get('company')}"):
                st.caption(item.get("location", ""))
                st.write(item.get("story", ""))
                for achievement in item.get("impact", []):
                    st.markdown(f"- {achievement}")
                st.markdown(f"**Stack:** {tech_badges(item.get('stack', []))}")


def render_experience() -> None:
    exp_data = texts.get("experience_section", {})
    st.header(exp_data.get("title", "Experience"))
    section_intro(exp_data.get("summary", ""))

    # ── Key figures ──
    stats = exp_data.get("stats", [])
    if stats:
        tiles = "".join(
            f'<div class="stat-tile"><span class="stat-value">{_html.escape(s.get("value", ""))}</span>'
            f'<span class="stat-label">{_html.escape(s.get("label", ""))}</span></div>'
            for s in stats
        )
        st.markdown(f'<div class="stat-strip">{tiles}</div>', unsafe_allow_html=True)

    # ── 1. Experience timeline ──
    with st.container(key="exp-timeline"):
        for n, item in enumerate(exp_data.get("items", [])):
            render_job(item, key=f"job-{n}")
        other_items = exp_data.get("other_items", [])
        if other_items:
            st.markdown(f"#### {exp_data.get('other_title', 'Other experience')}")
            for item in other_items:
                render_job(item, key="job-other")

    st.divider()

    # ── 2. What I bring: two columns (Data & AI / Life Sciences), points fold out ──
    value_prop = texts.get("value_proposition", {})
    st.header(value_prop.get("title", "What I bring"))
    columns = value_prop.get("columns", [])
    if columns:
        column_icons = {"data": "query_stats", "life": "biotech"}
        for col, column in zip(st.columns(len(columns), gap="large"), columns):
            with col, st.container(key=f"vp-{column.get('id')}"):
                st.markdown(
                    f'<div class="vp-header"><span class="ms-icon">{column_icons.get(column.get("id"), "star")}</span>'
                    f'{column.get("title", "")}</div>',
                    unsafe_allow_html=True,
                )
                for point in column.get("points", []):
                    with st.expander(point.get("title", "")):
                        st.write(point.get("description", ""))
    render_link_card("skills", value_prop.get("stack_link", "Tech stack"), value_prop.get("stack_link_hint", ""), key="stack")

    st.divider()

    # ── 3. Scientific publications ──
    pubs_data = texts.get("publications_section", {})
    st.header(pubs_data.get("title", "Publications"))
    section_intro(pubs_data.get("intro", ""))
    pub_labels = pubs_data.get("labels", {})
    for item in pubs_data.get("items", []):
        with st.expander(f"**{item.get('title')}**", expanded=False):
            st.caption(f"{item.get('authors')} · {item.get('journal')} ({item.get('year')})")
            if item.get("description"):
                st.markdown(f'<span class="featured-badge">{_html.escape(item["description"])}</span>', unsafe_allow_html=True)

            if item.get("image"):
                text_col, image_col = st.columns([3, 2], gap="large")
            else:
                text_col, image_col = st.container(), None

            with text_col:
                if item.get("summary"):
                    st.markdown(f"**{pub_labels.get('summary', 'Summary')}**")
                    st.write(item["summary"])
                if item.get("highlights"):
                    st.markdown(f"**{pub_labels.get('highlights', 'Key results')}**")
                    for highlight in item["highlights"]:
                        st.markdown(f"- {highlight}")
                if item.get("doi"):
                    st.link_button(
                        f"{pubs_data.get('link_label', 'DOI')} · DOI {item['doi']}",
                        f"https://doi.org/{item['doi']}",
                        type="primary",
                    )

            if image_col is not None:
                with image_col:
                    st.image(item["image"], caption=item.get("image_caption"), width="stretch")


def render_project(item: dict, labels: dict) -> None:
    """One project as a collapsed expander: title visible, the full case study inside."""
    is_featured = item.get("featured", False)
    with st.expander(f"**{item.get('title', '')}**"):
        if is_featured and item.get("badge"):
            st.markdown(f'<span class="featured-badge">{item.get("badge")}</span>', unsafe_allow_html=True)

        if item.get("image"):
            text_col, image_col = st.columns([3, 2], gap="large")
        else:
            text_col, image_col = st.container(), None

        with text_col:
            st.caption(f"{item.get('type')} · {item.get('year')}")
            if item.get("story"):
                st.write(item.get("story"))
            for field in ("challenge", "approach", "result"):
                if item.get(field):
                    st.markdown(f"**{labels.get(field, field.capitalize())}:** {item.get(field)}")
            if item.get("production_note"):
                st.success(item.get("production_note"))
            for highlight in item.get("impact", []):
                st.markdown(f"- {highlight}")
            st.markdown(f"**Tech:** {tech_badges(item.get('tech', []))}")
            if item.get("link"):
                link_label = item.get("link_label", labels.get("link", "GitHub"))
                if is_featured:
                    st.link_button(link_label, item["link"], type="primary")
                else:
                    st.markdown(f"[{link_label}]({item.get('link')})")

        if image_col is not None:
            with image_col:
                st.image(item["image"], width="stretch")


def select_project_category(category_id: str) -> None:
    st.session_state.project_category = category_id


def render_projects() -> None:
    projects_data = texts.get("projects_section", {})
    st.header(projects_data.get("title", "Projects"))
    section_intro(projects_data.get("intro", ""))
    labels = projects_data.get("labels", {})
    items = projects_data.get("items", [])
    categories = [c for c in projects_data.get("categories", []) if any(i.get("category") == c["id"] for i in items)]
    if not categories:
        for item in items:
            render_project(item, labels)
        return

    # First category (biomedical) is open by default so the page is never empty
    if st.session_state.get("project_category") not in {c["id"] for c in categories}:
        st.session_state.project_category = categories[0]["id"]
    selected = st.session_state.project_category

    # ── Category tiles: one per category, colour-coded in style.css (.st-key-projcat-<id>) ──
    singular, plural = projects_data.get("projects_word", ["project", "projects"])
    st.caption(projects_data.get("category_hint", ""))
    with st.container(key="project-categories"):
        for col, category in zip(st.columns(len(categories), gap="medium"), categories):
            count = sum(1 for i in items if i.get("category") == category["id"])
            with col, st.container(key=f"projcat-{category['id']}"):
                st.button(
                    f"{category.get('title', '')}\n\n{count} {singular if count == 1 else plural}",
                    key=f"projcat_btn_{category['id']}",
                    type="primary" if category["id"] == selected else "secondary",
                    on_click=select_project_category,
                    args=(category["id"],),
                    width="stretch",
                )

    # ── Projects of the selected category, collapsed ──
    for item in items:
        if item.get("category") == selected:
            render_project(item, labels)


def render_tableau() -> None:
    st.header(tableau_data.get("title", "Tableau Portfolio"))
    section_intro(tableau_data.get("intro", ""))
    if tableau_data.get("profile_url"):
        st.link_button(tableau_data.get("profile_label", "Tableau Public"), tableau_data["profile_url"], type="primary")

    dashboards = [d for d in tableau_data.get("items", []) if tableau_parts(d.get("url", ""))]
    if not dashboards:
        return

    # ── Gallery: thumbnails grouped by domain (health & science first) ──
    groups = tableau_data.get("groups", {})
    for group_key, group_title in groups.items():
        group_items = [d for d in dashboards if d.get("group") == group_key]
        if not group_items:
            continue
        st.subheader(group_title)
        for start in range(0, len(group_items), 3):
            cols = st.columns(3, gap="medium")
            for col, dashboard in zip(cols, group_items[start:start + 3]):
                with col, st.container(border=True, key=f"tableau-card-{dashboard['url'].rsplit('/', 2)[-2]}"):
                    st.image(tableau_thumbnail_url(dashboard["url"]), width="stretch")
                    st.markdown(f"**{dashboard.get('title', '')}**")
                    st.caption(dashboard.get("description", ""))
                    st.markdown(
                        f'<a class="tableau-link" href="{dashboard["url"]}" target="_blank" rel="noopener">'
                        f'{tableau_data.get("open_label", "Tableau Public")}</a>',
                        unsafe_allow_html=True,
                    )

    # ── Live viewer: one embedded viz at a time (each Tableau iframe is heavy) ──
    st.divider()
    st.subheader(tableau_data.get("live_title", "Explore live"))
    titles = [d.get("title", f"Dashboard {i+1}") for i, d in enumerate(dashboards)]
    selected = st.selectbox(tableau_data.get("select_label", "Dashboard"), titles)
    dashboard = dashboards[titles.index(selected)]
    components.iframe(tableau_embed_url(dashboard["url"]), height=dashboard.get("height", 800), scrolling=True)


STACK_GROUP_ICONS = {"analysis": "bar_chart", "datascience": "model_training", "llm": "smart_toy", "life": "genetics"}


def render_stack_group(group: dict) -> None:
    """One coloured block: header, then each category as a title + one chip per tool (+ optional note)."""
    cards = ""
    for category in group.get("categories", []):
        chips = "".join(f'<span class="stack-chip">{_html.escape(tool)}</span>' for tool in category.get("tools", []))
        note = f'<p class="stack-note">{_html.escape(category["note"])}</p>' if category.get("note") else ""
        cards += (
            f'<div class="stack-category"><p class="stack-card-title">{_html.escape(category.get("name", ""))}</p>'
            f'<div class="stack-chips">{chips}</div>{note}</div>'
        )
    with st.container(key=f"stack-group-{group['id']}"):
        st.markdown(
            f'<div class="stack-block">'
            f'<div class="vp-header"><span class="ms-icon">{STACK_GROUP_ICONS.get(group["id"], "star")}</span>{group.get("title", "")}</div>'
            f'{cards}</div>',
            unsafe_allow_html=True,
        )


def render_skills() -> None:
    skills_data = texts.get("skills_section", {})
    st.header(skills_data.get("title", "Tech Stack"))

    # The screen is split into a 2 x 2 grid: one block per group
    groups = skills_data.get("groups", [])
    for start in range(0, len(groups), 2):
        for col, group in zip(st.columns(2, gap="medium"), groups[start:start + 2]):
            with col:
                render_stack_group(group)

    render_link_card(
        "education",
        skills_data.get("education_link", "Education & certifications"),
        skills_data.get("education_link_hint", ""),
        key="education",
    )


CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def render_education() -> None:
    education_data = texts.get("education_section", {})
    cert_data = texts.get("certifications_section", {})
    st.header(education_data.get("title", "Education"))
    section_intro(education_data.get("intro", ""))

    # ── 1. Academic education ──
    st.subheader(education_data.get("degrees_title", "Education"))
    for item in education_data.get("items", []):
        with st.expander(f"**{item.get('degree')}** · {item.get('institution')} ({item.get('year')})"):
            st.caption(f"{item.get('location')} · {item.get('type')}")
            for highlight in item.get("highlights", []):
                st.markdown(f"- {highlight}")

    # ── 2. Certifications, split by domain (same colours as "What I bring") ──
    tech_cert_data = cert_data.get("certifications", {})
    if tech_cert_data:
        st.divider()
        st.subheader(tech_cert_data.get("title", "Certifications"))
        categories = tech_cert_data.get("categories", [])
        column_icons = {"data": "query_stats", "life": "biotech"}
        for col, category in zip(st.columns(len(categories) or 1, gap="large"), categories):
            with col, st.container(key=f"vp-{category['id']}"):
                cards = "".join(
                    f'<div class="cert-card"><p class="cert-name">{_html.escape(c.get("name", ""))}</p>'
                    f'<p class="cert-meta">{_html.escape(c.get("issuer", ""))} · {c.get("year", "")}</p></div>'
                    for c in tech_cert_data.get("items", []) if c.get("category") == category["id"]
                )
                st.markdown(
                    f'<div class="vp-header"><span class="ms-icon">{column_icons.get(category["id"], "verified")}</span>'
                    f'{category.get("title", "")}</div><div class="cert-list">{cards}</div>',
                    unsafe_allow_html=True,
                )
        value_prop = texts.get("value_proposition", {})
        render_link_card("skills", value_prop.get("stack_link", "Tech stack"), value_prop.get("stack_link_hint", ""), key="stack-edu")

    # ── 3. Languages: CEFR level as 6 dots (A1 = 1 … C2 = 6) ──
    lang_data = cert_data.get("languages", {})
    if lang_data.get("items"):
        st.divider()
        st.subheader(lang_data.get("title", "Languages"))
        cards = ""
        for item in lang_data["items"]:
            level = item.get("proficiency", "")
            filled = CEFR_LEVELS.index(level) + 1 if level in CEFR_LEVELS else 0
            dots = "".join(f'<span class="lang-dot{" on" if n < filled else ""}"></span>' for n in range(len(CEFR_LEVELS)))
            note = f'<p class="lang-note">{_html.escape(item["certification"])}</p>' if item.get("certification") else ""
            cards += (
                f'<div class="lang-card" title="{level} ({filled}/6)">'
                f'<div class="lang-top"><span class="lang-name">{_html.escape(item.get("language", ""))}</span>'
                f'<span class="lang-level">{level}</span></div>'
                f'<div class="lang-dots">{dots}</div>'
                f'<p class="lang-desc">{_html.escape(item.get("level", ""))}</p>{note}</div>'
            )
        st.markdown(f'<div class="lang-grid">{cards}</div>', unsafe_allow_html=True)


def render_contact() -> None:
    contact_data = texts.get("contact_section", {})
    st.header(contact_data.get("title", "Contact"))
    st.subheader(contact_data.get("cta"))
    st.write(contact_data.get("description"))

    availability = contact_data.get("availability", "")
    if availability:
        st.markdown(
            f'<div class="availability-badge availability-inline"><span class="availability-dot"></span>{availability}</div>',
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
                    f'{SOCIAL_ICONS["email"]}{SOCIAL_NAMES["email"]}</a>'
                )
                links_html_parts.append(html)
            else:
                html = (
                    f'<a href="{value}" target="_blank" rel="noopener" class="social-link">'
                    f'{SOCIAL_ICONS.get(key, "")}{SOCIAL_NAMES.get(key, key.capitalize())}</a>'
                )
                links_html_parts.append(html)

        feedback_html = '<span id="copy-feedback-contact" style="display:none; color:green; margin-left:10px; font-weight:bold;"></span>'
        links_html = "".join(links_html_parts)
        # Centered and with top separator
        st.markdown(
            f'<div class="social-links contact-links">'
            f'{links_html}{feedback_html}'
            f'</div>',
            unsafe_allow_html=True,
        )


VIEWS = {
    "experience": render_experience,
    "projects": render_projects,
    "tableau": render_tableau,
    "skills": render_skills,
    "education": render_education,
    "contact": render_contact,
}
if not HAS_TABLEAU:
    del VIEWS["tableau"]

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
