//  Lectures.swift
//  Vesper — a small starter set of soothing sleep-lectures (the iOS seed of the
//  desktop library of 337). Each lecture is a title, an ambience hint and an
//  ordered list of short sentences delivered slowly with breath-length pauses.
//
//  This is plain data; the full library can be bundled later as JSON. The
//  desktop "wonder-over-mastery, metaphor-as-map" voice is kept.

import Foundation

struct Lecture: Identifiable, Hashable {
    let title: String
    let branch: String
    let lines: [String]
    var id: String { title }
}

enum Lectures {
    static let all: [Lecture] = [
        Lecture(title: "The Constellations", branch: "The Cosmos", lines: [
            "Let your eyes grow heavy, and imagine the night sky opening above you.",
            "Long ago, people looked up at the same stars you can see tonight.",
            "They noticed that the points of light seemed to gather into shapes.",
            "A hunter. A swan. A great bear walking slowly around the pole.",
            "The stars themselves are not truly close to one another.",
            "Some are near, some unimaginably far, scattered through the deep.",
            "It is only from here, from this small blue world, that they line up.",
            "A constellation is really a story we lay gently over the dark.",
            "A way of remembering. A map drawn in light, to find our way home.",
            "And as the earth turns, the whole quiet wheel of them turns with it.",
            "So let the sky turn slowly now, and let yourself be carried with it.",
            "There is nothing to hold on to. Only the slow drift of the stars.",
        ]),
        Lecture(title: "How Glass Is Made", branch: "Materials & Making", lines: [
            "Settle in, and let your breathing slow, like sand settling in water.",
            "Glass begins as the most ordinary thing in the world. Sand.",
            "Ordinary sand, warmed in a furnace until it forgets that it is solid.",
            "At a great heat it softens, and begins to flow, slow as honey.",
            "A glassmaker gathers a glowing drop on the end of a long pipe.",
            "And then, with a single steady breath, they blow into the pipe.",
            "A bubble opens inside the glowing glass, like a held breath.",
            "They turn it, and turn it, so gravity cannot pull it out of true.",
            "As it cools, the flowing stops, but the glass never fully sets.",
            "It stays, forever, a liquid that has simply slowed almost to stillness.",
            "A clear, quiet thing, made of warmth and sand and one long breath.",
            "Let your own breath be that gentle now. Slow. Even. Almost still.",
        ]),
        Lecture(title: "The Tides", branch: "Earth & Sea", lines: [
            "Let everything grow calm, the way the shore calms between waves.",
            "Twice a day, all the seas of the world rise, and twice they fall.",
            "This is the tide, the slow breathing of the ocean against the land.",
            "It is the moon that draws the water gently up toward itself.",
            "A soft, invisible pull, reaching across the dark of space.",
            "The whole sea leans toward the moon, and a swell follows it round.",
            "Where you stand, the water climbs the sand, grain by grain.",
            "Then, just as gently, it loosens, and slides back out to sea.",
            "Nothing hurries. The tide has all the time there has ever been.",
            "In and out. Rising and falling. The patient breath of the world.",
            "Let your breath fall in beside it now, unhurried, and let go.",
            "Out with the tide. And in. And out again, into sleep.",
        ]),
        Lecture(title: "A Quiet Body Scan", branch: "The Body", lines: [
            "There is nothing to do now but rest, and follow these words.",
            "Bring a soft attention to the top of your head, and let it soften.",
            "Let your forehead smooth. Let the small muscles around your eyes rest.",
            "Let your jaw loosen, your tongue grow soft behind your teeth.",
            "Feel your shoulders drop, a little further than you thought they could.",
            "Let the warmth move down your arms, all the way to your fingertips.",
            "Let your chest rise and fall on its own, without your help.",
            "Feel your back held by the bed beneath you, completely supported.",
            "Let your hips, your legs, your feet grow heavy and warm.",
            "There is nowhere to be. Nothing to carry. Everything can wait.",
            "With each breath out, sink a little deeper into the quiet.",
            "Rest now. You are exactly where you need to be.",
        ]),
    ]

    static func byTitle(_ t: String) -> Lecture? { all.first { $0.title == t } }
}
