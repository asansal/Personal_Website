import streamlit as st
from pathlib import Path
import base64

def load_css(file_path: str):
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

def read_pdf_byte_stream(file_path: str) -> bytes:
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
    Useful if you want to embed an image directly in HTML/CSS (e.g., for circular profile pics in custom HTML).
    
    Args:
        file_path (str): Path to the image.
        
    Returns:
        str: Base64 encoded string of the image.
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""