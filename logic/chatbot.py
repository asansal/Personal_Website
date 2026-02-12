import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- CONFIGURATION ---
# Load API Key from Streamlit secrets
# Ensure your .streamlit/secrets.toml has [general] or just GOOGLE_API_KEY
try:
    GENAI_API_KEY = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    # Fallback for local testing without secrets file (not recommended for prod)
    GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GENAI_API_KEY:
    st.error("Google API Key not found. Please configure .streamlit/secrets.toml")
    st.stop()

genai.configure(api_key=GENAI_API_KEY)

# --- KNOWLEDGE BASE LOADING ---
@st.cache_data
def load_knowledge_base(file_path: str = "data/personal_knowledge.csv") -> str:
    """
    Loads the CSV knowledge base and converts it into a structured text format
    that the LLM can understand as context.
    
    Expected CSV columns: Category, Topic, Content
    """
    try:
        df = pd.read_csv(file_path)
        
        # Check if required columns exist
        required_columns = ["Category", "Topic", "Content"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"CSV format error. Required columns: {required_columns}")
            return ""

        # Convert dataframe to a string representation for the prompt context
        # Format: [Category] Topic: Content
        context_text = ""
        for _, row in df.iterrows():
            context_text += f"[{row['Category']}] {row['Topic']}: {row['Content']}\n"
            
        return context_text
        
    except FileNotFoundError:
        st.error(f"Knowledge base file not found at: {file_path}")
        return ""
    except Exception as e:
        st.error(f"Error loading knowledge base: {e}")
        return ""

# --- SYSTEM PROMPT DEFINITION ---
def get_system_instruction(context_data: str) -> str:
    """
    Constructs the rigid system prompt to prevent hallucinations.
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
def query_gemini(user_input: str, knowledge_context: str):
    """
    Sends the user query along with the system instruction to Gemini Flash.
    """
    # Initialize the model (Gemini 1.5 Flash is efficient for this)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Construct the full prompt
    system_instruction = get_system_instruction(knowledge_context)
    
    # We use a chat session logic or simple generation depending on needs.
    # For a simple Q&A, generate_content is sufficient and stateless (cheaper).
    # If we wanted memory of the conversation, we would use start_chat.
    
    try:
        # Combining system instruction + user query is a common pattern for 1-shot Q&A
        response = model.generate_content(
            f"{system_instruction}\n\nUser Question: {user_input}"
        )
        return response.text
    except Exception as e:
        return "Lo siento, hubo un error de conexión. Por favor intenta más tarde."