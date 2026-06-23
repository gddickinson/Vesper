"""Content for the physics sleep-lecture: a poetic deep-dive on the cosmos.

Authored (not procedural) text for the "Spacetime & the Quantum" lecture — a long,
gentle wander through relativity, wave–particle duality, the quantum world and
cosmology, threaded with the idea that mathematics is the territory and our words
are only metaphor. Delivered slowly by ``lectures.units`` so it lulls, not lectures.
Pure data: a list of sections, each a list of short lines.
"""
from __future__ import annotations

NAME = "Spacetime & the Quantum"
AMBIENCE = "Brown Noise"            # a deep, even hush — the sound of the void

SECTIONS = [
    # --- invitation ---
    [
        "Tonight, let us wander together through some of the strangest and most "
        "beautiful ideas we have ever had about the universe.",
        "There is nothing here to study, and nothing at all to remember.",
        "Let the words drift over you like weather, and let your body grow heavy "
        "and warm.",
        "We will speak of space and time, of light and matter, of the very small "
        "and the almost unthinkably large.",
        "And whenever an idea grows too heavy to hold, simply set it down, and "
        "let yourself drift.",
    ],
    # --- math as metaphor ---
    [
        "Before we begin, a quiet confession.",
        "No one truly pictures these things. Not the physicists. Not anyone at all.",
        "Deep down, the universe does not speak in pictures, or in words. It speaks "
        "in mathematics.",
        "An equation is a kind of poem — a few small symbols standing patiently for "
        "something far too vast to say out loud.",
        "When we say that a particle is a wave, or that space itself can bend, we "
        "are only reaching for metaphor.",
        "The mathematics is the territory. Our images are gentle maps, sketched by "
        "candlelight.",
        "So let the metaphors be soft, and imperfect. They are lanterns we carry "
        "into the dark — not the landscape itself.",
        "And that is alright. We can love a thing we cannot fully picture.",
    ],
    # --- spacetime and relativity ---
    [
        "Let us begin with light.",
        "More than a century ago, two patient men, Michelson and Morley, tried to "
        "measure the earth's motion through space by racing beams of light against "
        "one another.",
        "To their astonishment, the light did not care.",
        "However they turned, however they moved, the speed of light stayed exactly, "
        "stubbornly, the same.",
        "A young Einstein took this strange little fact, and followed it, calmly, "
        "all the way to the end.",
        "If the speed of light never changes, he saw, then space and time themselves "
        "must be the things that give way.",
        "They are not the fixed stage we imagined. They are woven together into a "
        "single, supple fabric — spacetime.",
        "A moving clock runs slow. A traveler's seconds stretch, ever so gently, "
        "compared to your own.",
        "And mass, he realised, curves this fabric, the way a heavy stone dimples a "
        "sheet pulled taut.",
        "We give that dimpling a familiar name. We call it gravity.",
        "A falling apple, a turning planet — each only follows the gentle valleys "
        "that mass carves into spacetime.",
        "The stretched sheet is just a metaphor, of course. The real curving happens "
        "in four dimensions, where no hand can point.",
        "In 1919, during a total eclipse, an astronomer named Eddington watched "
        "starlight bend as it grazed the darkened sun.",
        "It bent by just the amount Einstein's equations had quietly foretold. The "
        "stars had shifted, a little, from where they ought to be.",
        "Spacetime was real. And it was listening.",
        "Even now, the satellites that whisper directions to us must correct their "
        "clocks for this, every single day, or slowly lead us astray.",
        "Relativity is not a rumor from the edge of physics. It is woven into the "
        "ground beneath your feet.",
    ],
    # --- wave-particle duality ---
    [
        "Now let us grow smaller, and quieter, and turn to the world of the very "
        "small.",
        "Imagine a wall with two narrow slits, and a soft light shining through.",
        "On the screen beyond, the light does not lay down two bright lines, the way "
        "thrown pebbles would.",
        "Instead it paints many soft bands — bright, then dark, then bright again — "
        "the unmistakable ripple of waves overlapping.",
        "It is the very pattern two stones make when dropped into a still pond. So "
        "light is a wave. The matter seemed settled.",
        "But then the experimenters turned the light down, lower and lower, until it "
        "left one tiny piece at a time. One photon, alone. Then another.",
        "Each arrives as a single faint dot, like a single grain of sand. So light "
        "is a particle after all.",
        "And yet — as the lonely dots gather, one by one, over minutes and hours — "
        "they slowly build the same rippling bands.",
        "Each single particle, somehow, passes through both slits at once, and "
        "quietly interferes with itself.",
        "So we lean in, and set a gentle watcher at the slits, to catch which path "
        "each one truly takes.",
        "And the instant we look, the ripples vanish. The pattern collapses into two "
        "plain and ordinary lines.",
        "The universe, it seems, will not be both watched and wavelike at the same "
        "time.",
        "The photon is not really a wave, and not really a particle. It is something "
        "for which we simply have no everyday word.",
        "Wave and particle are two metaphors, two maps, for a single thing that lives "
        "in neither of our worlds.",
    ],
    # --- the quantum universe ---
    [
        "This is the heart of the quantum world — and it is gentler, and stranger, "
        "than any story.",
        "Before we look, a particle has no single place. It is described instead by "
        "a wavefunction — a soft haze of every possibility at once.",
        "Here, and there, and elsewhere, all at the same time. We call this "
        "superposition.",
        "It is not that we are simply ignorant of where it is. It is that, until we "
        "look, there is no single where.",
        "And there is a quiet limit, which Heisenberg first heard, on how much we may "
        "ever know.",
        "The more precisely we pin down where a particle is, the more its motion "
        "blurs away — and the reverse, just as surely.",
        "Position and motion are like two ends of a seesaw. Press one down, and the "
        "other rises gently beyond your reach.",
        "When at last we measure, the haze of possibility settles, all at once, into "
        "a single quiet fact.",
        "Strangest of all is what Einstein uneasily called spooky action at a "
        "distance.",
        "Two particles can be born together, entangled, sharing one story even after "
        "they drift far, far apart.",
        "Measure one, and the other answers in the very same instant — though oceans, "
        "or whole galaxies, lie between them.",
        "Einstein hoped this meant the theory was unfinished — that some hidden, "
        "sensible truth lay quietly underneath.",
        "But a thoughtful man named Bell found a way to put the question directly, "
        "and patient experimenters, like Aspect, carried out the test.",
        "And the universe gave its answer, again and again. There is no cosy hidden "
        "machinery. The strangeness is simply, genuinely real.",
        "Here our metaphors grow thinnest of all. The mathematics stays steady and "
        "exact; it is only our pictures that tremble.",
    ],
    # --- cosmology ---
    [
        "Now let us open our eyes again, and grow very large, and very slow.",
        "Look out at the galaxies — those great quiet islands, each of a hundred "
        "billion stars.",
        "Nearly every one is drifting away from us. And the farther it lies, the "
        "faster it goes.",
        "Hubble first saw this, written in the colour of their light — stretched, and "
        "reddened, like the lowering tone of a train as it passes.",
        "The galaxies are not so much flying through space, as the space between them "
        "is gently, endlessly growing.",
        "And if space is stretching now, then long ago it was smaller. And hotter. "
        "And closer together.",
        "Wind the story back far enough, and all that is draws into a single blinding "
        "warmth — the beginning we call the Big Bang.",
        "It left an afterglow — a faint warmth filling all of space, cooled now to "
        "a whisper, just above the absolute cold.",
        "Two engineers, Penzias and Wilson, stumbled upon it — a faint hiss in their "
        "antenna they could not explain away, arriving from every direction at once.",
        "It was the light of the newborn universe, still gently raining down on us, "
        "after thirteen billion years.",
        "We are very small, then. And very brief. A soft flicker of awareness, on one "
        "quiet world, among uncountable others.",
        "And yet — here we are. Made of the ash of long-dead stars, somehow able to "
        "wonder about it all.",
    ],
    # --- the nature of things (closing) ---
    [
        "So what is the universe, in the end?",
        "It is lawful, and it is strange. The same few rules hold in a falling leaf "
        "and in the farthest, faintest galaxy.",
        "It is woven of space and time, of waves that are also particles, of "
        "possibility that becomes fact only when it is met.",
        "And it is, in some deep way, beyond our picturing — speaking always in a "
        "mathematics that our words can only echo.",
        "Perhaps that is not a problem to be solved, but a quiet to be rested in.",
        "The map is not the territory. The metaphor is not the thing. And the mystery "
        "is not a debt you must repay tonight.",
        "You are a small, warm part of this vast and lawful strangeness — star-stuff, "
        "grown somehow able to dream.",
        "Let the equations keep their secrets a little longer.",
        "Let your breath slow, and your thoughts grow faint, like distant stars at "
        "the very edge of sleep.",
        "There is nothing left to understand. There is only this — the gentle weight "
        "of your body, and the quiet turning of the universe, holding you as you "
        "drift.",
        "Rest now.",
    ],
]
