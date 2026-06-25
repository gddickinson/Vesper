"""Grouped option sources for the searchable :mod:`picker` (pure data).

Builds the ``[(group_header, [values])]`` lists the picker shows for the long
selectors -- the bedtime story/lecture chooser and the breath-voice chooser --
so the card builders stay short. No Qt here.
"""
from __future__ import annotations

from breathsim import stories, voices

# the breath voices offered as inhale/exhale, by family
_VOICE_GROUPS = (voices.GROUP_BREATH, voices.GROUP_CAT, voices.GROUP_VOCAL,
                 voices.GROUP_TECHNIQUE, voices.GROUP_SING, voices.GROUP_EXERCISE,
                 voices.GROUP_SYNTH, voices.GROUP_CUSTOM)


def voice_groups(include_same=False):
    """Breath-voice families for the picker. ``include_same`` prepends the
    'Same as inhale' option (for the exhale chooser)."""
    out = []
    if include_same:
        out.append(("General", ["Same as inhale"]))
    for g in _VOICE_GROUPS:
        names = voices.names(g)
        if names:
            out.append((g, names))
    return out


def story_groups():
    """Scenes, novels, self-help/poetry, then every lecture branch -- the whole
    bedtime-story menu, grouped for the searchable picker."""
    groups = [("General", ["Off", "Random"]),
              ("Scenes", list(stories.scene_names()))]
    books = list(stories.book_names())
    if books:
        groups.append(("Your novels", books))
    extras = list(stories.extra_names())
    if extras:
        groups.append(("Self-help & poetry", extras))
    for cat in stories.lecture_categories():
        groups.append((cat, list(stories.lecture_names(cat))))
    return groups
