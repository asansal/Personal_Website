"""Pre-generate the chatbot answers to every suggested question, in every language.

The site serves these answers without calling Gemini, so the suggestion buttons and the
follow-up suggestions never spend tokens or count towards a visitor's limit.

Run it again after editing data/personal_knowledge.csv or the suggestions in locales/:
answers whose question and knowledge base did not change are kept (no new calls).
While data/chat_answers.json is out of date, the site answers those questions live once
and caches them, so it never serves answers based on an old knowledge base.

The output is plain JSON: review it and edit any answer by hand if needed.

Usage:  python scripts/pregenerate_answers.py [--force]
"""
from __future__ import annotations

import json
import os
import sys
import tomllib
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from logic.chatbot import ANSWERS_PATH, build_context, knowledge_hash, query_gemini  # noqa: E402


def api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY", "")
    secrets = BASE_DIR / ".streamlit" / "secrets.toml"
    if not key and secrets.exists():
        key = tomllib.loads(secrets.read_text(encoding="utf-8")).get("GOOGLE_API_KEY", "")
    if not key:
        sys.exit("GOOGLE_API_KEY not found (environment or .streamlit/secrets.toml)")
    return key


def main() -> None:
    os.environ["GOOGLE_API_KEY"] = api_key()
    force = "--force" in sys.argv
    kb_hash = knowledge_hash()
    languages = json.loads((BASE_DIR / "config" / "languages.json").read_text(encoding="utf-8"))

    old = json.loads(ANSWERS_PATH.read_text(encoding="utf-8")) if ANSWERS_PATH.exists() else {}
    reuse = old.get("answers", {}) if old.get("kb_hash") == kb_hash and not force else {}
    answers: dict[str, dict] = {}
    calls = 0

    for lang in languages:
        cfg = json.loads((BASE_DIR / "locales" / f"{lang}.json").read_text(encoding="utf-8"))["chatbot_config"]
        questions = [s["msg"] for s in cfg.get("suggestions", []) + cfg.get("more_suggestions", [])]
        answers[lang] = {}
        context = build_context(lang)
        for question in questions:
            if question in reuse.get(lang, {}):
                answers[lang][question] = reuse[lang][question]
                continue
            result = query_gemini(question, context, lang=lang)
            calls += 1
            if not result or not result["answer"]:
                sys.exit(f"Gemini failed for [{lang}] {question!r}; nothing written")
            answers[lang][question] = {"answer": result["answer"], "topic": result["topic"]}
            print(f"[{lang}] {question}")

    ANSWERS_PATH.write_text(json.dumps(
        {"kb_hash": kb_hash, "generated": date.today().isoformat(), "model": "gemini-2.5-flash", "answers": answers},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(len(v) for v in answers.values())
    print(f"{total} answers in {ANSWERS_PATH.relative_to(BASE_DIR)} ({calls} new Gemini calls)")


if __name__ == "__main__":
    main()
