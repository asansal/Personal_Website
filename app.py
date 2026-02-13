import streamlit as st
import json
import streamlit.components.v1 as components
from logic import utils, chatbot

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Alejandro Sánchez | Portfolio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD STYLES ---
utils.load_css("assets/css/style.css")

# --- HELPER FUNCTIONS ---
def load_localization(lang_code):
    """Carga el archivo de localización según el idioma"""
    try:
        with open(f"locales/{lang_code}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Locale file not found: locales/{lang_code}.json")
        return {}

def load_config():
    """Carga la configuración de idiomas disponibles"""
    try:
        with open("config/languages.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"es": {"name": "Español", "flag": "🇪🇸"}}

def inject_chatbot_popup(bot_config, kb_text):
    """Inyecta el chatbot popup flotante con diseño profesional"""
    
    # JavaScript para comunicación bidireccional
    popup_html = f"""
    <style>
    /* CHATBOT POPUP STYLES */
    .chatbot-trigger {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 70px;
        height: 70px;
        background: linear-gradient(135deg, #4CAF50, #00d4aa);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 
            0 8px 30px rgba(76, 175, 80, 0.5),
            0 0 40px rgba(0, 212, 170, 0.3);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 10000;
        border: 3px solid rgba(255, 255, 255, 0.15);
        animation: pulse-ring 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    }}
    
    @keyframes pulse-ring {{
        0%, 100% {{
            box-shadow: 
                0 8px 30px rgba(76, 175, 80, 0.5),
                0 0 40px rgba(0, 212, 170, 0.3),
                0 0 0 0 rgba(76, 175, 80, 0.7);
        }}
        50% {{
            box-shadow: 
                0 8px 30px rgba(76, 175, 80, 0.5),
                0 0 40px rgba(0, 212, 170, 0.3),
                0 0 0 15px rgba(76, 175, 80, 0);
        }}
    }}
    
    .chatbot-trigger:hover {{
        transform: scale(1.15) rotate(10deg);
        box-shadow: 
            0 12px 40px rgba(76, 175, 80, 0.7),
            0 0 60px rgba(0, 212, 170, 0.5);
    }}
    
    .chatbot-trigger svg {{
        width: 35px;
        height: 35px;
        fill: white;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
    }}
    
    .chatbot-popup {{
        position: fixed;
        bottom: 120px;
        right: 30px;
        width: 420px;
        height: 600px;
        background: linear-gradient(180deg, 
            rgba(10, 14, 39, 0.98) 0%, 
            rgba(22, 33, 62, 0.96) 100%);
        border-radius: 24px;
        box-shadow: 
            0 25px 80px rgba(0, 0, 0, 0.6),
            0 0 60px rgba(76, 175, 80, 0.25),
            inset 0 1px 2px rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(30px) saturate(180%);
        border: 1px solid rgba(76, 175, 80, 0.3);
        display: none;
        flex-direction: column;
        overflow: hidden;
        z-index: 9999;
        animation: slideUpScale 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    
    .chatbot-popup.active {{
        display: flex;
    }}
    
    @keyframes slideUpScale {{
        from {{
            opacity: 0;
            transform: translateY(40px) scale(0.9);
        }}
        to {{
            opacity: 1;
            transform: translateY(0) scale(1);
        }}
    }}
    
    .chatbot-header {{
        background: linear-gradient(135deg, #4CAF50 0%, #00d4aa 100%);
        padding: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }}
    
    .chatbot-header-content {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .chatbot-avatar {{
        width: 45px;
        height: 45px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        border: 2px solid rgba(255, 255, 255, 0.3);
    }}
    
    .chatbot-header h3 {{
        color: white;
        margin: 0;
        font-size: 1.3rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        font-family: 'Playfair Display', serif;
    }}
    
    .chatbot-header .status {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.95);
        font-weight: 500;
    }}
    
    .status-dot {{
        width: 9px;
        height: 9px;
        background: #66FF66;
        border-radius: 50%;
        animation: pulse-dot 2s ease infinite;
        box-shadow: 0 0 12px #66FF66;
    }}
    
    @keyframes pulse-dot {{
        0%, 100% {{ transform: scale(1); opacity: 1; }}
        50% {{ transform: scale(1.2); opacity: 0.7; }}
    }}
    
    .close-btn {{
        background: rgba(255, 255, 255, 0.2);
        border: none;
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        font-size: 22px;
        font-weight: bold;
    }}
    
    .close-btn:hover {{
        background: rgba(255, 255, 255, 0.35);
        transform: rotate(90deg) scale(1.1);
    }}
    
    .chatbot-body {{
        flex: 1;
        overflow-y: auto;
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }}
    
    .chatbot-body::-webkit-scrollbar {{
        width: 8px;
    }}
    
    .chatbot-body::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }}
    
    .chatbot-body::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, #4CAF50, #00d4aa);
        border-radius: 4px;
    }}
    
    .chat-message {{
        display: flex;
        gap: 12px;
        animation: fadeIn 0.4s ease;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .chat-message.bot {{
        align-self: flex-start;
    }}
    
    .chat-message.user {{
        align-self: flex-end;
        flex-direction: row-reverse;
    }}
    
    .message-avatar {{
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.1);
    }}
    
    .bot .message-avatar {{
        background: linear-gradient(135deg, #4CAF50, #00d4aa);
    }}
    
    .user .message-avatar {{
        background: linear-gradient(135deg, #0066cc, #00d4aa);
    }}
    
    .message-bubble {{
        background: rgba(255, 255, 255, 0.08);
        padding: 14px 18px;
        border-radius: 18px;
        max-width: 80%;
        color: rgba(255, 255, 255, 0.95);
        font-size: 0.98rem;
        line-height: 1.6;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    
    .user .message-bubble {{
        background: linear-gradient(135deg, 
            rgba(0, 102, 204, 0.3), 
            rgba(0, 212, 170, 0.3));
        border-color: rgba(0, 212, 170, 0.3);
    }}
    
    .welcome-message {{
        text-align: center;
        padding: 30px 20px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    
    .welcome-message h4 {{
        color: #4CAF50;
        margin-bottom: 12px;
        font-size: 1.3rem;
        font-family: 'Playfair Display', serif;
    }}
    
    .quick-suggestions {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        padding: 0 24px 20px 24px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}
    
    .suggestion-chip {{
        background: rgba(76, 175, 80, 0.15);
        color: #66BB6A;
        padding: 10px 16px;
        border-radius: 20px;
        font-size: 0.88rem;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(76, 175, 80, 0.3);
        font-weight: 500;
    }}
    
    .suggestion-chip:hover {{
        background: rgba(76, 175, 80, 0.3);
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.25);
    }}
    
    .chatbot-footer {{
        padding: 20px 24px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(0, 0, 0, 0.25);
    }}
    
    .input-container {{
        display: flex;
        gap: 12px;
        align-items: center;
    }}
    
    #chatbot-input {{
        flex: 1;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 14px;
        padding: 14px 18px;
        color: white;
        font-size: 0.98rem;
        outline: none;
        transition: all 0.3s ease;
    }}
    
    #chatbot-input:focus {{
        background: rgba(255, 255, 255, 0.12);
        border-color: #4CAF50;
        box-shadow: 0 0 25px rgba(76, 175, 80, 0.25);
    }}
    
    #chatbot-input::placeholder {{
        color: rgba(255, 255, 255, 0.4);
    }}
    
    .send-btn {{
        background: linear-gradient(135deg, #4CAF50, #00d4aa);
        border: none;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
    }}
    
    .send-btn:hover {{
        transform: scale(1.1) rotate(15deg);
        box-shadow: 0 8px 20px rgba(76, 175, 80, 0.5);
    }}
    
    .send-btn svg {{
        width: 22px;
        height: 22px;
        fill: white;
    }}
    
    .typing-indicator {{
        display: flex;
        gap: 5px;
        padding: 14px 18px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        width: fit-content;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    .typing-dot {{
        width: 9px;
        height: 9px;
        background: #4CAF50;
        border-radius: 50%;
        animation: typing 1.4s ease infinite;
    }}
    
    .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
    
    @keyframes typing {{
        0%, 60%, 100% {{ transform: translateY(0); opacity: 0.7; }}
        30% {{ transform: translateY(-12px); opacity: 1; }}
    }}
    
    @media (max-width: 768px) {{
        .chatbot-popup {{
            width: calc(100vw - 30px);
            height: calc(100vh - 160px);
            bottom: 15px;
            right: 15px;
        }}
        
        .chatbot-trigger {{
            bottom: 15px;
            right: 15px;
            width: 60px;
            height: 60px;
        }}
    }}
    </style>
    
    <div class="chatbot-trigger" id="chatbotTrigger">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
            <circle cx="8" cy="10" r="1.5"/>
            <circle cx="12" cy="10" r="1.5"/>
            <circle cx="16" cy="10" r="1.5"/>
        </svg>
    </div>
    
    <div class="chatbot-popup" id="chatbotPopup">
        <div class="chatbot-header">
            <div class="chatbot-header-content">
                <div class="chatbot-avatar">🤖</div>
                <div>
                    <h3>{bot_config.get('title', 'AI Assistant')}</h3>
                    <div class="status">
                        <div class="status-dot"></div>
                        <span>Online</span>
                    </div>
                </div>
            </div>
            <button class="close-btn" id="closeChat">×</button>
        </div>
        
        <div class="quick-suggestions">
            <div class="suggestion-chip" onclick="sendSuggestion('¿Cuál es tu experiencia en Data Science?')">
                💼 Experiencia
            </div>
            <div class="suggestion-chip" onclick="sendSuggestion('¿Qué tecnologías dominas?')">
                🛠️ Skills
            </div>
            <div class="suggestion-chip" onclick="sendSuggestion('Cuéntame sobre tus proyectos')">
                🚀 Proyectos
            </div>
        </div>
        
        <div class="chatbot-body" id="chatbotBody">
            <div class="welcome-message">
                <h4>👋 ¡Bienvenido!</h4>
                <p>{bot_config.get('welcome_message', 'Pregúntame sobre mi experiencia, habilidades y proyectos.')}</p>
            </div>
        </div>
        
        <div class="chatbot-footer">
            <div class="input-container">
                <input 
                    type="text" 
                    id="chatbot-input" 
                    placeholder="Escribe tu pregunta..."
                    onkeypress="handleEnter(event)"
                />
                <button class="send-btn" onclick="sendMessage()">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    
    <script>
    // Estado del chat
    let chatHistory = [];
    
    // Toggle chatbot
    document.getElementById('chatbotTrigger').addEventListener('click', function() {{
        const popup = document.getElementById('chatbotPopup');
        popup.classList.toggle('active');
    }});
    
    document.getElementById('closeChat').addEventListener('click', function() {{
        document.getElementById('chatbotPopup').classList.remove('active');
    }});
    
    function sendSuggestion(text) {{
        document.getElementById('chatbot-input').value = text;
        sendMessage();
    }}
    
    function handleEnter(event) {{
        if (event.key === 'Enter') {{
            sendMessage();
        }}
    }}
    
    async function sendMessage() {{
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (message === '') return;
        
        addMessage(message, 'user');
        input.value = '';
        
        showTypingIndicator();
        
        try {{
            // Enviar mensaje a Streamlit para procesarlo
            const response = await fetch('/component/chatbot.query_gemini', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ 
                    query: message,
                    kb_text: `{kb_text.replace('`', '\\`')[:1000]}`  // Primeros 1000 chars
                }})
            }});
            
            hideTypingIndicator();
            
            // Simulación de respuesta (en producción esto vendría del backend)
            setTimeout(() => {{
                const botResponse = "Gracias por tu pregunta. Estoy aquí para ayudarte con información sobre mi experiencia en Data Science, AI y Bioinformática.";
                addMessage(botResponse, 'bot');
            }}, 500);
            
        }} catch (error) {{
            hideTypingIndicator();
            addMessage("Lo siento, hubo un error. Por favor intenta de nuevo.", 'bot');
        }}
    }}
    
    function addMessage(text, type) {{
        const chatBody = document.getElementById('chatbotBody');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${{type}}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'bot' ? '🤖' : '👤';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        chatBody.appendChild(messageDiv);
        
        chatBody.scrollTop = chatBody.scrollHeight;
        
        chatHistory.push({{ role: type, content: text }});
    }}
    
    let typingElement = null;
    
    function showTypingIndicator() {{
        const chatBody = document.getElementById('chatbotBody');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message bot';
        messageDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(typingDiv);
        chatBody.appendChild(messageDiv);
        typingElement = messageDiv;
        
        chatBody.scrollTop = chatBody.scrollHeight;
    }}
    
    function hideTypingIndicator() {{
        if (typingElement) {{
            typingElement.remove();
            typingElement = null;
        }}
    }}
    </script>
    """
    
    components.html(popup_html, height=0)

# ============================================
# MAIN APP LOGIC
# ============================================

# Initialize session state
if 'lang' not in st.session_state:
    st.session_state.lang = 'es'

# Load configurations
languages_conf = load_config()
texts = load_localization(st.session_state.lang)
profile = texts.get('profile', {})

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    # --- Profile Image ---
    st.image("assets/images/profile.png", use_container_width=True)
    
    # --- Language Selector ---
    lang_options = list(languages_conf.keys())
    selected_lang = st.selectbox(
        "Idioma / Language",
        options=lang_options,
        format_func=lambda x: f"{languages_conf[x]['flag']} {languages_conf[x]['name']}",
        index=lang_options.index(st.session_state.lang) if st.session_state.lang in lang_options else 0
    )
    
    if selected_lang != st.session_state.lang:
        st.session_state.lang = selected_lang
        st.rerun()
    
    # --- Profile Info ---
    st.title(profile.get('name', 'Alejandro Sánchez'))
    st.write(profile.get('location', ''))
    
    # --- Social Links con iconos SVG ---
    socials = profile.get('socials', {})
    st.markdown(f"""
    <div class="social-links">
        <a href="{socials.get('linkedin', '#')}" target="_blank" class="social-link">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
            </svg>
            LinkedIn
        </a>
        <a href="{socials.get('github', '#')}" target="_blank" class="social-link">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/>
            </svg>
            GitHub
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

# 1. Definir los archivos según el idioma seleccionado
    # Asumimos que la variable 'selected_lang' viene del selectbox que tienes más arriba
    if selected_lang == 'es':
        cv_options = {
            "Data Scientist": "assets/files/CV_Data_Science_ES_2026_Alejandro_Sanchez.pdf",
            "Data Analyst": "assets/files/CV_Data_Analyst_ES_2026_Alejandro_Sanchez.pdf"
        }
    elif selected_lang == 'de':
        cv_options = {
            "Data Scientist": "assets/files/CV_Data_Science_DE_2026_Alejandro_Sanchez.pdf",
            "Data Analyst": "assets/files/CV_Data_Analyst_DE_2026_Alejandro_Sanchez.pdf"
        }
    else:
        # Default: Inglés (para 'en' y cualquier otro idioma futuro como 'fr', 'it')
        cv_options = {
            "Data Scientist": "assets/files/CV_Data_Science_EN_2026_Alejandro_Sanchez.pdf",
            "Data Analyst": "assets/files/CV_Data_Analyst_EN_2026_Alejandro_Sanchez.pdf"
        }

    # 2. Selector de versión (Data Scientist vs Analyst)
    # Usamos key única para evitar errores de duplicidad de widgets si recarga
    selected_cv_key = st.radio(
        "Perfil", 
        list(cv_options.keys()),
        key=f"cv_radio_{selected_lang}" 
    )
    
    # 3. Lógica de lectura y descarga
    current_cv_path = cv_options[selected_cv_key]
    pdf_data = utils.read_pdf_byte_stream(current_cv_path)
    
    if pdf_data:
        st.download_button(
            label=texts.get('chatbot_config', {}).get('cv_download_text', 'Descargar CV'),
            data=pdf_data,
            # El nombre del archivo al descargar se adapta automáticamente
            file_name=current_cv_path.split("/")[-1], 
            mime="application/pdf",
        )


# ============================================
# MAIN CONTENT
# ============================================

# --- HERO ---
st.title(profile.get('tagline', 'Data Scientist'))

# --- ABOUT SECTION (Elegante, sin expander) ---
about = texts.get('about', {})
st.markdown(f"""
<div class="about-section">
    <h2>{about.get('title', 'Sobre Mí')}</h2>
    <p style="font-size: 1.15rem; margin-bottom: 1.5rem;">{about.get('text_short', '')}</p>
    <p>{about.get('text_long', '')}</p>
</div>
""", unsafe_allow_html=True)

# --- VALUE PROPOSITION (Si existe) ---
value_prop = texts.get('value_proposition', {})
if value_prop:
    st.markdown("---")
    st.header(value_prop.get('title', 'Propuesta de Valor'))
    
    points = value_prop.get('points', [])
    if points:
        cols = st.columns(min(len(points), 4))
        for idx, point in enumerate(points):
            with cols[idx % len(cols)]:
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem;">
                    <h4 style="color: var(--accent-color); margin-bottom: 0.8rem;">{point['title']}</h4>
                    <p style="font-size: 0.95rem; color: rgba(255,255,255,0.8);">{point['description']}</p>
                </div>
                """, unsafe_allow_html=True)

# --- SKILLS ---
st.markdown("---")
skills_sec = texts.get('skills_section', {})
st.header(skills_sec.get('title', 'Habilidades'))

categories = skills_sec.get('categories', [])
if categories:
    cols = st.columns(len(categories))
    
    for idx, cat in enumerate(categories):
        with cols[idx]:
            st.subheader(cat['name'])
            for item in cat['items']:
                st.write(f" · {item}")

# --- EXPERIENCE ---
st.markdown("---")
exp_sec = texts.get('experience_section', {})
st.header(exp_sec.get('title', 'Experiencia'))

for item in exp_sec.get('items', []):
    # Tech stack
    tech_stack_html = "".join([
        f"<span>{tech}</span>"
        for tech in item.get('stack', [])
    ])
    
    # Achievements (si existen)
    achievements_html = ""
    if 'achievements' in item and item['achievements']:
        achievements_html = "<ul style='margin-top: 1rem; color: rgba(255,255,255,0.8);'>"
        for achievement in item['achievements']:
            achievements_html += f"<li style='margin-bottom: 0.5rem;'>{achievement}</li>"
        achievements_html += "</ul>"
    
    # Location y type (si existen)
    meta_info = ""
    if 'location' in item:
        meta_info += f"<span style='color: #999; margin-right: 15px;'>📍 {item['location']}</span>"
    if 'type' in item:
        meta_info += f"<span style='color: #999;'>💼 {item['type']}</span>"
    
    st.markdown(f"""
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3>{item['role']}</h3>
            <span style="color:#4CAF50; font-weight:600; font-size:1rem;">{item['period']}</span>
        </div>
        <div style="color:#999; font-style:italic; margin-bottom:8px; font-size:0.98rem;">
            {item['company']}
        </div>
        <div style="margin-bottom:14px; font-size:0.9rem;">
            {meta_info}
        </div>
        <p>{item['description']}</p>
        {achievements_html}
        <div style="margin-top:14px;">{tech_stack_html}</div>
    </div>
    """, unsafe_allow_html=True)

# --- PROJECTS ---
st.markdown("---")
proj_sec = texts.get('projects_section', {})
st.header(proj_sec.get('title', 'Proyectos'))

projects = proj_sec.get('items', [])
if projects:
    # Agrupar por tipo o categoría
    project_types = list(set([p.get('type', p.get('category', 'General')) for p in projects]))
    tabs = st.tabs(project_types)

    for i, p_type in enumerate(project_types):
        with tabs[i]:
            type_projects = [p for p in projects if p.get('type', p.get('category', 'General')) == p_type]
            for idx, p in enumerate(type_projects):
                # Highlights si existen
                highlights_html = ""
                if 'highlights' in p and p['highlights']:
                    highlights_html = "<div style='margin-top: 1rem; padding: 1rem; background: rgba(76, 175, 80, 0.05); border-left: 3px solid var(--accent-color); border-radius: 8px;'>"
                    highlights_html += "<strong style='color: var(--accent-color);'>Logros Destacados:</strong><ul style='margin-top: 0.5rem; color: rgba(255,255,255,0.85);'>"
                    for highlight in p['highlights']:
                        highlights_html += f"<li style='margin-bottom: 0.4rem;'>{highlight}</li>"
                    highlights_html += "</ul></div>"
                
                # Year y link
                year_info = f" <span style='color: #999;'>({p['year']})</span>" if 'year' in p else ""
                link_html = f"<a href='{p['link']}' target='_blank' style='color: var(--accent-color); text-decoration: none;'>Ver proyecto →</a>" if p.get('link') else ""
                
                st.markdown(f"""
                <div style="margin-bottom: 2rem;">
                    <h3>{p['title']}{year_info}</h3>
                    <p>{p['description']}</p>
                    <p style="margin-top: 0.8rem;"><strong>Tech Stack:</strong> {', '.join(p['tech'])}</p>
                    {highlights_html}
                    {f'<p style="margin-top: 1rem;">{link_html}</p>' if link_html else ''}
                </div>
                """, unsafe_allow_html=True)
                
                if idx < len(type_projects) - 1:
                    st.markdown("---")

# --- EDUCATION ---
st.markdown("---")
edu_sec = texts.get('education_section', {})
st.header(edu_sec.get('title', 'Educación'))

for item in edu_sec.get('items', []):
    # Highlights si existen
    highlights_html = ""
    if 'highlights' in item and item['highlights']:
        highlights_html = "<ul style='margin-top: 0.8rem; margin-left: 1.5rem; color: rgba(255,255,255,0.75); font-size: 0.95rem;'>"
        for highlight in item['highlights']:
            highlights_html += f"<li style='margin-bottom: 0.4rem;'>{highlight}</li>"
        highlights_html += "</ul>"
    
    # Location y type si existen
    meta = ""
    if 'location' in item:
        meta += f" <span style='color: #999; font-size: 0.9rem;'>• {item['location']}</span>"
    if 'type' in item:
        meta += f" <span style='color: #999; font-size: 0.9rem;'>• {item['type']}</span>"
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"<p style='color: var(--accent-color); font-weight: 600; font-size: 1.1rem;'>{item['year']}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div>
            <p style='margin-bottom: 0.3rem;'><strong style='font-size: 1.1rem;'>{item['degree']}</strong></p>
            <p style='color: #999; font-style: italic; margin-bottom: 0.5rem;'>{item['institution']}{meta}</p>
            {highlights_html}
        </div>
        """, unsafe_allow_html=True)
        

# --- CERTIFICATIONS (Si existen en JSON) ---
cert_sec = texts.get('certifications_section', {})
if cert_sec and 'certifications' in cert_sec:
    st.markdown("---")
    st.header(cert_sec['certifications'].get('title', 'Certificaciones'))
    
    certs = cert_sec['certifications'].get('items', [])
    if certs:
        cols = st.columns(2)
        for idx, cert in enumerate(certs):
            with cols[idx % 2]:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.04); padding: 1.2rem; border-radius: 12px; 
                            margin-bottom: 1rem; border-left: 3px solid var(--accent-color);">
                    <h4 style="color: var(--accent-color); margin-bottom: 0.5rem; font-size: 1rem;">{cert['name']}</h4>
                    <p style="color: #999; margin-bottom: 0.3rem; font-size: 0.9rem;">{cert['issuer']}</p>
                    <p style="color: rgba(255,255,255,0.7); font-size: 0.85rem;">{cert['type']} • {cert['year']}</p>
                </div>
                """, unsafe_allow_html=True)

