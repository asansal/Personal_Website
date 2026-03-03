# Data Science & AI Portfolio

Hello! Welcome to the source code of my professional portfolio. I designed this space not just as a digital resume to showcase my career path, but as an interactive project in itself. Here, I apply my knowledge in Python, data application development, and the use of Large Language Models (LLMs) to create a dynamic user experience.

You can visit the live version of this portfolio here [missing link]

## Key Features

This project goes a step beyond a traditional static page. I have implemented several features focused on usability and AI integration:

- **Virtual Assistant (Gemini Chatbot)**: The website integrates a custom conversational agent using the Google Gemini API. This bot reads from a closed context (my knowledge base) and answers questions about my experience, projects, and skills, preventing hallucinations or out-of-context responses.

- **Multilingual Support (i18n)**: All website content is centralized in .json files within the locales/ folder. This allows for seamless, real-time interface language switching, while also adapting resume downloads to the active language.

- **Responsive Design and CSS/JS Injection**: Although Streamlit is excellent for rapid prototyping, I have injected custom CSS and JavaScript to achieve advanced UI components (such as the floating chatbot pop-up) and improve the mobile experience.

## Tech Stack

- **Backend & Frontend**: Python 3.10+, Streamlit

- **Artificial Intelligence**: Google GenAI SDK (Gemini 2.5 Flash)

- **Data Processing (Bot Context)**: Pandas

- **Data Structure**: JSON (Localization), CSV (Knowledge Base)

## Project Structure

The repository is organized as follows to maintain a clean separation between the interface, logic, and data:

```
├── app.py                  # Main entry point for the Streamlit application
├── logic/
│   ├── chatbot.py          # Connection logic for the Gemini API and prompting
│   └── utils.py            # Helper functions (image encoding, PDF reading, JSON loading)
├── locales/
│   ├── es.json             # Texts and translations in Spanish
│   ├── en.json             # Texts and translations in English
│   └── de.json             # Texts and translations in German
├── data/
│   └── personal_knowledge.csv # Knowledge base feeding the Chatbot
├── assets/
│   ├── css/                # Custom stylesheets
│   ├── images/             # Photographs and icons
│   └── files/              # PDF documents (Resumes in different languages)
└── requirements.txt        # Project dependencies
```

## Local Installation and Deployment

If you want to clone this repository and run it locally to see how it works under the hood, follow these steps:

Clone the repository:

```
git clone [https://github.com/asansal/Personal_Website.git](https://github.com/asansal/Personal_Website.git)
cd portfolio-streamlit
```

Create a virtual environment and install dependencies:

```
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Configure the Google Gemini API key:
The chatbot requires a Google API Key to function. For security reasons, it is not included in the code. You must create a file at .streamlit/secrets.toml in the root of the project and add your key:

```
# .streamlit/secrets.toml
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
GENAI_API_KEY =  "YOUR_API_KEY_HERE"
```

(Note: If you do not configure the API Key, the website will still work perfectly; the chatbot will simply display a friendly warning that it is unavailable).

Run the application:

```
streamlit run app.py
```

#### About Me

After more than 4 years managing terabytes of data in high-level research environments (CSIC-UAM, Universität Konstanz), I have formalized my transition to the tech and business sector with a Master's degree in Data Science & AI. I am accustomed to ensuring data integrity, continuously seeking process efficiency, and translating complex analyses into strategic business decisions.

If you are interested in my profile or want to discuss technology, data science, or potential collaborations, feel free to contact me via LinkedIn or email at asansal@outlook.es.
