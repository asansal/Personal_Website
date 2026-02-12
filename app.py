import streamlit as st
import json
import pandas as pd
from pathlib import Path

# --- LOCAL MODULES ---
from logic import utils, chatbot

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Portfolio | Data Science & Bio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD STYLES ---
utils.load_css("assets/css/style.css")

# --- HELPER: LOAD LANGUAGES ---
def load_localization(lang_code):
    """Loads the JSON file for the selected language."""
    try:
        with open(f"locales/{lang_code}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Locale file not found: locales/{lang_code}.json")
        return {}

def load_config():
    """Loads the language configuration index."""
    try:
        with open("config/languages.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback if config is missing
        return {"es": {"name": "Español", "flag": "🇪🇸"}}

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    # 1. Profile Image
    st.image("assets/images/profile.png", width=180)
    
    # 2. Language Selector
    st.markdown("### 🌐 Language")
    languages_conf = load_config()
    lang_options = list(languages_conf.keys())
    
    # Use session state to remember selection if needed, but selectbox handles it well naturally
    selected_lang = st.selectbox(
        "Select Language",
        options=lang_options,
        format_func=lambda x: f"{languages_conf[x]['flag']} {languages_conf[x]['name']}",
        label_visibility="collapsed"
    )
    
    # Load the text content based on selection
    texts = load_localization(selected_lang)

    st.markdown("---")

    # 3. Dynamic Profile / CV Selector
    st.markdown("### 🎯 Perfil Objetivo")
    profile_type = st.radio(
        "Ver enfoque:",
        ("Data Scientist", "Bioinformático", "Investigador"),
        label_visibility="collapsed"
    )

    # 4. CV Download Logic
    # Map profile selection to file paths
    cv_files = {
        "Data Scientist": "assets/files/cv_data_scientist.pdf",
        "Bioinformático": "assets/files/cv_researcher.pdf", # Assuming filename
        "Investigador": "assets/files/cv_researcher.pdf"
    }
    
    current_cv_path = cv_files.get(profile_type)
    pdf_data = utils.read_pdf_byte_stream(current_cv_path)
    
    if pdf_data:
        st.download_button(
            label=f"📄 {texts.get('cv_button', 'Download CV')}",
            data=pdf_data,
            file_name=f"CV_TuNombre_{profile_type.replace(' ', '_')}.pdf",
            mime="application/pdf",
        )
    
    st.markdown("---")
    st.write("📧 contacto@email.com")
    st.write("🔗 [LinkedIn](https://www.linkedin.com/in/tu-perfil)")
    st.write("🐙 [GitHub](https://github.com/tu-usuario)")

# --- MAIN CONTENT ---

# 1. Hero Section
st.title(f"Hola, soy Tu Nombre 👋")
st.markdown(f"### {texts.get('role', 'Data Scientist')}")
st.write(texts.get('about_text', ''))

# 2. Skills Section
st.markdown("---")
st.header(texts.get('skills_title', 'Technical Stack'))

col1, col2, col3 = st.columns(3)

# Helper to safely get lists from JSON
skills = texts.get('skills', {})

with col1:
    st.markdown(f"#### 📊 Data Science")
    for s in skills.get('ds', []): st.write(f"- {s}")

with col2:
    st.markdown(f"#### 🧬 Bioinfo")
    for s in skills.get('bio', []): st.write(f"- {s}")

with col3:
    st.markdown(f"#### 🛠 Tools")
    for s in skills.get('tools', []): st.write(f"- {s}")

# 3. Experience Timeline
st.markdown("---")
st.header(texts.get('experience_title', 'Experience'))

experience_list = texts.get('experience', [])
for job in experience_list:
    # Using the CSS card class defined in style.css
    st.markdown(
        f"""
        <div class="card">
            <span style="font-weight: bold; color: #4CAF50;">{job['period']}</span><br>
            <span style="font-size: 1.1em; font-weight: bold;">{job['role']}</span><br>
            <span style="font-style: italic; color: #555;">{job['place']}</span>
        </div>
        """, 
        unsafe_allow_html=True
    )

# 4. Featured Projects (Interactive)
st.markdown("---")
st.header(texts.get('projects_title', 'Projects'))
tab_labels = texts.get('tabs', ["Project A", "Project B"])
tab1, tab2 = st.tabs(tab_labels)

with tab1:
    st.subheader("🧬 Genomic Analysis Pipeline")
    st.write("Exploración de datos de expresión génica. (Aquí podrías poner un gráfico de Plotly)")
    # Example placeholder for interactivity
    if st.checkbox("Show code snippet"):
        st.code("import biopython\n# Analysis logic here...", language="python")

with tab2:
    st.subheader("🤖 Churn Prediction Model")
    st.write("Modelo predictivo utilizando Random Forest.")

# --- AI ASSISTANT SECTION ---
st.markdown("---")
st.subheader(texts.get('chatbot_title', 'AI Assistant'))
st.write(texts.get('chatbot_desc', 'Ask me anything about my profile.'))

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load knowledge base (Cached)
# Checks secrets logic inside chatbot.py or falls back to local CSV
kb_text = chatbot.load_knowledge_base()

# Display chat input
user_query = st.chat_input("Escribe tu pregunta aquí...")

if user_query:
    # 1. Display user message
    with st.chat_message("user"):
        st.write(user_query)
    
    # 2. Get AI Response
    with st.chat_message("assistant"):
        with st.spinner("Consulting knowledge base..."):
            response = chatbot.query_gemini(user_query, kb_text)
            st.write(response)