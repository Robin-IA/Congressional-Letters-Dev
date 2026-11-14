"""The "Last updated" line at the foot of every explorer and the home page.

The pages are rebuilt every time new letters, text or thumbnails arrive
(build/auto_publish.sh), so a reader needs to know how fresh the numbers
are (asked for by Robin on 14 November 2026). The line is written into the
HTML at build time, not by script, so it shows even if the page's script
fails, and it gives the time with its zone: builds run on the Mac, whose
local time is what the zone names.

Each page template carries one ``<!-- last-updated -->`` marker in its
footer; ``stamp()`` replaces it.
"""
from __future__ import annotations

from datetime import datetime

MARKER = "<!-- last-updated -->"


def line(when: datetime | None = None) -> str:
    """<p class="updated">Last updated <time …>November 14, 2026, 11:17 AM PST</time></p>"""
    when = (when or datetime.now()).astimezone()
    hour = when.strftime("%I").lstrip("0")
    shown = f"{when:%B} {when.day}, {when.year}, {hour}:{when:%M %p %Z}"
    return (f'<p class="updated">Last updated '
            f'<time datetime="{when.isoformat(timespec="minutes")}">{shown}</time>.</p>')


def stamp(html: str, when: datetime | None = None, label: str = "page") -> str:
    """The page with its marker replaced; exits if the template lost it."""
    if html.count(MARKER) != 1:
        raise SystemExit(f"{label}: expected one {MARKER}, found {html.count(MARKER)}")
    return html.replace(MARKER, line(when))
