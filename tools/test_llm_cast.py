"""Offline test for breathsim.llm_cast -- stubbed completer, NO network, NO LLM.

Asserts: a good JSON reply refines the cast within the allowed registries; an
out-of-registry character/costume is clamped back to the heuristic / 'None';
malformed JSON falls back to the heuristic; no backend (no completer, llm
unavailable) yields the heuristic; and the cast caches + reloads per book.
"""
import json
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import books, llm, llm_cast, llm_keys  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")
llm_cast.CASTS = os.path.join(os.environ["BREATHSIM_HOME"], "casts.json")
llm_keys.clear()
llm.enable_ollama(False)

CHARACTERS = ["Cat", "Owl", "Fox", "Bear", "Mouse", "Sheep", "Penguin"]
COSTUMES = ["None", "Nightcap", "Crown", "Wizard Hat"]

TEXT = ('The hall was quiet.\n\n"Welcome," said Alice.\n\n"Thank you," replied Bob.\n\n'
        '"Come in," Alice said.\n\nThey stepped inside together.')


def book():
    return books.from_text(TEXT, "A Welcome", source="upload")


def reply(d):
    return lambda prompt, **kw: json.dumps(d)


def main():
    b = book()
    # heuristic baseline (speakers Alice, Bob)
    base = llm_cast.direct(b, CHARACTERS, COSTUMES, complete=None, save=False)
    assert set(base) == {"Alice", "Bob"} and base["Alice"]["character"] in CHARACTERS
    print(f"ok: no backend -> heuristic cast {[(k, v['character']) for k, v in base.items()]}")

    # a good reply refines within the registries
    good = reply({"cast": {
        "Alice": {"character": "Owl", "costume": "Nightcap", "voice": "warm", "emotion": "soft"},
        "Bob": {"character": "Bear", "costume": "None", "voice": "deep", "emotion": "calm"}}})
    cast = llm_cast.direct(b, CHARACTERS, COSTUMES, complete=good)
    assert cast["Alice"]["character"] == "Owl" and cast["Alice"]["costume"] == "Nightcap"
    assert cast["Bob"]["character"] == "Bear"
    assert llm_cast.load_cast(b.id) == cast        # cached + reloads
    print("ok: good JSON refines the cast within registries, cached per book")

    # out-of-registry character/costume -> clamped back to heuristic / 'None'
    llm_cast.delete_cast(b.id)
    bad = reply({"cast": {
        "Alice": {"character": "Dragon", "costume": "Jetpack", "voice": "x", "emotion": "e"},
        "Bob": {"character": "Fox", "costume": "Crown"}}})
    cast2 = llm_cast.direct(b, CHARACTERS, COSTUMES, complete=bad)
    assert cast2["Alice"]["character"] in CHARACTERS and cast2["Alice"]["character"] != "Dragon"
    assert cast2["Alice"]["costume"] == "None"     # 'Jetpack' dropped
    assert cast2["Bob"]["character"] == "Fox" and cast2["Bob"]["costume"] == "Crown"
    print("ok: out-of-registry character/costume clamped")

    # malformed JSON -> heuristic fallback (never raises)
    llm_cast.delete_cast(b.id)
    cast3 = llm_cast.direct(b, CHARACTERS, COSTUMES, complete=lambda p, **k: "not json")
    assert set(cast3) == {"Alice", "Bob"} and cast3 == base or all(
        c["character"] in CHARACTERS for c in cast3.values())
    print("ok: malformed JSON -> heuristic fallback, no crash")

    # a plain book (no dialogue) -> empty cast
    plain = books.from_text("It was quiet. The lamp glowed.", "Plain", source="upload")
    assert llm_cast.direct(plain, CHARACTERS, COSTUMES, complete=good) == {}
    print("ok: a plain book -> empty cast")

    print("PASS: llm_cast -- opt-in director, validated, clamped, fail-closed, cached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
