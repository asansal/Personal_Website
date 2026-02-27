import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from google import genai
import json
import html as _html
import os


# --- CHATBOT INITIALIZATION ---
def initialize_chatbot() -> str | None:
    """
    Loads API key from secrets and sets it as an environment variable.
    Returns the API key if successful, otherwise None.
    """
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except (FileNotFoundError, KeyError):
        api_key = os.getenv("GOOGLE_API_KEY", "")

    if not api_key:
        st.error("Google API Key no encontrada. Configura .streamlit/secrets.toml con GOOGLE_API_KEY.")
        return None

    os.environ['GOOGLE_API_KEY'] = api_key
    return api_key


# --- KNOWLEDGE BASE LOADING ---
@st.cache_data
def load_knowledge_base(file_path: str = "data/personal_knowledge.csv") -> str:
    """
    Carga el CSV de conocimiento y lo convierte en texto estructurado
    que el LLM puede entender como contexto.

    Columnas esperadas en el CSV: Category, Topic, Content
    """
    try:
        df = pd.read_csv(file_path)

        required_columns = ["Category", "Topic", "Content"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"Error de formato en el CSV. Columnas requeridas: {required_columns}")
            return ""

        context_text = ""
        for _, row in df.iterrows():
            context_text += f"[{row['Category']}] {row['Topic']}: {row['Content']}\n"

        return context_text

    except FileNotFoundError:
        st.error(f"Archivo de conocimiento no encontrado en: {file_path}")
        return ""
    except Exception as e:
        st.error(f"Error cargando la base de conocimiento: {e}")
        return ""


# --- SYSTEM PROMPT ---
def get_system_instruction(context_data: str, lang: str = "es") -> str:
    lang_names = {"es": "Spanish", "en": "English", "de": "German"}
    response_lang = lang_names.get(lang, "English")

    """
    Construye el system prompt que se enviará al modelo.
    """
    return f"""
    You are the AI Assistant for a professional portfolio website.
    Your goal is to answer visitor questions about the professional profile, skills, and experience of the owner, strictly based on the provided context.

    --- CONTEXT STARTS HERE ---
    {context_data}
    --- CONTEXT ENDS HERE ---

    ### INSTRUCTIONS:
    1. **Strict Grounding:** Answer ONLY using the information provided in the CONTEXT above.
    2. **No Hallucinations:** If the answer is not in the context, do NOT make it up. Instead, politely say: "Lo siento, no tengo esa información específica en mi base de datos actual. ¿Te gustaría contactar directamente por email para preguntar?"
    3. **Tone:** Be friendly, humble, but professional and structured. Avoid being overly enthusiastic or robotic.
    4. **Language:** Respond in {response_lang} by default (can be ES, EN or DE), or in the language the user writes in.
    5. **CVs & Links:** If the context contains a URL (e.g., for a CV), present it clearly to the user.

    ### RESTRICTIONS:
    - Do not mention that you are an AI model developed by Google unless asked.
    - Do not give advice outside the scope of the resume/portfolio.
    - Do not use filler phrases like "Of course", "Sure!", "Certainly", "Claro", "Por supuesto",
      "I hope this helps", "Espero que te sea útil", "Feel free to ask", or any similar opener/closer.
      Go directly to the answer.
    """


# --- SERVER-SIDE CHAT (llamada Python → Gemini) ---
def query_gemini(user_input: str, knowledge_context: str, lang: str = "es") -> str:
    try:
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        system_instruction = get_system_instruction(knowledge_context, lang)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_input,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
            )
        )
        return response.text
    except Exception as e:
        st.error(f"Chatbot Gemini Error: {e}")
        return "Lo siento, hubo un error al procesar tu pregunta. Por favor intenta más tarde."


