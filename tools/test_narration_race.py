"""Offline regression: an outgoing narrator must not kill the incoming one.

The bedtime storyteller speaks one line at a time on a background thread; a
voice/scene change bumps a generation token and starts a fresh narrator thread.
Each speaking thread shells out to a player process (macOS ``say`` or
``afplay``). The process handle used to live in a single shared field
(``self._proc``); on a mid-line change the *new* thread overwrote it, and the
still-looping *old* thread then read that field and terminated the **new**
narrator's process -- cutting the new narration's first line to silence.

The fix: each thread loops on and terminates its OWN local process handle, so an
outgoing thread can only ever stop its own audio. This test drives the race
deterministically (no real audio): mid-loop we overwrite ``self._proc`` with a
stand-in for the incoming process and assert the outgoing call leaves it alone.
Pure, no Qt, no audio.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import narration  # noqa: E402


class FakeProc:
    def __init__(self):
        self.terminated = False
        self._done = False

    def poll(self):
        return 0 if (self.terminated or self._done) else None

    def terminate(self):
        self.terminated = True


class FakeSpeech:
    binary = "say"
    available = True


def main():
    nar = narration.Narrator(FakeSpeech())

    spawned = []
    narration.subprocess.Popen = lambda *a, **k: spawned.append(FakeProc()) or spawned[-1]
    narration.time.sleep = lambda *_a, **_k: None       # don't actually wait

    # The incoming narrator's process: the outgoing thread must NOT touch it.
    incoming = FakeProc()

    def racing_active(_tok):
        # Mimic the new narrator thread having just replaced the shared field
        # right before this (outgoing) thread checks whether it should stop.
        nar._proc = incoming
        return False                                     # outgoing thread: stand down

    nar._stop = False
    nar._active = racing_active

    nar._speak_say(1, {"text": "a calm line", "pause": 900}, 0.8, None, "Serena")

    assert len(spawned) == 1, ("expected one spawned proc", len(spawned))
    outgoing = spawned[0]
    assert outgoing.terminated, "the outgoing thread should stop its OWN process"
    assert not incoming.terminated, (
        "BUG: the outgoing thread terminated the incoming narrator's process")
    print("ok: _speak_say terminates only its own process, never the successor's")

    # And a clean run (token stays active until the proc finishes) must not
    # terminate anything -- it just plays to completion.
    spawned.clear()
    calls = {"n": 0}

    def finish_after_one(_tok):
        calls["n"] += 1
        if calls["n"] >= 1:
            spawned[0]._done = True                      # process ended naturally
        return True                                      # token still active

    nar._active = finish_after_one
    nar._speak_say(2, {"text": "another line", "pause": 900}, 0.8, None, "Serena")
    assert spawned and not spawned[0].terminated, (
        "a naturally-finishing line should not be force-terminated")
    print("ok: a line that ends on its own is never force-terminated")

    print("PASS: narration proc-race")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
