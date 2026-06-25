"""Sleep "Generate a bedtime story" action -- optional, opt-in, off the UI thread.

Available ONLY when an LLM backend is configured (a key set, or Ollama opted into,
via Help -> AI Assistant). The model reply is treated as **untrusted** by
:mod:`breathsim.llm_story` (parsed, linted to the lecture 7x12 schema, repaired,
or rejected). A valid story registers into the live lecture library and narrates
like any other, clearly labelled ``AI:``; the user is then asked to **keep** it
(persist to ``~/.breathsim``) or let it drift away. Generation runs on a daemon
thread and is delivered back via a queued Qt signal, so the **UI never blocks on
the network**. With no backend the whole feature is hidden/disabled and the app
is unaffected.

:func:`can_generate` / :func:`make_story` are Qt-free and unit-tested offline;
:func:`generate_dialog` is the thin Qt orchestration.
"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox

from breathsim import llm_story

# Gentle, plotless prompts to seed the topic box (the user can type their own).
TOPICS = [
    "a quiet snowfall over a sleeping village",
    "a slow boat drifting down a warm river",
    "a small house at the edge of a still forest",
    "the last lamp glowing in a harbour at night",
    "a walled garden settling into dusk",
    "a cat dreaming by a low hearth",
    "drifting among slow and distant stars",
    "a library long after closing time",
    "a meadow under a low summer moon",
    "rain falling softly on a tin roof in the hills",
]


def can_generate():
    """True only when an LLM backend is configured (a key, or Ollama opted in)."""
    return llm_story.available()


def make_story(topic, complete=None):
    """Generate + register ONE AI story into the live lecture library. Off-thread
    safe and Qt-free. Returns ``(name, story)`` or ``(None, None)`` if the model's
    reply never validates. Pass *complete* (a ``fn(prompt, **opts) -> str``) to
    test offline; otherwise the active backend is used."""
    story = llm_story.generate(topic, complete=complete)
    if not story:
        return None, None
    return llm_story.register(story), story


class _Worker(QObject):
    """Runs generation on a daemon thread, emits the result on the main thread."""
    done = Signal(object)        # (name, story) | (None, None) | Exception

    def run(self, topic):
        def work():
            try:
                self.done.emit(make_story(topic))
            except Exception as e:          # surface a calm message; never leak
                self.done.emit(e)
        threading.Thread(target=work, daemon=True).start()


def generate_dialog(win):
    """Ask for a topic, generate off-thread, then offer keep/discard. With no
    backend, points the user (gently) at the AI Assistant settings instead."""
    if not can_generate():
        QMessageBox.information(
            win, "AI Assistant",
            "No AI backend is set up yet.\n\nOpen Help -> AI Assistant (optional) "
            "to add your own API key or enable a local model. Vesper works fully "
            "without it.")
        return
    import random
    suggestion = random.choice(TOPICS)
    topic, ok = QInputDialog.getText(
        win, "Generate a bedtime story",
        "What should tonight's story be about?", text=suggestion)
    if not ok:
        return
    topic = (topic or "").strip() or suggestion
    win.status.showMessage(f"Dreaming up a story about {topic}…", 0)

    worker = _Worker()
    win._story_gen_worker = worker          # keep a ref so it isn't GC'd mid-run

    def on_done(result):
        win._story_gen_worker = None
        if isinstance(result, Exception):
            win.status.showMessage("Could not reach the AI just now.", 5000)
            return
        name, story = result
        if not name:
            win.status.showMessage(
                "The story didn't come out right -- please try again.", 6000)
            return
        win.status.clearMessage()
        _offer_keep(win, name, story)

    worker.done.connect(on_done, Qt.ConnectionType.QueuedConnection)
    worker.run(topic)


def _offer_keep(win, name, story):
    """Arm the freshly made story as tonight's Sleep story, then ask keep/discard."""
    if win.current_mode != "Sleep":
        win.apply_mode("Sleep")
    win.set_story(name)                     # arms _story_scene + ambience
    win._ensure_running()                   # start the Sleep session + narration
    win.panel.build_workspace(win.current_mode)   # show it in the story picker
    box = QMessageBox(win)
    box.setWindowTitle("Your story is ready")
    box.setText(f'"{name}" is playing now.\n\nKeep it in your library for another '
                "night, or let it drift away when you close the app?")
    keep = box.addButton("Keep it", QMessageBox.ButtonRole.AcceptRole)
    box.addButton("Just tonight", QMessageBox.ButtonRole.RejectRole)
    box.exec()
    if box.clickedButton() is keep:
        llm_story.save(story)               # register (idempotent) + persist
        win.status.showMessage(f"Saved {name}", 4000)
