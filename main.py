#!/usr/bin/env python3
"""NetScope – Modern Linux Internet Usage Monitor."""

from pathlib import Path

import webview

from backend.app import Api

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"


def main(debug: bool = False) -> None:
    if not INDEX_HTML.exists():
        raise FileNotFoundError(f"Frontend not found at: {INDEX_HTML}")

    api = Api()

    window = webview.create_window(
        title="NetScope",
        url=str(INDEX_HTML),
        js_api=api,
        width=1280,
        height=800,
        min_size=(960, 640),
        background_color="#0c0e12",
        text_select=True,
    )

    webview.start(
        debug=debug,
        # private_mode=False allows localStorage if needed later
    )


if __name__ == "__main__":
    import sys

    debug = "--debug" in sys.argv or "-d" in sys.argv
    main(debug=debug)