# --- CHATBOT POPUP INJECTION ---
def inject_chatbot_popup(bot_config: dict, kb_text: str, api_key: str) -> None:
    """
    Inyecta el chatbot flotante en la aplicación Streamlit.
    Todos los textos se leen desde bot_config (cargado del JSON de localización),
    por lo que el popup se adapta automáticamente al idioma seleccionado.

    Estrategia:
    - HTML y CSS se inyectan solo una vez (guardados por id).
    - Los event listeners se re-adjuntan SIEMPRE fuera del guard del DOM,
      usando cloneNode para evitar duplicados. Esto permite que el popup
      sobreviva a reruns de Streamlit (ej: cambio de idioma).
    """
    # ── Textos desde el JSON de localización ─────────────────────────────────
    bot_title         = _html.escape(bot_config.get("title",             "AI Assistant"))
    status_text       = _html.escape(bot_config.get("status_text",       "Online"))
    welcome_title     = _html.escape(bot_config.get("welcome_title",     "👋 Welcome!"))
    welcome_message   = json.dumps(bot_config.get("welcome_message",   "Ask me anything."))
    input_placeholder = _html.escape(bot_config.get("input_placeholder", "Type your question..."))
    error_timeout     = _html.escape(bot_config.get("error_timeout",     "Response timed out. Please try again."))
    error_connection  = _html.escape(bot_config.get("error_connection",  "Internal error: could not reach the server."))

    # Suggestions: lista de {label, msg} serializada a JSON para usarla en JS
    raw_suggestions = bot_config.get("suggestions", [])
    suggestions_json = json.dumps(raw_suggestions, ensure_ascii=False)

    components.html(f"""
    <script>
    (function() {{
        const doc = window.parent.document;

        // ── 1. INYECTAR CSS (solo una vez) ───────────────────────────────────
        if (!doc.getElementById('chatbot-injected-styles')) {{
            const style = doc.createElement('style');
            style.id = 'chatbot-injected-styles';
            style.textContent = `
                .chatbot-trigger {{
                    position: fixed; bottom: 30px; right: 30px; width: 70px; height: 70px;
                    background: linear-gradient(135deg, #4CAF50, #00d4aa); border-radius: 50%;
                    display: flex; align-items: center; justify-content: center; cursor: pointer;
                    box-shadow: 0 8px 30px rgba(76,175,80,0.5), 0 0 40px rgba(0,212,170,0.3);
                    transition: all 0.4s cubic-bezier(0.4,0,0.2,1); z-index: 10000;
                    border: 3px solid rgba(255,255,255,0.15);
                    animation: cb-pulse-ring 3s cubic-bezier(0.4,0,0.2,1) infinite;
                }}
                @keyframes cb-pulse-ring {{
                    0%,100% {{ box-shadow: 0 8px 30px rgba(76,175,80,0.5), 0 0 40px rgba(0,212,170,0.3), 0 0 0 0 rgba(76,175,80,0.7); }}
                    50%      {{ box-shadow: 0 8px 30px rgba(76,175,80,0.5), 0 0 40px rgba(0,212,170,0.3), 0 0 0 15px rgba(76,175,80,0); }}
                }}
                .chatbot-trigger:hover {{ transform: scale(1.15) rotate(10deg); }}
                .chatbot-trigger svg  {{ width: 35px; height: 35px; fill: white; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }}

                .chatbot-popup {{
                    position: fixed; bottom: 120px; right: 30px; width: 420px; height: 600px;
                    background: linear-gradient(180deg, rgba(10,14,39,0.98) 0%, rgba(22,33,62,0.96) 100%);
                    border-radius: 24px;
                    box-shadow: 0 25px 80px rgba(0,0,0,0.6), 0 0 60px rgba(76,175,80,0.25), inset 0 1px 2px rgba(255,255,255,0.1);
                    backdrop-filter: blur(30px) saturate(180%); border: 1px solid rgba(76,175,80,0.3);
                    display: none; flex-direction: column; overflow: hidden; z-index: 9999;
                }}
                .chatbot-popup.active {{ display: flex; animation: cb-slideUpScale 0.5s cubic-bezier(0.34,1.56,0.64,1); }}
                @keyframes cb-slideUpScale {{
                    from {{ opacity: 0; transform: translateY(40px) scale(0.9); }}
                    to   {{ opacity: 1; transform: translateY(0)   scale(1);   }}
                }}

                .chatbot-header {{
                    background: linear-gradient(135deg, #4CAF50 0%, #00d4aa 100%); padding: 24px;
                    display: flex; justify-content: space-between; align-items: center;
                    border-bottom: 1px solid rgba(255,255,255,0.15); box-shadow: 0 4px 20px rgba(0,0,0,0.25);
                    flex-shrink: 0;
                }}
                .chatbot-header-content {{ display: flex; align-items: center; gap: 12px; }}
                .chatbot-avatar {{
                    width: 45px; height: 45px; background: rgba(255,255,255,0.2); border-radius: 12px;
                    display: flex; align-items: center; justify-content: center; font-size: 24px;
                    border: 2px solid rgba(255,255,255,0.3);
                }}
                .chatbot-header h3 {{
                    color: white; margin: 0; font-size: 1.3rem; font-weight: 700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                .chatbot-header .status {{ display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: rgba(255,255,255,0.95); }}
                .status-dot {{
                    width: 9px; height: 9px; background: #66FF66; border-radius: 50%;
                    animation: cb-pulse-dot 2s ease infinite; box-shadow: 0 0 12px #66FF66;
                }}
                @keyframes cb-pulse-dot {{ 0%,100% {{ transform: scale(1); opacity: 1; }} 50% {{ transform: scale(1.2); opacity: 0.7; }} }}
                .chatbot-close-btn {{
                    background: rgba(255,255,255,0.2); border: none; color: white; width: 36px; height: 36px;
                    border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
                    transition: all 0.3s ease; font-size: 22px; font-weight: bold; line-height: 1;
                }}
                .chatbot-close-btn:hover {{ background: rgba(255,255,255,0.35); transform: rotate(90deg) scale(1.1); }}

                .quick-suggestions {{
                    display: flex; flex-wrap: wrap; gap: 10px; padding: 16px 24px;
                    border-bottom: 1px solid rgba(255,255,255,0.08); flex-shrink: 0;
                }}
                .suggestion-chip {{
                    background: rgba(76,175,80,0.15); color: #66BB6A; padding: 8px 14px; border-radius: 20px;
                    font-size: 0.88rem; cursor: pointer; transition: all 0.3s ease;
                    border: 1px solid rgba(76,175,80,0.3); font-weight: 500;
                    font-family: inherit;
                }}
                .suggestion-chip:hover {{ background: rgba(76,175,80,0.3); transform: translateY(-2px); }}

                .chatbot-body {{
                    flex: 1; overflow-y: auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 14px;
                }}
                .chatbot-body::-webkit-scrollbar {{ width: 8px; }}
                .chatbot-body::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); border-radius: 4px; }}
                .chatbot-body::-webkit-scrollbar-thumb {{ background: linear-gradient(180deg, #4CAF50, #00d4aa); border-radius: 4px; }}

                .chat-message {{ display: flex; gap: 12px; animation: cb-fadeIn 0.4s ease; }}
                @keyframes cb-fadeIn {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
                .chat-message.bot  {{ align-self: flex-start; }}
                .chat-message.user {{ align-self: flex-end; flex-direction: row-reverse; }}
                .message-avatar {{
                    width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center;
                    justify-content: center; flex-shrink: 0; font-size: 20px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 2px solid rgba(255,255,255,0.1);
                }}
                .chat-message.bot  .message-avatar {{ background: linear-gradient(135deg, #4CAF50, #00d4aa); }}
                .chat-message.user .message-avatar {{ background: linear-gradient(135deg, #0066cc, #00d4aa); }}
                .message-bubble {{
                    background: rgba(255,255,255,0.08); padding: 14px 18px; border-radius: 18px; max-width: 80%;
                    color: rgba(255,255,255,0.95); font-size: 0.95rem; line-height: 1.6;
                    border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                    white-space: pre-wrap; word-break: break-word;
                }}
                .chat-message.user .message-bubble {{
                    background: linear-gradient(135deg, rgba(0,102,204,0.3), rgba(0,212,170,0.3));
                    border-color: rgba(0,212,170,0.3);
                }}
                .chatbot-welcome {{
                    text-align: center; padding: 30px 20px; color: rgba(255,255,255,0.7);
                    font-size: 0.95rem; line-height: 1.6;
                }}
                .chatbot-welcome h4 {{ color: #4CAF50; margin-bottom: 12px; font-size: 1.2rem; }}

                .chatbot-footer {{
                    padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.1);
                    background: rgba(0,0,0,0.25); flex-shrink: 0;
                }}
                .chatbot-input-container {{ display: flex; gap: 10px; align-items: center; }}
                #chatbot-text-input {{
                    flex: 1; background: rgba(255,255,255,0.08); border: 1px solid rgba(76,175,80,0.3);
                    border-radius: 14px; padding: 12px 16px; color: white; font-size: 0.96rem;
                    outline: none; transition: all 0.3s ease; font-family: inherit;
                }}
                #chatbot-text-input:focus {{
                    background: rgba(255,255,255,0.12); border-color: #4CAF50;
                    box-shadow: 0 0 20px rgba(76,175,80,0.2);
                }}
                #chatbot-text-input::placeholder {{ color: rgba(255,255,255,0.4); }}
                #chatbot-text-input:disabled     {{ opacity: 0.5; cursor: not-allowed; }}
                .chatbot-send-btn {{
                    background: linear-gradient(135deg, #4CAF50, #00d4aa); border: none; width: 46px; height: 46px;
                    border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
                    transition: all 0.3s ease; box-shadow: 0 6px 16px rgba(76,175,80,0.4); flex-shrink: 0;
                }}
                .chatbot-send-btn:hover {{ transform: scale(1.1) rotate(15deg); }}
                .chatbot-send-btn svg {{ width: 20px; height: 20px; fill: white; }}
                .chatbot-typing {{
                    display: flex; gap: 5px; padding: 12px 16px; background: rgba(255,255,255,0.08);
                    border-radius: 18px; width: fit-content; border: 1px solid rgba(255,255,255,0.1);
                }}
                .chatbot-typing-dot {{
                    width: 8px; height: 8px; background: #4CAF50; border-radius: 50%;
                    animation: cb-typing 1.4s ease infinite;
                }}
                .chatbot-typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
                .chatbot-typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
                @keyframes cb-typing {{
                    0%,60%,100% {{ transform: translateY(0); opacity: 0.7; }}
                    30%          {{ transform: translateY(-10px); opacity: 1; }}
                }}

                @media (max-width: 768px) {{
                    .chatbot-popup   {{ width: calc(100vw - 30px); height: calc(100vh - 160px); bottom: 15px; right: 15px; }}
                    .chatbot-trigger {{ bottom: 15px; right: 15px; width: 60px; height: 60px; }}
                }}
            `;
            doc.head.appendChild(style);
        }}

        // ── 2. INYECTAR HTML (solo una vez) ──────────────────────────────────
        if (!doc.getElementById('chatbot-root')) {{
            const root = doc.createElement('div');
            root.id = 'chatbot-root';
            root.innerHTML = `
                <div class="chatbot-trigger" id="chatbotTrigger">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                        <circle cx="8"  cy="10" r="1.5"/>
                        <circle cx="12" cy="10" r="1.5"/>
                        <circle cx="16" cy="10" r="1.5"/>
                    </svg>
                </div>

                <div class="chatbot-popup" id="chatbotPopup">
                    <div class="chatbot-header">
                        <div class="chatbot-header-content">
                            <div class="chatbot-avatar">🤖</div>
                            <div>
                                <h3 id="chatbotTitle">{bot_title}</h3>
                                <div class="status">
                                    <div class="status-dot"></div>
                                    <span id="chatbotStatusText">{status_text}</span>
                                </div>
                            </div>
                        </div>
                        <button class="chatbot-close-btn" id="chatbotCloseBtn">&times;</button>
                    </div>

                    <div class="quick-suggestions" id="chatbotSuggestions"></div>

                    <div class="chatbot-body" id="chatbotBody">
                        <div class="chatbot-welcome" id="chatbotWelcome">
                            <h4 id="chatbotWelcomeTitle">{welcome_title}</h4>
                            <p id="chatbotWelcomeMsg">{welcome_message}</p>
                        </div>
                    </div>

                    <div class="chatbot-footer">
                        <div class="chatbot-input-container">
                            <input type="text" id="chatbot-text-input"
                                   placeholder="{input_placeholder}" autocomplete="off"/>
                            <button class="chatbot-send-btn" id="chatbotSendBtn">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            doc.body.appendChild(root);
        }}

        // ── 3. ACTUALIZAR TEXTOS LOCALIZADOS (siempre, en cada rerun) ────────
        //
        // Aunque el DOM no se recrea, los textos deben refrescarse cuando
        // el usuario cambia de idioma y Streamlit hace rerun.
        //
        const suggestions = {suggestions_json};

        const titleEl = doc.getElementById('chatbotTitle');
        if (titleEl) titleEl.textContent = '{bot_title}';

        const statusEl = doc.getElementById('chatbotStatusText');
        if (statusEl) statusEl.textContent = '{status_text}';

        const welcomeTitleEl = doc.getElementById('chatbotWelcomeTitle');
        if (welcomeTitleEl) welcomeTitleEl.textContent = '{welcome_title}';

        const welcomeMsgEl = doc.getElementById('chatbotWelcomeMsg');
        if (welcomeMsgEl) welcomeMsgEl.textContent = '{welcome_message}';

        const inputEl2 = doc.getElementById('chatbot-text-input');
        if (inputEl2) inputEl2.placeholder = '{input_placeholder}';

        // Reconstruir los chips de sugerencias con el idioma actual
        const suggestionsContainer = doc.getElementById('chatbotSuggestions');
        if (suggestionsContainer) {{
            suggestionsContainer.innerHTML = '';
            suggestions.forEach(function(s) {{
                const btn = doc.createElement('button');
                btn.className    = 'suggestion-chip';
                btn.dataset.msg  = s.msg;
                btn.textContent  = s.label;
                suggestionsContainer.appendChild(btn);
            }});
        }}

        // ── 4. RE-ADJUNTAR EVENTOS (siempre, en cada rerun) ──────────────────
        //
        // Usamos cloneNode + replaceChild para eliminar listeners anteriores
        // antes de añadir los nuevos, evitando duplicados acumulados.
        //
        let typingElement = null;

        function reattach(id, event, handler) {{
            const el = doc.getElementById(id);
            if (!el) return;
            const clone = el.cloneNode(true);
            el.parentNode.replaceChild(clone, el);
            doc.getElementById(id).addEventListener(event, handler);
        }}

        reattach('chatbotTrigger', 'click', function() {{
            doc.getElementById('chatbotPopup').classList.toggle('active');
        }});

        reattach('chatbotCloseBtn', 'click', function() {{
            doc.getElementById('chatbotPopup').classList.remove('active');
        }});

        reattach('chatbotSendBtn', 'click', function() {{
            sendMessage();
        }});

        reattach('chatbotSuggestions', 'click', function(e) {{
            const chip = e.target.closest('.suggestion-chip');
            if (chip) sendMessage(chip.dataset.msg);
        }});

        // El input necesita tratamiento especial para preservar el valor escrito
        const inputEl = doc.getElementById('chatbot-text-input');
        if (inputEl) {{
            const savedValue    = inputEl.value;
            const savedDisabled = inputEl.disabled;
            const newInput = inputEl.cloneNode(true);
            inputEl.parentNode.replaceChild(newInput, inputEl);
            const freshInput = doc.getElementById('chatbot-text-input');
            freshInput.value       = savedValue;
            freshInput.disabled    = savedDisabled;
            freshInput.placeholder = '{input_placeholder}';
            freshInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendMessage(); }}
            }});
        }}

        // ── 5. LÓGICA DEL CHAT (bridge a Python) ─────────────────────────────

        function triggerStreamlitInput(message) {{
            const stInput = doc.querySelector('input[aria-label="__cb_input__"]');
            if (!stInput) {{
                console.warn('[Chatbot] No se encontró el input bridge de Streamlit.');
                return false;
            }}
            const nativeSetter = Object.getOwnPropertyDescriptor(
                window.parent.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(stInput, message);
            stInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            ['keydown','keypress','keyup'].forEach(function(evtType) {{
                stInput.dispatchEvent(new KeyboardEvent(evtType, {{
                    key: 'Enter', code: 'Enter', keyCode: 13,
                    charCode: 13, which: 13, bubbles: true
                }}));
            }});
            return true;
        }}

        function sendMessage(suggestion) {{
            const activeInput = doc.getElementById('chatbot-text-input');
            const message = (suggestion !== undefined ? suggestion : activeInput.value).trim();
            if (!message) return;

            addMessage(message, 'user');
            activeInput.value    = '';
            activeInput.disabled = true;
            showTypingIndicator();

            const responseDiv = doc.getElementById('cb-py-response');
            const baseId = responseDiv
                ? parseInt(responseDiv.getAttribute('data-id') || '0', 10)
                : 0;

            const ok = triggerStreamlitInput(message);
            if (!ok) {{
                hideTypingIndicator();
                addMessage('{error_connection}', 'bot');
                activeInput.disabled = false;
                return;
            }}

            let elapsed = 0;
            const maxWait = 60000;
            const interval = setInterval(function() {{
                elapsed += 500;
                const rd = doc.getElementById('cb-py-response');
                if (rd) {{
                    const newId = parseInt(rd.getAttribute('data-id') || '0', 10);
                    if (newId > baseId) {{
                        clearInterval(interval);
                        hideTypingIndicator();
                        const botReply = rd.textContent || rd.innerText || '';
                        addMessage(botReply.trim(), 'bot');
                        activeInput.disabled = false;
                        activeInput.focus();
                        return;
                    }}
                }}
                if (elapsed >= maxWait) {{
                    clearInterval(interval);
                    hideTypingIndicator();
                    addMessage('{error_timeout}', 'bot');
                    activeInput.disabled = false;
                }}
            }}, 500);
        }}

        function addMessage(text, type) {{
            const chatBody   = doc.getElementById('chatbotBody');
            const messageDiv = doc.createElement('div');
            messageDiv.className = 'chat-message ' + type;

            const avatar       = doc.createElement('div');
            avatar.className   = 'message-avatar';
            avatar.textContent = type === 'bot' ? '🤖' : '👤';

            const bubble       = doc.createElement('div');
            bubble.className   = 'message-bubble';
            bubble.textContent = text;

            messageDiv.appendChild(avatar);
            messageDiv.appendChild(bubble);
            chatBody.appendChild(messageDiv);
            chatBody.scrollTop = chatBody.scrollHeight;
        }}

        function showTypingIndicator() {{
            const chatBody   = doc.getElementById('chatbotBody');
            const messageDiv = doc.createElement('div');
            messageDiv.className = 'chat-message bot';
            messageDiv.id        = 'chatbot-typing-row';

            const avatar       = doc.createElement('div');
            avatar.className   = 'message-avatar';
            avatar.textContent = '🤖';

            const typingDiv     = doc.createElement('div');
            typingDiv.className = 'chatbot-typing';
            typingDiv.innerHTML = '<div class="chatbot-typing-dot"></div><div class="chatbot-typing-dot"></div><div class="chatbot-typing-dot"></div>';

            messageDiv.appendChild(avatar);
            messageDiv.appendChild(typingDiv);
            chatBody.appendChild(messageDiv);
            typingElement      = messageDiv;
            chatBody.scrollTop = chatBody.scrollHeight;
        }}

        function hideTypingIndicator() {{
            if (typingElement) {{ typingElement.remove(); typingElement = null; }}
        }}

    }})();
    </script>
    """, height=0)