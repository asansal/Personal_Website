import os
import json
import argparse
from google import genai
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).parent.parent
SECRETS_PATH = BASE_DIR / ".streamlit" / "secrets.toml"
CONFIG_PATH = BASE_DIR / "config" / "languages.json"
LOCALES_DIR = BASE_DIR / "locales"
SOURCE_FILE = LOCALES_DIR / "es.json"
AI_MODEL_FAST = "gemini-2.5-flash"
AI_MODEL_SMART = "gemini-2.5-pro"

# Diccionario maestro de soporte (puedes añadir más aquí)
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "it": {"name": "Italiano", "flag": "🇮🇹"},
    "pt": {"name": "Português", "flag": "🇵🇹"},
    "jp": {"name": "日本語", "flag": "🇯🇵"},
    "cn": {"name": "中文", "flag": "🇨🇳"}
}

def get_api_key():
    """Recupera la API Key de secrets.toml o variables de entorno."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key: return api_key
    if SECRETS_PATH.exists():
        try:
            with open(SECRETS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if "GOOGLE_API_KEY" in line:
                        return line.split("=")[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return None

def load_json(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def translate_content(client, source_data, target_lang_name):
    """Llama a Gemini para traducir."""
    prompt = f"""
    Role: Professional Technical Translator.
    Task: Translate the JSON values from Spanish to {target_lang_name}.
    Context: A Data Science & Bioinformatics Portfolio.
    
    Constraints:
    1. Keep exact JSON keys and structure.
    2. Translate ONLY values.
    3. Use technical terminology suitable for the target language.
    4. Output strictly valid JSON.

    Input:
    {json.dumps(source_data, indent=2, ensure_ascii=False)}
    """
    try:
        response = client.models.generate_content(model=AI_MODEL_FAST, contents=prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"❌ Error traduciendo a {target_lang_name}: {e}")
        return None

def update_config_file(lang_code):
    """Añade el nuevo idioma al archivo config/languages.json"""
    config = load_json(CONFIG_PATH)
    
    # Si ya existe, no hacemos nada (o podríamos actualizar banderas)
    if lang_code in config:
        return

    # Si es un idioma soportado en nuestro diccionario, cogemos sus datos
    if lang_code in SUPPORTED_LANGUAGES:
        config[lang_code] = SUPPORTED_LANGUAGES[lang_code]
    else:
        # Fallback genérico
        config[lang_code] = {"name": lang_code.upper(), "flag": "🏳️"}
    
    save_json(CONFIG_PATH, config)
    print(f"📝 Configuración actualizada: {lang_code} añadido a languages.json")

def process_language(client, lang_code, source_data, is_update=False):
    """Función core que gestiona la traducción y guardado."""
    target_info = SUPPORTED_LANGUAGES.get(lang_code, {"name": lang_code})
    target_name = target_info["name"]
    
    print(f"⏳ {'Actualizando' if is_update else 'Generando'} {target_name} ({lang_code})...")
    
    translated_data = translate_content(client, source_data, target_name)
    
    if translated_data:
        target_path = LOCALES_DIR / f"{lang_code}.json"
        save_json(target_path, translated_data)
        update_config_file(lang_code)
        print(f"✅ {target_name} listo en: {target_path}")
    else:
        print(f"❌ Falló {target_name}")

def main():
    parser = argparse.ArgumentParser(description="Gestor de Traducciones con IA")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", help="Código del idioma a añadir (ej: fr, de, it)")
    group.add_argument("--update", action="store_true", help="Actualiza todos los idiomas existentes basándose en es.json")
    
    args = parser.parse_args()
    
    # 1. Setup
    api_key = get_api_key()
    if not api_key:
        print("❌ Error: Falta API Key.")
        return
    client = genai.Client(api_key=api_key)

    # 2. Cargar Fuente
    if not SOURCE_FILE.exists():
        print(f"❌ No existe el archivo fuente: {SOURCE_FILE}")
        return
    source_data = load_json(SOURCE_FILE)

    # 3. Ejecutar lógica
    if args.add:
        process_language(client, args.add, source_data)
    
    elif args.update:
        config = load_json(CONFIG_PATH)
        print(f"🔄 Actualizando {len(config) - 1} idiomas (excluyendo 'es')...") # -1 por el español
        for lang_code in config:
            if lang_code == "es": continue # Saltamos la fuente
            process_language(client, lang_code, source_data, is_update=True)

if __name__ == "__main__":
    main()