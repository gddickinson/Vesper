"""A gentle, honest "when do you usually practise" observation.

Pure + unit-testable. ``best_time_phrase(hours, min_total=5)`` takes the practice
history's hour histogram (a ``{hour: count}`` dict, as stored by
:func:`breathsim.store.log_session`) and returns a kind one-line phrase like
"You most often practise around 9-10 pm", or ``None`` when there is too little
data to say anything honestly. ``best_window(...)`` is the underlying pure
computation. It is only an observation of when you tend to practise -- no advice,
no medical claims.
"""
from __future__ import annotations


def _counts(hours):
    """A 24-slot list of counts from a ``{hour: count}`` dict (robust to junk)."""
    arr = [0] * 24
    if isinstance(hours, dict):
        for hr, n in hours.items():
            try:
                h, c = int(hr), int(n)
            except (TypeError, ValueError):
                continue
            if 0 <= h < 24 and c > 0:
                arr[h] += c
    return arr


def _h12(h):
    """(number, meridian) in 12-hour wording for hour-of-day *h* (0..23)."""
    mer = "am" if h < 12 else "pm"
    num = h % 12 or 12
    return num, mer


def _window_words(a, b):
    """Readable 12-hour wording for the hour window [a, b] (b == a, or a+1 mod 24)."""
    na, ma = _h12(a)
    if a == b:
        return f"{na} {ma}"
    nb, mb = _h12(b)
    if ma == mb:                          # same half of the day -> "9-10 pm"
        return f"{na}-{nb} {ma}"
    return f"{na} {ma}-{nb} {mb}"         # crosses noon/midnight -> "11 pm-12 am"


def best_window(hours, min_total=5):
    """(start_hour, end_hour) you most often practise, or ``None`` if too little
    data. ``end_hour == start_hour`` for a single dominant hour, else the adjacent
    hour (``start+1`` mod 24) when a neighbour is also well-used. Pure."""
    arr = _counts(hours)
    total = sum(arr)
    if total < int(min_total):            # too little to claim a pattern honestly
        return None
    peak = max(arr)
    if peak < 2:                          # need a little repetition to mean it
        return None
    h = arr.index(peak)                   # modal hour (earliest on a tie)
    left, right = arr[(h - 1) % 24], arr[(h + 1) % 24]
    thresh = max(2, peak * 0.5)           # a neighbour worth grouping in
    if max(left, right) >= thresh:
        if right >= left:
            return (h, (h + 1) % 24)
        return ((h - 1) % 24, h)
    return (h, h)


def best_time_phrase(hours, min_total=5):
    """A kind one-liner naming when you usually practise, or ``None`` if too sparse."""
    win = best_window(hours, min_total)
    if win is None:
        return None
    return f"You most often practise around {_window_words(*win)}."
