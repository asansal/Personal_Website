import streamlit as st

from logic.chatbot import load_knowledge_base, inject_chatbot_popup, initialize_chatbot
from logic.utils import load_css


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Portfolio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# --- STYLES ---
load_css("assets/css/style.css")


# --- CHATBOT INITIALIZATION ---
GENAI_API_KEY = initialize_chatbot()
if not GENAI_API_KEY:
    st.stop()


# --- PAGE CONTENT ---
st.title("My Portfolio")
st.write("Welcome! Feel free to ask my AI assistant about my profile.")


# --- CHATBOT ---
knowledge_base_text = load_knowledge_base()
if knowledge_base_text:
    bot_config = {
        'title': 'AI Assistant',
        'welcome_message': 'Pregúntame sobre mi experiencia, habilidades y proyectos.'
    }
    inject_chatbot_popup(bot_config, knowledge_base_text, GENAI_API_KEY)
