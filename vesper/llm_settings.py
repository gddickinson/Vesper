"""The optional **AI Assistant** settings dialog -- the safe gateway to the LLM.

Everything here is opt-in and **fail-closed**. The whole app works fully with no
backend; the LLM features stay hidden/disabled until the user provides their own
key here (or opts into a local Ollama). This dialog is the ONLY place a key is
entered, and it honours the key-security rules of :mod:`breathsim.llm_keys`:

  * the key is **masked on entry** (password echo) and **never shown back**,
    never logged, never written to a tracked/committed path;
  * the user chooses where it is kept -- **session only** (memory, default),
    the **OS keychain** (most secure, if ``keyring`` is installed), or a local
    **chmod-600 file** (plaintext on this device only, clearly labelled);
  * **Forget** wipes it from everywhere we control;
  * **Ollama** (local, no key) is an explicit opt-in -- no network otherwise.

The :func:`status_text` / :func:`apply_key` / :func:`forget` helpers are Qt-free
and unit-tested offline; :func:`open_llm_settings` is the thin Qt view.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QDialog, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QRadioButton,
                               QVBoxLayout)

from breathsim import llm, llm_keys

from . import widgets

# Storage options offered for a freshly typed key (env is read-only: it is set
# outside the app and always takes precedence, so it is shown, never written).
SESSION, KEYCHAIN, FILE = "session", "keychain", "file"


def muted(text):
    """A muted label that wraps (the notes here are long, sentence-length)."""
    lbl = widgets.muted(text)
    lbl.setWordWrap(True)
    return lbl


# --- Qt-free helpers (unit-tested) ----------------------------------------

def status_text():
    """A safe one-line status of the active backend + key SOURCE (never the key)."""
    st = llm.status()
    backend, src = st["backend"], st["key_source"]
    if backend == "claude":
        return f"Active: Claude  (your key, stored: {src})."
    if backend == "ollama":
        return "Active: local Ollama  (no API key needed)."
    return "Active: none.  Vesper works fully without an assistant."


def apply_key(text, where):
    """Store a typed key via the chosen mechanism. Returns ``(ok, message)`` and
    NEVER includes the key in the message. Empty text is rejected (use forget)."""
    key = (text or "").strip()
    if not key:
        return False, "Type a key first, or use Forget to remove one."
    if where == SESSION:
        llm_keys.set_session(key)
    elif where == KEYCHAIN:
        if not llm_keys.set_keychain(key):
            return False, "Keychain unavailable -- install the 'keyring' package."
    elif where == FILE:
        llm_keys.set_file(key)
    else:
        return False, "Unknown storage option."
    return True, "Key saved. " + status_text()


def forget():
    """Wipe the key from session, the chmod-600 file and the keychain entry."""
    llm_keys.clear()
    msg = "Key forgotten (session, file, keychain). "
    if llm_keys.source() == "env":      # env we cannot clear from here
        msg += "Note: ANTHROPIC_API_KEY is still set in your environment."
    return msg + status_text()


# --- the dialog ------------------------------------------------------------

def open_llm_settings(win):
    dlg = QDialog(win)
    dlg.setWindowTitle("AI Assistant (optional)")
    dlg.setStyleSheet(win.styleSheet())
    dlg.setMinimumWidth(440)
    v = QVBoxLayout(dlg)

    title = QLabel("AI Assistant")
    title.setObjectName("title")
    v.addWidget(title)
    v.addWidget(muted(
        "Optional. Vesper is complete without it. If you add your own Anthropic "
        "API key (or a local Ollama), the app can generate fresh bedtime stories "
        "and help you find features. Your key stays on this device, is never shown "
        "again, never logged, and is never committed or shipped."))

    status = QLabel(status_text())
    status.setWordWrap(True)
    v.addWidget(status)

    src = llm_keys.source()
    if src == "env":
        v.addWidget(muted("A key is set via the ANTHROPIC_API_KEY environment "
                          "variable; it takes precedence over anything saved here."))

    # --- key entry (masked) ---
    v.addWidget(QLabel("Paste your Anthropic API key:"))
    field = QLineEdit()
    field.setEchoMode(QLineEdit.EchoMode.Password)        # masked, never shown back
    field.setPlaceholderText("sk-ant-...  (kept on this device only)")
    v.addWidget(field)

    v.addWidget(QLabel("Keep it:"))
    grp = QButtonGroup(dlg)
    rb_session = QRadioButton("This session only  (in memory, forgotten on quit)")
    rb_key = QRadioButton("In the OS keychain  (most secure)")
    rb_file = QRadioButton("In a local file  (~/.breathsim/llm.json, chmod 600, plaintext)")
    rb_session.setChecked(True)
    for rb, where in ((rb_session, SESSION), (rb_key, KEYCHAIN), (rb_file, FILE)):
        grp.addButton(rb)
        rb._where = where                                 # carry the storage id
        v.addWidget(rb)
    if not llm_keys.keychain_available():
        rb_key.setEnabled(False)
        rb_key.setText(rb_key.text() + "  -- install 'keyring'")

    def chosen_where():
        for rb in (rb_session, rb_key, rb_file):
            if rb.isChecked():
                return rb._where
        return SESSION

    def on_save():
        ok, msg = apply_key(field.text(), chosen_where())
        field.clear()                                     # don't let the key linger
        status.setText(msg)
        if ok and hasattr(win, "rebuild_menu"):
            win.rebuild_menu()                            # reveal gated features

    def on_forget():
        field.clear()
        status.setText(forget())
        if hasattr(win, "rebuild_menu"):
            win.rebuild_menu()

    row = QHBoxLayout()
    save = QPushButton("Save key")
    save.clicked.connect(on_save)
    forget_btn = QPushButton("Forget key")
    forget_btn.clicked.connect(on_forget)
    row.addWidget(save)
    row.addWidget(forget_btn)
    v.addLayout(row)

    # --- local Ollama opt-in (no key, no network unless ticked) ---
    v.addWidget(muted("--- or use a local model ---"))
    oll = QCheckBox("Use a local Ollama server if no key is set  (localhost only)")
    oll.setChecked(bool(getattr(win, "_llm_ollama", False)))

    def on_ollama(checked):
        on = bool(checked)
        llm.enable_ollama(on)
        win._llm_ollama = on                              # persisted on close
        status.setText(status_text())
        if hasattr(win, "rebuild_menu"):
            win.rebuild_menu()

    oll.toggled.connect(on_ollama)
    v.addWidget(oll)
    v.addWidget(muted("Ollama runs entirely on your computer; prompts go only to "
                      "your local server. Off by default."))

    close = QPushButton("Close")
    close.clicked.connect(dlg.accept)
    v.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
    win._llm_settings_dlg = dlg                           # keep a ref
    dlg.exec()
