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
    Loads the knowledge CSV and converts it into structured text
    for the LLM to understand as context.
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
    Builds the system prompt sent to the model.
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


# --- SERVER-SIDE CHAT ---
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
    Injects the floating chatbot HTML into the Streamlit app.
    All CSS has been moved to style.css for cleaner separation of concerns.
    """
    bot_title         = _html.escape(bot_config.get("title",             "AI Assistant"))
    status_text       = _html.escape(bot_config.get("status_text",       "Online"))
    welcome_title     = _html.escape(bot_config.get("welcome_title",     "👋 Welcome!"))
    welcome_message   = json.dumps(bot_config.get("welcome_message",   "Ask me anything."))
    input_placeholder = _html.escape(bot_config.get("input_placeholder", "Type your question..."))
    error_timeout     = _html.escape(bot_config.get("error_timeout",     "Response timed out. Please try again."))
    error_connection  = _html.escape(bot_config.get("error_connection",  "Internal error: could not reach the server."))

    raw_suggestions = bot_config.get("suggestions", [])
    suggestions_json = json.dumps(raw_suggestions, ensure_ascii=False)

    components.html(f"""
    <script>
    (function() {{
        const doc = window.parent.document;

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