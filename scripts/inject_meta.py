"""Insert SEO / social-preview tags into the index.html that Streamlit serves.

Streamlit builds the page in the browser, so tags added with st.markdown are
invisible to link-preview crawlers (LinkedIn, WhatsApp, Slack, Google). Those
crawlers only read the static index.html shipped inside the streamlit package,
so this script edits that file. It is idempotent: the block between the
markers is replaced on every run. Run it after every `pip install` (the deploy
workflow does), because reinstalling Streamlit restores the original file.

Usage:  python scripts/inject_meta.py [path/to/index.html]
"""
import html
import json
import re
import sys
from pathlib import Path

SITE_URL = "https://asansal.com"
OG_IMAGE = f"{SITE_URL}/app/static/og-image.png"   # served from ./static (enableStaticServing)
FAVICON = "./app/static/favicon.png"
START, END = "<!-- asansal-meta:start -->", "<!-- asansal-meta:end -->"

BASE_DIR = Path(__file__).resolve().parent.parent


def streamlit_index() -> Path:
    import streamlit
    return Path(streamlit.__file__).parent / "static" / "index.html"


def build_block() -> str:
    seo = json.loads((BASE_DIR / "locales" / "en.json").read_text(encoding="utf-8"))["seo"]
    title = html.escape(seo["meta_title"], quote=True)
    desc = html.escape(seo["meta_description"], quote=True)
    keywords = html.escape(", ".join(seo.get("keywords", [])), quote=True)
    alt = html.escape("Alejandro Sánchez, AI Engineer & Data Scientist", quote=True)
    tags = [
        f'<meta name="description" content="{desc}" />',
        f'<meta name="keywords" content="{keywords}" />',
        f'<link rel="canonical" href="{SITE_URL}/" />',
        f'<link rel="apple-touch-icon" href="{FAVICON}" />',
        '<meta property="og:type" content="website" />',
        f'<meta property="og:url" content="{SITE_URL}/" />',
        f'<meta property="og:title" content="{title}" />',
        f'<meta property="og:description" content="{desc}" />',
        f'<meta property="og:image" content="{OG_IMAGE}" />',
        '<meta property="og:image:width" content="1200" />',
        '<meta property="og:image:height" content="630" />',
        f'<meta property="og:image:alt" content="{alt}" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{title}" />',
        f'<meta name="twitter:description" content="{desc}" />',
        f'<meta name="twitter:image" content="{OG_IMAGE}" />',
    ]
    return START + "\n    " + "\n    ".join(tags) + "\n    " + END, title


def main() -> None:
    index = Path(sys.argv[1]) if len(sys.argv) > 1 else streamlit_index()
    page = index.read_text(encoding="utf-8")
    block, title = build_block()

    page = re.sub(re.escape(START) + r".*?" + re.escape(END), "", page, flags=re.S)
    page = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", page, count=1, flags=re.S)
    page = re.sub(r'<link rel="shortcut icon" href="[^"]*"\s*/>', f'<link rel="shortcut icon" href="{FAVICON}" />', page, count=1)
    page = page.replace("</head>", f"    {block}\n  </head>", 1)

    index.write_text(page, encoding="utf-8")
    print(f"Meta tags written to {index}")


if __name__ == "__main__":
    main()
