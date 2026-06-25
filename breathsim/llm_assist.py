"""A quiet in-app helper: plain language -> a WHITELIST of bounded app actions.

The user asks for help ("I'm anxious, set me up for sleep"); the assistant calls
the LLM with a small, fixed set of **tools** and returns a normalized result: a
short calm reply plus a list of **validated** actions for the app to apply. It
never runs free-form code. Every tool call the model returns is checked against
the real registries (mode / pattern / voice / ambience / story names) and numeric
ranges; anything unknown or out of range is **refused**, never executed.

This module is GUI-free and stateless: it returns *intents* (``{action, args}``)
that the Qt layer maps to its own methods (a later round wires that up and may
voice the reply through the face). Gated on :func:`breathsim.llm.available`; with
no LLM the helper is simply absent. Calm and brief by design; no medical advice.
"""
from __future__ import annotations

from . import llm

SYSTEM = (
    "You are Vesper's quiet bedtime helper. Be calm, brief and kind, in one or two "
    "short sentences. Help the user set up the app using ONLY the provided tools; "
    "never invent actions or names. Use the exact preset/voice/story names the user "
    "mentions. Give no medical advice. If a request is outside these tools, gently "
    "say you cannot do that and suggest what you can.")

WHITELIST = {"set_mode", "set_pattern", "set_ambience", "set_voice", "play",
             "pause", "set_volume", "start_story", "set_sleep_timer"}


def tools():
    """Anthropic-style tool schemas for the whitelisted app actions."""
    def obj(props, req=()):
        return {"type": "object", "properties": props, "required": list(req)}
    name = {"name": {"type": "string"}}
    return [
        {"name": "set_mode", "description": "Switch the app mode (Meditate, "
         "Breathwork, Chant, Sing, Relax, Sleep).",
         "input_schema": obj({"mode": {"type": "string"}}, ["mode"])},
        {"name": "set_pattern", "description": "Choose a breathing pattern by its "
         "exact preset name.", "input_schema": obj(name, ["name"])},
        {"name": "set_ambience", "description": "Choose a background nature sound "
         "by exact name.", "input_schema": obj(name, ["name"])},
        {"name": "set_voice", "description": "Choose a breath voice by exact name.",
         "input_schema": obj(name, ["name"])},
        {"name": "play", "description": "Start or resume the session.",
         "input_schema": obj({})},
        {"name": "pause", "description": "Pause the session.", "input_schema": obj({})},
        {"name": "set_volume", "description": "Set the master volume, 0.0 to 1.0.",
         "input_schema": obj({"level": {"type": "number"}}, ["level"])},
        {"name": "start_story", "description": "Begin a bedtime story or lecture by "
         "its exact name.", "input_schema": obj(name, ["name"])},
        {"name": "set_sleep_timer", "description": "Auto-stop after N minutes.",
         "input_schema": obj({"minutes": {"type": "integer"}}, ["minutes"])},
    ]


def _validate(name, args):
    """Return validated/clamped args for a whitelisted action, or None to refuse."""
    a = args if isinstance(args, dict) else {}
    if name == "set_mode":
        from . import modes
        m = str(a.get("mode", ""))
        return {"mode": m} if m in modes.names() else None
    if name == "set_pattern":
        from .patterns import preset_by_name
        n = str(a.get("name", ""))
        return {"name": n} if preset_by_name(n) is not None else None
    if name in ("set_ambience", "set_voice"):
        from . import voices
        n = str(a.get("name", ""))
        return {"name": n} if n in set(voices.names()) else None
    if name in ("play", "pause"):
        return {}
    if name == "set_volume":
        try:
            lvl = float(a.get("level"))
        except Exception:
            return None
        return {"level": max(0.0, min(1.0, lvl))}
    if name == "start_story":
        from . import stories
        n = str(a.get("name", ""))
        opts = (set(stories.scene_names()) | set(stories.extra_names())
                | set(stories.lecture_names()))
        return {"name": n} if n in opts else None
    if name == "set_sleep_timer":
        try:
            mins = int(float(a.get("minutes")))
        except Exception:
            return None
        return {"minutes": max(1, min(180, mins))}
    return None


def available():
    return llm.available()


def ask(message, history=None, chat=None):
    """Answer *message* and return ``{reply, actions, refused}``.

    ``actions`` is a list of validated ``{action, args}`` intents the app may
    apply; ``refused`` lists any tool calls that were unknown or invalid (never
    applied). Pass *chat* (a stub) for offline tests; else the active LLM is used
    and a missing backend raises ``LLMUnavailable``."""
    fn = chat or (llm.chat if llm.available() else None)
    if fn is None:
        raise llm.LLMUnavailable(
            "The helper needs an LLM (set an API key or enable Ollama).")
    msgs = list(history or []) + [{"role": "user", "content": str(message)}]
    out = fn(msgs, system=SYSTEM, tools=tools())
    reply = str((out or {}).get("text") or "").strip()
    actions, refused = [], []
    for c in (out or {}).get("tool_calls") or []:
        nm = c.get("name")
        if nm not in WHITELIST:
            refused.append(str(nm))
            continue
        va = _validate(nm, c.get("input"))
        if va is None:
            refused.append(str(nm))
            continue
        actions.append({"action": nm, "args": va})
    return {"reply": reply, "actions": actions, "refused": refused}
