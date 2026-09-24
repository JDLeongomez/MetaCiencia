#!/usr/bin/env python3
"""Genera divulgacion/_youtube-videos.qmd a partir del feed RSS público del
canal de YouTube de MetaCiencia. Se ejecuta como paso pre-render de Quarto
en cada build, así la grilla de videos se mantiene al día sin intervención
manual. Si el feed no está disponible (sin red, canal caído, etc.) se
escribe un mensaje de respaldo en vez de romper el build.
"""
import html
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CHANNEL_ID = "UCOV1LrVB71T7JnRGHVmx0Ww"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
MAX_VIDEOS = 6
OUTPUT = Path(__file__).resolve().parent.parent / "divulgacion" / "_youtube-videos.qmd"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}

FALLBACK = (
    '::: {.callout-note appearance="simple"}\n'
    "Aún no hay videos publicados en nuestro canal de YouTube. ¡Vuelve pronto!\n"
    ":::\n"
)


def fetch_videos():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    videos = []
    for entry in root.findall("atom:entry", NS)[:MAX_VIDEOS]:
        video_id = entry.findtext("yt:videoId", default=None, namespaces=NS)
        title = entry.findtext("atom:title", default=None, namespaces=NS)
        if video_id and title:
            videos.append((video_id, title))
    return videos


def render(videos):
    if not videos:
        return FALLBACK

    cards = []
    for video_id, title in videos:
        safe_title = html.escape(title, quote=True)
        cards.append(
            '  <div class="g-col-12 g-col-md-4">\n'
            '    <div class="ratio ratio-16x9">\n'
            f'      <iframe src="https://www.youtube.com/embed/{video_id}" '
            f'title="{safe_title}" allowfullscreen loading="lazy" '
            'referrerpolicy="strict-origin-when-cross-origin"></iframe>\n'
            "    </div>\n"
            f'    <p class="video-title">{safe_title}</p>\n'
            "  </div>"
        )

    body = "\n".join(cards)
    return f'```{{=html}}\n<div class="grid">\n{body}\n</div>\n```\n'


def main():
    try:
        videos = fetch_videos()
        content = render(videos)
    except Exception as exc:
        print(f"[fetch_youtube_videos] No se pudo obtener el feed de YouTube: {exc}", file=sys.stderr)
        content = FALLBACK

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
