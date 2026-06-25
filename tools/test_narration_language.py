"""Offline test for narration voice grouping by language (no model, no Qt).

`narration.kokoro_language_groups` splits Kokoro voice ids by spoken language via
the id prefix, so the narration-voice picker offers Spanish / French / Hindi /
Italian / Japanese / Portuguese / Chinese groups (English variants first) instead
of one big 'Other languages' bucket. Pure logic, tested with a fixture id list;
`voice_groups` is also exercised to confirm it never crashes and degrades.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import narration  # noqa: E402

# one female + (sometimes) male id per language, plus an unknown prefix
FIXTURE = ["bf_emma", "bm_george", "af_heart", "am_adam", "ef_dora", "em_alex",
           "ff_siwis", "hf_alpha", "hm_omega", "if_sara", "jf_alpha", "jm_kumo",
           "pf_dora", "zf_xiaobei", "zm_yunjian", "xx_weird"]


def main():
    groups = narration.kokoro_language_groups(FIXTURE)
    headers = [h for h, _ in groups]
    assert headers == [
        "British (Kokoro)", "American (Kokoro)", "Spanish (Kokoro)",
        "French (Kokoro)", "Hindi (Kokoro)", "Italian (Kokoro)",
        "Japanese (Kokoro)", "Portuguese (Kokoro)", "Chinese (Kokoro)",
        "Other (Kokoro)"], headers
    print("ok: languages split out, English variants first, 'Other' last")

    by = dict(groups)
    assert by["Spanish (Kokoro)"] == ["ef_dora", "em_alex"]
    assert by["Japanese (Kokoro)"] == ["jf_alpha", "jm_kumo"]
    assert by["Other (Kokoro)"] == ["xx_weird"]              # unknown prefix
    # every fixture id lands in exactly one group, none lost
    placed = [v for _, lst in groups for v in lst]
    assert sorted(placed) == sorted(FIXTURE), "every voice grouped exactly once"
    print("ok: each voice routed to the right language group (none lost)")

    # edge cases: empty / None -> no groups, never raises
    assert narration.kokoro_language_groups([]) == []
    assert narration.kokoro_language_groups(None) == []
    print("ok: empty / None inputs are safe")

    # the picker builder never crashes (even with speech=None, now None-safe) and
    # returns well-formed (header, [ids]) tuples; when Kokoro's model is installed
    # it yields the per-language groups, else it degrades to system voices.
    from breathsim import kokoro_tts
    groups2 = narration.voice_groups(None)
    assert isinstance(groups2, list)
    assert all(isinstance(h, str) and isinstance(lst, list) for h, lst in groups2)
    if kokoro_tts.ready():
        assert any("(Kokoro)" in h for h, _ in groups2), "Kokoro language groups expected"
    # a label can be produced for a multilingual id (used by the picker rows)
    assert "Spanish" in narration.voice_label("ef_dora"), narration.voice_label("ef_dora")
    print(f"ok: voice_groups() is None-safe; {len(groups2)} groups; labels work")

    print("PASS: narration language grouping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