# --- PUBLICATIONS (Si existen en JSON) ---
pubs_sec = texts.get('publications_section', {})
if pubs_sec and 'items' in pubs_sec:
    st.markdown("---")
    st.header(pubs_sec.get('title', 'Publicaciones Científicas'))
    
    for pub in pubs_sec.get('items', []):
        doi_link = f"<a href='https://doi.org/{pub['doi']}' target='_blank' style='color: var(--accent-color); text-decoration: none;'>Ver publicación →</a>" if pub.get('doi') else ""
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.04); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
            <p style="font-size: 1.05rem; font-weight: 600; margin-bottom: 0.5rem; color: rgba(255,255,255,0.95);">
                {pub['title']}
            </p>
            <p style="color: #999; font-style: italic; margin-bottom: 0.5rem;">
                {pub['authors']}
            </p>
            <p style="color: rgba(255,255,255,0.8); font-size: 0.95rem;">
                <strong>{pub['journal']}</strong> ({pub['year']}) • {pub['type']}
            </p>
            <p style="color: rgba(255,255,255,0.8); font-size: 0.95rem;">
                {pub['description']}
            </p>
            {f'<p style="margin-top: 0.8rem;">{doi_link}</p>' if doi_link else ''}
        </div>
        """, unsafe_allow_html=True)

# --- INJECT CHATBOT POPUP ---
bot_config = texts.get('chatbot_config', {})
kb_text = chatbot.load_knowledge_base()
inject_chatbot_popup(bot_config, kb_text)

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.4); padding: 30px; font-size: 0.95rem;">
    <p style="font-family: 'Cormorant Garamond', serif; font-size: 1.1rem;">
        © 2026 Alejandro Sánchez | Diseñado con ♥ y Streamlit
    </p>
</div>
""", unsafe_allow_html=True)