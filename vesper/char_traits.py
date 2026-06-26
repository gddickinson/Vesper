"""Per-character **motion signatures** for the 2D cast.

The animation engine (``char_anim.AnimState``) is character-agnostic -- every
animal blinks, yawns, swishes and perks on the same shared timers. This map gives
each character a small dict of *multipliers* (default 1.0) so they each move with
their own personality, with no extra per-character drawing code:

  tail    swish width (cats, dogs, foxes are swishy; owls, tortoises barely)
  blink   blink interval (an owl blinks rarely -> 1.8; a frog blinks a lot -> 0.6)
  yawn    yawn interval (sleepy types -- sloth, koala, bear -- yawn often -> ~0.6)
  twitch  ear / nose perk rate + size (rabbits, mice twitch a lot -> ~1.8)
  swivel  head-cock size (an owl swivels its whole head -> ~1.8)
  energy  overall liveliness / tail speed (a duckling is lively; a sloth is calm)

``face.set_character`` pushes ``get(name)`` into the widget's AnimState. Pure data.
"""
from __future__ import annotations

TRAITS = {
    # lively, swishy-tailed
    "Cat": {"tail": 1.6, "energy": 1.1},
    "Dog": {"tail": 1.9, "energy": 1.25, "twitch": 1.2},
    "Fox": {"tail": 1.7, "twitch": 1.3, "energy": 1.15, "swivel": 1.2},
    "Red Panda": {"tail": 1.6, "twitch": 1.3, "energy": 1.05},
    "Mouse": {"tail": 1.5, "twitch": 1.9, "blink": 0.7, "energy": 1.2},
    "Duckling": {"twitch": 1.3, "energy": 1.45, "blink": 1.1, "tail": 0.6},
    # alert birds / perky
    "Owl": {"blink": 1.9, "swivel": 1.8, "tail": 0.3, "energy": 0.8},
    "Chicken": {"twitch": 1.5, "blink": 1.3, "energy": 1.15, "swivel": 1.3},
    "Penguin": {"tail": 0.4, "energy": 0.95, "swivel": 1.2},
    # twitchy ears, quick blinks
    "Bunny": {"twitch": 1.9, "blink": 0.7, "tail": 0.4, "energy": 1.05},
    "Hedgehog": {"twitch": 1.4, "blink": 0.9, "energy": 0.95},
    "Frog": {"blink": 0.55, "tail": 0.5, "energy": 0.9},
    # big, slow, sleepy
    "Bear": {"yawn": 0.6, "energy": 0.8, "tail": 0.3, "swivel": 0.8},
    "Panda": {"yawn": 0.7, "energy": 0.85, "tail": 0.4},
    "Sheep": {"yawn": 0.7, "energy": 0.85, "twitch": 1.1, "tail": 0.4},
    "Sloth": {"yawn": 0.5, "energy": 0.6, "tail": 0.3, "blink": 1.2, "swivel": 0.7},
    "Koala": {"yawn": 0.5, "energy": 0.6, "tail": 0.2, "blink": 1.2, "swivel": 0.7},
    # people: gentle, even motion
    "Woman": {"energy": 1.0, "tail": 0.0, "swivel": 1.1},
    "Man": {"energy": 1.0, "tail": 0.0, "swivel": 1.0},
    # the odd ones out
    "Snowman": {"energy": 0.5, "tail": 0.0, "blink": 1.7, "twitch": 0.5,
                "swivel": 0.6, "yawn": 1.6},   # a snowman holds very still
    "Robot": {"blink": 1.6, "yawn": 2.5, "energy": 0.9, "twitch": 0.6, "tail": 0.0},
    "Skull": {"blink": 2.2, "yawn": 1.4, "energy": 0.85, "tail": 0.0, "swivel": 1.1},
}


def get(name):
    """The motion-signature dict for *name* (empty -> all defaults of 1.0)."""
    return TRAITS.get(name, {})
