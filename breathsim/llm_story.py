"""Generate a sleep story with the optional LLM, validate it, save it.

When :func:`breathsim.llm.available` is true, :func:`generate` asks the model for
a soothing bedtime story in the lecture **7x12** schema (7 sections of 12
sentences), then treats the reply as **untrusted**: it parses the JSON, runs the
same lint the authored lectures must pass (7x12, ASCII, sentences end in . ? !,
a fact-free settling section 1, a sleep-closing final section), and **repairs**
by re-prompting with the specific errors, up to a few times. A story that never
validates is rejected (``None``).

Validated stories register straight into the lecture library under the **"AI
Stories"** category with an **"AI: "** name prefix (clearly labelled AI-written),
so they narrate through the ordinary storyteller and can be **saved** to
``~/.breathsim`` via :mod:`breathsim.store` (loaded again next run). AI stories
are framed as *atmospheric / imaginative* -- they make none of the authored
lectures' factual-accuracy claims. With no LLM the whole feature is simply absent
and the app is unaffected.
"""
from __future__ import annotations

import json
import re

from . import llm, store

PREFIX = "AI: "
CATEGORY = "AI Stories"
DEFAULT_AMBIENCE = "Soft Rainstorm"
_AMBIENCES = ["Soft Rainstorm", "Gentle Rain", "Ocean Waves", "Wind in Pines",
              "Night Crickets", "Singing Bowl", "Mountain Stream", "Forest Wind",
              "Whale Song", "Brown Noise"]


def available():
    return llm.available()


# --- validation (untrusted model output) -----------------------------------

def validate(sections):
    """Return a list of human-readable problems (empty == valid 7x12 story)."""
    errs = []
    if not isinstance(sections, list) or len(sections) != 7:
        return ["the story must have exactly 7 sections"]
    for i, sec in enumerate(sections):
        if not isinstance(sec, list) or len(sec) != 12:
            errs.append(f"section {i + 1} must have exactly 12 sentences")
            continue
        for j, s in enumerate(sec):
            if not isinstance(s, str) or not s.strip():
                errs.append(f"section {i + 1} sentence {j + 1} is empty")
                continue
            if not s.rstrip().endswith((".", "?", "!")):
                errs.append(f"section {i + 1} sentence {j + 1} must end with . ? or !")
            try:
                s.encode("ascii")
            except UnicodeEncodeError:
                errs.append(f"section {i + 1} sentence {j + 1} has non-ASCII characters")
    if isinstance(sections[0], list):
        for j, s in enumerate(sections[0]):
            if isinstance(s, str) and any(c.isdigit() for c in s):
                errs.append("section 1 must be a fact-free settling-in (no numbers)")
                break
    if isinstance(sections[6], list):
        tail = " ".join(x for x in sections[6] if isinstance(x, str)).lower()
        if not any(w in tail for w in ("sleep", "rest", "drift", "dream", "asleep")):
            errs.append("the final section must ease all the way into sleep")
    return errs


# --- prompt + parse --------------------------------------------------------

def _prompt(topic, errors=None):
    p = (
        "Write a soothing, original bedtime sleep-story about " + str(topic) + ".\n"
        "Return ONLY a JSON object, nothing else, of this exact shape:\n"
        '{"title": "...", "ambience": "...", "sections": [[12 sentences], ... 7 lists ...]}\n'
        "Rules: exactly 7 sections, each exactly 12 sentences. Second person, present "
        "tense ('you'). ASCII only (straight quotes, no accents or dashes). Each "
        "sentence ends with . ? or !. Section 1 is a gentle settling-in with NO facts "
        "and NO numbers. Every section eases toward sleep; the final section drifts "
        "fully into sleep. Keep it calm, gentle, atmospheric and imaginative, with no "
        "medical claims. 'ambience' must be one of: " + ", ".join(_AMBIENCES) + ".")
    if errors:
        p = ("Your previous reply had these problems: " + "; ".join(errors)
             + ". Fix them and return corrected JSON only.\n\n" + p)
    return p


def _parse(text):
    if not isinstance(text, str):
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _resolve_ambience(amb):
    try:
        from . import voices
        if amb in set(voices.names()):
            return amb
    except Exception:
        pass
    return DEFAULT_AMBIENCE


def generate(topic, model=None, max_repairs=2, complete=None):
    """Generate + validate (+ repair) one story dict, or None if it never passes.
    Pass *complete* (a ``fn(prompt, **opts) -> str``) to test offline; otherwise
    the active LLM is used and a missing backend raises ``LLMUnavailable``."""
    comp = complete or (llm.complete if llm.available() else None)
    if comp is None:
        raise llm.LLMUnavailable(
            "Story generation needs an LLM (set an API key or enable Ollama).")
    errors = None
    for _ in range(int(max_repairs) + 1):
        raw = comp(_prompt(topic, errors), max_tokens=4000)
        data = _parse(raw)
        if data is None:
            errors = ["the reply was not valid JSON"]
            continue
        sections = data.get("sections")
        errs = validate(sections)
        if not errs:
            title = (str(data.get("title") or topic).strip() or str(topic))[:60]
            return {"name": PREFIX + title,
                    "ambience": _resolve_ambience(str(data.get("ambience") or "")),
                    "sections": sections, "ai": True, "topic": str(topic)}
        errors = errs[:6]
    return None


# --- registry + persistence ------------------------------------------------

def register(story):
    """Add a story dict into the live lecture library (in-memory) so it narrates
    immediately. Re-validates first; returns the registered name or None."""
    if not isinstance(story, dict) or validate(story.get("sections")):
        return None
    from . import lectures
    name = story.get("name") or (PREFIX + "Untitled")
    if not name.startswith(PREFIX):
        name = PREFIX + name
    amb = _resolve_ambience(str(story.get("ambience") or ""))
    lectures.LECTURES[name] = lectures.Lecture(name, amb, story["sections"], CATEGORY)
    return name


def save(story):
    """Register *story* and persist it to the library (~/.breathsim)."""
    name = register(story)
    if name:
        store.save_ai_story({"name": name, "ambience": story.get("ambience"),
                             "sections": story["sections"]})
    return name


def saved():
    return store.ai_stories_list()


def delete(name):
    store.delete_ai_story(name)
    from . import lectures
    lectures.LECTURES.pop(name, None)


def register_saved():
    """Load every saved AI story into the live lecture library (called at start)."""
    for d in store.ai_stories_list():
        try:
            register(d)
        except Exception:
            pass
