import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- CONFIGURATION ---
# Load API Key from Streamlit secrets
try:
    GENAI_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    # Fallback para testing local sin secrets file
    GENAI_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not GENAI_API_KEY:
    st.error("Google API Key no encontrada. Configura .streamlit/secrets.toml con GOOGLE_API_KEY.")
    st.stop()

genai.configure(api_key=GENAI_API_KEY)

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

# --- SYSTEM PROMPT DEFINITION ---
def get_system_instruction(context_data: str) -> str:
    """
    Construye el system prompt que se enviará al modelo.
    
    Esta función es usada tanto por query_gemini() (llamadas desde Python)
    como por inject_chatbot_popup() en app.py (la inyecta en JS para 
    llamadas directas al API REST de Gemini desde el navegador).
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
    4. **Language:** Respond in the same language as the user's question (likely Spanish or English).
    5. **CVs & Links:** If the context contains a URL (e.g., for a CV), present it clearly to the user.
    
    ### RESTRICTIONS:
    - Do not mention that you are an AI model developed by Google unless asked.
    - Do not give advice outside the scope of the resume/portfolio.
    """

# --- MAIN CHAT FUNCTION ---
def query_gemini(user_input: str, knowledge_context: str) -> str:
    """
    Envía la pregunta del usuario junto con el system prompt a Gemini Flash.
    
    Nota: Esta función se usa para llamadas desde Python (e.g., testing, 
    integraciones server-side). El chatbot popup del portfolio llama a 
    Gemini directamente desde JavaScript para mayor fluidez.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    system_instruction = get_system_instruction(knowledge_context)
    
    try:
        response = model.generate_content(
            f"{system_instruction}\n\nUser Question: {user_input}"
        )
        return response.text
    except Exception as e:
        return "Lo siento, hubo un error de conexión. Por favor intenta más tarde."