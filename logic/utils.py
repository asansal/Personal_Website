import streamlit as st
from pathlib import Path
import base64
import json


# --- CSS ---

def load_css(file_path: str) -> None:
    """
    Reads a CSS file and injects it into the Streamlit app.

    Args:
        file_path (str): Relative path to the CSS file (e.g., "assets/css/style.css").
    """
    try:
        with open(file_path, "r") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ CSS file not found at: {file_path}. The app will run without custom styles.")
    except Exception as e:
        st.error(f"Error loading CSS: {e}")


# --- FILES ---

def read_pdf_byte_stream(file_path: str) -> bytes | None:
    """
    Reads a PDF file in binary mode to be used in download buttons.

    Args:
        file_path (str): Relative path to the PDF file.

    Returns:
        bytes: The binary content of the file, or None if not found.
    """
    path = Path(file_path)
    if path.is_file():
        with open(path, "rb") as f:
            return f.read()
    else:
        st.error(f"❌ PDF not found: {file_path}")
        return None


def get_img_as_base64(file_path: str) -> str:
    """
    Encodes an image to base64 string.
    Useful to embed images directly in HTML/CSS (e.g., circular profile pics).

    Args:
        file_path (str): Path to the image.

    Returns:
        str: Base64 encoded string of the image, or empty string if not found.
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""


# --- LOCALISATION ---

@st.cache_data
def load_localization(lang_code: str) -> dict:
    """
    Carga el archivo de localización JSON para el idioma indicado.

    Args:
        lang_code (str): Código de idioma (e.g., 'es', 'en', 'de').

    Returns:
        dict: Diccionario con los textos localizados, o {} si no se encuentra.
    """
    try:
        with open(f"locales/{lang_code}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Locale file not found: locales/{lang_code}.json")
        return {}
    except json.JSONDecodeError as e:
        st.error(f"Error parsing locale file for '{lang_code}': {e}")
        return {}


@st.cache_data
def load_config(file_path: str = "config/languages.json") -> dict:
    """
    Carga el archivo de configuración de idiomas disponibles.

    Args:
        file_path (str): Ruta al JSON de configuración.

    Returns:
        dict: Configuración de idiomas, con fallback a español.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"es": {"name": "Español", "flag": "🇪🇸"}}
    except json.JSONDecodeError as e:
        st.error(f"Error parsing config file: {e}")
        return {"es": {"name": "Español", "flag": "🇪🇸"}}