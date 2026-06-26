"""The bundled public-domain **sample book** -- so Read mode works out of the box
on a fresh install, with nothing to download.

Kenneth Grahame's *The Wind in the Willows* (1908), long in the public domain. The
plain text lives beside this module under ``data/``; :func:`breathsim.books.seed_sample_if_fresh`
segments + saves it into the local library once, on first run. Only the
public-domain text is shipped -- the Project Gutenberg header/footer and trademark
have been stripped -- so it carries no usage restriction.
"""
from __future__ import annotations

import os

TITLE = "The Wind in the Willows"
AUTHOR = "Kenneth Grahame"
_PATH = os.path.join(os.path.dirname(__file__), "data", "wind_in_the_willows.txt")


def text():
    """The raw sample-book text, or ``""`` if the bundled asset is missing."""
    try:
        with open(_PATH, encoding="ascii") as fh:
            return fh.read()
    except OSError:
        return ""
