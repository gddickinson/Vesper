"""Offline test for the guided-program stepping (breathsim/session.py).

A SessionDirector drives every guided program (Wim Hof, pranayama, body-scan,
vocal warm-up, NSDR, sleep wind-down, ...) by walking its Stages on the breath
clock: each stage starts cleanly at its time, applies its settings once and speaks
its line, and the final stage simply holds once the program is over. This locks
that stepping with a fake app + a controllable clock -- the setup, the transitions
(applied/announced exactly once per stage, never re-applied mid-stage), the
end-of-program hold, stage_info's countdowns, and the unknown / empty-program
edges -- plus a smoke over every shipped program. Pure logic, no Qt / audio.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import programs  # noqa: E402
from breathsim.session import SessionDirector  # noqa: E402


class _Clock:
    def __init__(self):
        self.now = 0.0
        self.session_seconds = 0.0

    def elapsed(self):
        return self.now


class _Speech:
    def __init__(self):
        self.said = []

    def announce(self, text):
        self.said.append(text)


class _Engine:                       # only the non-program path touches this
    def set_morph(self, x):
        pass

    def set_voice_b(self, n):
        pass


class _App:
    def __init__(self):
        self.controller = _Clock()
        self.speech = _Speech()
        self.engine = _Engine()
        self.applied = []            # stages handed to apply_stage, in order

    def apply_stage(self, stage):
        self.applied.append(stage)


def _prog():
    return programs.Program("Test", "d", [
        programs.Stage("Settle", 1.0, {"voice": "A"}, "settle in"),
        programs.Stage("Deepen", 2.0, {"voice": "B"}, "deepen now"),
        programs.Stage("Rest", 1.0, {"voice": "C"}, "and rest"),
    ])


def test_start_sets_up_the_schedule():
    app = _App(); app.controller.now = 100.0
    d = SessionDirector(app)
    d.start_program(_prog())
    assert d.program is not None
    assert d._starts == [0.0, 60.0, 180.0], d._starts
    assert d._total == 240.0
    assert app.controller.session_seconds == 100.0 + 240.0
    # starting cues stage 0 right away (applied + spoken once)
    assert d.program_stage == 0
    assert app.applied[-1].title == "Settle" and app.speech.said[-1] == "settle in"
    print("ok: start lays out _starts/_total/session_seconds and cues stage 0")


def test_transitions_apply_once_and_hold_at_the_end():
    app = _App(); app.controller.now = 100.0
    d = SessionDirector(app)
    d.start_program(_prog())
    t0 = d.program_t0
    n0 = len(app.applied)
    d.update(t0 + 30); d.update(t0 + 55)                  # mid stage 0
    assert d.program_stage == 0 and len(app.applied) == n0   # no re-apply mid-stage
    d.update(t0 + 61)                                     # stage 1 (starts at 60)
    assert d.program_stage == 1 and app.applied[-1].title == "Deepen"
    assert app.speech.said[-1] == "deepen now"
    d.update(t0 + 181)                                    # stage 2 (starts at 180)
    assert d.program_stage == 2 and app.applied[-1].title == "Rest"
    d.update(t0 + 99999)                                  # well past the end
    assert d.program_stage == 2                           # holds the last stage
    assert [s.title for s in app.applied] == ["Settle", "Deepen", "Rest"]
    print("ok: each stage applies + speaks once, last stage holds past the end")


def test_stage_info_countdowns():
    app = _App(); app.controller.now = 0.0
    d = SessionDirector(app)
    d.start_program(_prog())                              # program_t0 = 0
    app.controller.now = 30.0                             # 30 s into stage 0 (ends at 60)
    title, i1, n, stage_rem, total_rem = d.stage_info()
    assert title == "Settle" and i1 == 1 and n == 3
    assert abs(stage_rem - 30.0) < 1e-6                   # 60 - 30
    assert abs(total_rem - 210.0) < 1e-6                  # 240 - 30
    # countdowns never go negative once the program is over
    app.controller.now = 9999.0
    _, _, _, sr, tr = d.stage_info()
    assert sr == 0.0 and tr == 0.0
    print("ok: stage_info reports the right stage + non-negative countdowns")


def test_unknown_and_empty_programs_degrade():
    app = _App()
    d = SessionDirector(app)
    d.start_program("no such program")                   # unknown -> no-op
    assert d.program is None and d.stage_info() is None
    d.update(123.0)                                       # manual path, must not raise
    # an empty-stages program is accepted but never advances or crashes
    app2 = _App(); d2 = SessionDirector(app2)
    d2.start_program(programs.Program("Empty", "d", []))
    assert d2.program_stage == -1 and d2.stage_info() is None
    d2.update(d2.program_t0 + 50.0)
    assert app2.applied == []
    print("ok: unknown / empty-stages programs degrade safely")


def test_every_shipped_program_steps_in_order():
    assert programs.names()
    for name in programs.names():
        prog = programs.get(name)
        app = _App(); app.controller.now = 0.0
        d = SessionDirector(app)
        d.start_program(prog)
        t0 = d.program_t0
        n = len(prog.stages)
        for k in range(n + 2):                            # walk into each stage, then past
            d.update(t0 + d._starts[min(k, n - 1)] + 1.0)
        # every positive-length stage applied exactly once, in order
        expect = [s.title for s in prog.stages if s.minutes > 0]
        assert [s.title for s in app.applied] == expect, (name, len(app.applied))
        assert all(s.minutes > 0 for s in prog.stages), (name, "0-min stage")
    print("ok: all %d shipped programs step through in order" % len(programs.names()))


def main():
    test_start_sets_up_the_schedule()
    test_transitions_apply_once_and_hold_at_the_end()
    test_stage_info_countdowns()
    test_unknown_and_empty_programs_degrade()
    test_every_shipped_program_steps_in_order()
    print("PASS: guided-program stepping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
