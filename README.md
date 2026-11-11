# asansal.com – portfolio with an AI assistant

Source code of my portfolio website, live at **[asansal.com](https://asansal.com)**.

I am an AI Engineer and Data Scientist with a background in bioinformatics. This site is a small production project of its own: a multilingual Streamlit app with a Gemini chatbot that answers questions about my experience from a closed knowledge base, deployed automatically to my own server.

## Features

- **AI assistant (Google Gemini API):** answers only from [`data/personal_knowledge.csv`](data/personal_knowledge.csv), in the visitor's language. If the answer is not in the knowledge base, it says so and points to LinkedIn or email instead of guessing.
- **Six languages:** Spanish, English, German, Swedish, Dutch and Danish. The language is detected from the browser and can be changed with the flag selector. All texts live in [`locales/`](locales/), one JSON file per language with identical keys. The CV download follows the selected language.
- **Single-page navigation:** home grid, experience, projects by category, Tableau dashboards, tech stack, education and contact, with custom CSS and a floating chatbot.
- **Social previews:** [`scripts/inject_meta.py`](scripts/inject_meta.py) writes Open Graph and Twitter tags into the HTML that Streamlit serves, so links shared on LinkedIn or WhatsApp show a preview image.
- **Command center:** a private Streamlit dashboard ([`panel/panel_app.py`](panel/panel_app.py)) at panel.asansal.com, behind Cloudflare Access. It shows visits, languages, countries, sections, CV downloads, outbound link clicks and chatbot questions grouped by topic. Tracking is cookieless (daily-salted hashes, no IPs stored) and lives in [`logic/analytics.py`](logic/analytics.py).
- **Abuse protection:** 5 chatbot questions per visitor and day, 5 more after a Cloudflare Turnstile check, a global daily cap on Gemini calls, and cached answers for the suggested questions. Setup guide: [`docs/SEGURIDAD_Y_PANEL.md`](docs/SEGURIDAD_Y_PANEL.md).
- **Continuous deployment:** every push to `main` runs a GitHub Actions workflow that updates the server over SSH and restarts the service.

## Tech stack

Python · Streamlit · Google Gemini API (`google-genai`) · SQLite · Altair · JSON (i18n) · CSV (knowledge base) · Cloudflare (Tunnel, Access, Turnstile) · GitHub Actions · Linux server on Oracle Cloud (systemd)

## Project structure

```
├── app.py                      # Streamlit app: layout, navigation and sections
├── logic/
│   ├── chatbot.py              # Knowledge base loading, system prompt and Gemini calls
│   ├── analytics.py            # Cookieless tracking, chatbot limits and answer cache (SQLite)
│   └── utils.py                # Helpers (CSS, JSON, images, PDFs)
├── locales/                    # es, en, de, sv, nl, da: all site texts
├── config/languages.json       # Available languages and flags
├── data/personal_knowledge.csv # Knowledge base for the chatbot
├── assets/
│   ├── css/style.css           # Custom styles
│   ├── images/                 # Photos, project images, app icon
│   └── files/                  # CV in each language (CV_Alejandro_Sanchez_XX.pdf)
├── static/                     # Served at /app/static/ (preview image, favicon)
├── panel/panel_app.py          # Private command center (panel.asansal.com)
├── deploy/                     # systemd unit for the panel, Cloudflare Tunnel config
├── docs/SEGURIDAD_Y_PANEL.md   # Cloudflare, Turnstile, tunnel and server hardening
├── scripts/
│   ├── inject_meta.py          # SEO / Open Graph tags (run on every deploy)
│   └── generate_locales.py     # Machine translation helper for new languages
└── .github/workflows/deploy.yml
```

## Run it locally

```bash
git clone https://github.com/asansal/Personal_Website.git
cd Personal_Website
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The chatbot needs a Google Gemini API key in `.streamlit/secrets.toml` (this file is git-ignored):

```toml
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
GENAI_API_KEY = "YOUR_API_KEY_HERE"
```

Without a key the site works normally and only the chatbot is disabled. Optional keys: `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY` (the "not a robot" check after 5 questions) and `PANEL_ALLOWED_EMAIL` (the command center).

To open the command center locally:

```bash
PANEL_LOCAL=1 streamlit run panel/panel_app.py --server.port 8502
```

## Other projects

- **[Job Matcher](https://lab.asansal.com/job-matcher):** AI job application assistant with structured output, hallucination validators and RAG with Google Search grounding.
- **[Sextant IA](https://sextantia.eu):** multi-stage LLM travel planner built with Django, in production.

## Contact

[LinkedIn](https://www.linkedin.com/in/alejandro-sanchez-salvador) · asansal@outlook.es
