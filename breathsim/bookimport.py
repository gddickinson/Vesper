"""Import the user's OWN books from local files -- .txt and .epub. No network.

Everything a file contains is treated as **untrusted data**: it is read with hard
size caps, decoded defensively, and only ever parsed into a local
:class:`breathsim.books.Book` (boilerplate-stripped, ASCII, segmented) -- never
executed. EPUB is a ZIP of XHTML, so it is opened with **zip-bomb guards** (a
per-entry read cap, a total-read cap and an entry-count cap; non-XHTML entries
ignored). Every path catches its own errors and returns ``None`` rather than
raising, so a bad file can never crash the app. Imported books stay on this
device -- nothing is uploaded anywhere.

Pure + offline-testable: :func:`import_txt` / :func:`import_epub` /
:func:`import_file` take bytes OR a path; the GUI hook lives in
``vesper/booklib.py``.
"""
from __future__ import annotations

import html as _html
import io
import os
import re
import zipfile

from . import books, booktext

MAX_TXT_BYTES = 12_000_000        # cap a plain-text file at ~12 MB
MAX_ENTRY_BYTES = 10_000_000      # cap one decompressed zip entry at ~10 MB
MAX_TOTAL_BYTES = 40_000_000      # cap total decompressed text pulled from a zip
MAX_ENTRIES = 4000                # refuse archives with absurd entry counts


# --- shared helpers --------------------------------------------------------

def _read_bytes(data, cap):
    """Bytes from a bytes object or a path, hard-capped. None on any error."""
    try:
        if isinstance(data, (bytes, bytearray)):
            return bytes(data[:cap])
        with open(data, "rb") as fh:
            return fh.read(cap + 1)[:cap]
    except OSError:
        return None


def _decode(raw):
    """Defensive decode: UTF-8, then Latin-1, then UTF-8 with replacement."""
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, AttributeError):
            continue
    return raw.decode("utf-8", "replace")


def _title_from_path(data):
    if isinstance(data, str):
        return os.path.splitext(os.path.basename(data))[0].replace("_", " ").strip()
    return ""


# --- plain text ------------------------------------------------------------

def import_txt(data, title=None, author=None):
    """Import a .txt (bytes or path) into the library. Returns the book id or None."""
    raw = _read_bytes(data, MAX_TXT_BYTES)
    if not raw:
        return None
    text = _decode(raw)
    book = books.from_text(text, (title or _title_from_path(data) or "Imported Book"),
                           author or "", source="upload")
    return books.save(book)


# --- epub ------------------------------------------------------------------

def _localname(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else tag


def _strip_html(s):
    """Turn one XHTML chapter into plain text with paragraph breaks preserved."""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<(/p|/div|/h[1-6]|/li|br\s*/?|/tr|/blockquote)\s*>", "\n\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)          # drop all remaining tags
    return _html.unescape(s)


def _zip_read(zf, name):
    """Read one entry, decompressed-size-capped (bounds memory vs. a zip bomb)."""
    try:
        with zf.open(name) as fh:
            return fh.read(MAX_ENTRY_BYTES + 1)[:MAX_ENTRY_BYTES]
    except (KeyError, OSError, zipfile.BadZipFile):
        return b""


def _opf_path(zf):
    """The OPF rootfile path from META-INF/container.xml (best-effort)."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(_zip_read(zf, "META-INF/container.xml"))
        for el in root.iter():
            if _localname(el.tag) == "rootfile" and el.get("full-path"):
                return el.get("full-path")
    except Exception:
        pass
    return None


def _parse_opf(zf, opf_path):
    """Return (title, author, [chapter_hrefs]) from the OPF, reading-order."""
    import xml.etree.ElementTree as ET
    title, author, manifest, spine = "", "", {}, []
    try:
        root = ET.fromstring(_zip_read(zf, opf_path))
    except Exception:
        return title, author, []
    for el in root.iter():
        tag = _localname(el.tag)
        if tag == "title" and not title and (el.text or "").strip():
            title = el.text.strip()
        elif tag == "creator" and not author and (el.text or "").strip():
            author = el.text.strip()
        elif tag == "item":
            mid, href, mtype = el.get("id"), el.get("href"), el.get("media-type", "")
            if mid and href:
                manifest[mid] = (href, mtype)
        elif tag == "itemref" and el.get("idref"):
            spine.append(el.get("idref"))
    base = opf_path.rsplit("/", 1)[0] if "/" in opf_path else ""
    hrefs = []
    for idref in spine:
        item = manifest.get(idref)
        if not item or "xml" not in item[1] and "html" not in item[1]:
            continue
        href = item[0].split("#", 1)[0]
        hrefs.append((base + "/" + href) if base else href)
    return title, author, hrefs


def import_epub(data, title=None, author=None):
    """Import an .epub (bytes or path) into the library. Returns the id or None.
    Zip-bomb-guarded + fail-closed."""
    raw = _read_bytes(data, MAX_TOTAL_BYTES + 1)
    if not raw:
        return None
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile, OSError):
        return None
    try:
        if len(zf.namelist()) > MAX_ENTRIES:
            return None
        opf = _opf_path(zf)
        meta_title, meta_author, hrefs = _parse_opf(zf, opf) if opf else ("", "", [])
        names = set(zf.namelist())
        if not hrefs:                              # fallback: every xhtml in name order
            hrefs = [n for n in zf.namelist()
                     if n.lower().endswith((".xhtml", ".html", ".htm"))]
        parts, total = [], 0
        for href in hrefs:
            if href not in names:
                continue
            chunk = _strip_html(_decode(_zip_read(zf, href)))
            total += len(chunk)
            if total > MAX_TOTAL_BYTES:            # stop pulling at the total cap
                break
            parts.append(chunk)
    finally:
        zf.close()
    text = "\n\n".join(parts)
    if not booktext.to_ascii(text).strip():
        return None
    book = books.from_text(text, (title or meta_title or _title_from_path(data)
                                  or "Imported Book"),
                           author or meta_author or "", source="upload")
    return books.save(book)


def import_file(path, title=None, author=None):
    """Dispatch by extension. Returns the saved book id or None."""
    if isinstance(path, str) and path.lower().endswith(".epub"):
        return import_epub(path, title, author)
    return import_txt(path, title, author)
