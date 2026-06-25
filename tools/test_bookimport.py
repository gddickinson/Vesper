"""Offline test for breathsim.bookimport -- NO Qt, NO network.

Builds a tiny in-memory .epub (mimetype + container.xml + content.opf + one XHTML
chapter) and .txt blobs, runs the importer, and asserts a Book is produced + saved
with the right title/author + sentences, that path dispatch works, that odd
encodings decode, and that a zip-bomb-ish archive (too many entries) and junk are
refused -- all fail-closed.
"""
import io
import os
import sys
import tempfile
import zipfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import bookimport, books  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")

CONTAINER = ('<?xml version="1.0"?><container version="1.0" '
             'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
             '<rootfile full-path="OEBPS/content.opf" '
             'media-type="application/oebps-package+xml"/></rootfiles></container>')
OPF = ('<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" '
       'version="2.0" unique-identifier="id"><metadata '
       'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Test Novel</dc:title>'
       '<dc:creator>A. Writer</dc:creator></metadata><manifest>'
       '<item id="c1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>'
       '</manifest><spine><itemref idref="c1"/></spine></package>')
CHAP = ('<html><body><h1>Chapter One</h1>'
        '<p>It was a calm night. The lamp glowed softly.</p>'
        '<p>Outside, the snow fell without a sound.</p></body></html>')


def make_epub():
    buf = io.BytesIO()
    z = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)
    z.writestr("mimetype", "application/epub+zip")
    z.writestr("META-INF/container.xml", CONTAINER)
    z.writestr("OEBPS/content.opf", OPF)
    z.writestr("OEBPS/chapter1.xhtml", CHAP)
    z.close()
    return buf.getvalue()


def main():
    # epub from bytes -> title/author from OPF, chapter segmented + ASCII
    bid = bookimport.import_epub(make_epub())
    book = books.load(bid)
    assert book and book.title == "Test Novel" and book.author == "A. Writer"
    flat = " ".join(book.sentences())
    assert "It was a calm night." in book.sentences()
    assert "snow fell without a sound" in flat and "Chapter One" in flat
    assert book.sentence_count() >= 4 and all(s.isascii() for s in book.sentences())
    print(f"ok: epub imported '{book.title}' / {book.author} ({book.sentence_count()} sentences)")

    # txt from bytes
    tid = bookimport.import_txt(b"Hello there. This is mine.\n\nA second line here.",
                                title="My Notes")
    tb = books.load(tid)
    assert tb and tb.title == "My Notes" and tb.sentence_count() >= 3
    print("ok: txt imported with explicit title")

    # odd encoding decodes (latin-1 accent -> folded to ASCII), never crashes
    lid = bookimport.import_txt(b"Caf\xe9 at dawn. It was good.\n", title="Latin")
    lb = books.load(lid)
    assert lb and all(s.isascii() for s in lb.sentences())
    print("ok: latin-1 bytes decode + fold to ASCII")

    # path dispatch by extension
    d = tempfile.mkdtemp()
    ep = os.path.join(d, "novel.epub")
    with open(ep, "wb") as fh:
        fh.write(make_epub())
    tp = os.path.join(d, "diary.txt")
    with open(tp, "w") as fh:
        fh.write("Monday. I walked by the sea.\n\nIt was quiet and grey.")
    assert bookimport.import_file(ep)
    dt = books.load(bookimport.import_file(tp))
    assert dt and dt.title == "diary"          # title from filename
    print("ok: import_file dispatches .epub vs .txt, title from filename")

    # zip-bomb-ish: too many entries -> refused
    buf = io.BytesIO()
    z = zipfile.ZipFile(buf, "w")
    for i in range(bookimport.MAX_ENTRIES + 1):
        z.writestr(f"f{i}.txt", "x")
    z.close()
    assert bookimport.import_epub(buf.getvalue()) is None
    print("ok: archive with too many entries refused")

    # junk / empty -> None, never raises
    assert bookimport.import_epub(b"not a zip at all") is None
    assert bookimport.import_txt(b"") is None
    print("ok: junk + empty refused, no crash")

    print("PASS: bookimport -- txt + epub, untrusted-safe, zip-bomb-guarded, offline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
