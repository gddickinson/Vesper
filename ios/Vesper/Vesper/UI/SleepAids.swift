//  SleepAids.swift
//  Vesper — guided sleep-onset sessions, an alternative to the bedtime stories
//  in Sleep mode. Each is a stream of soft lines the wind-down narrator speaks
//  slowly. Pure content; reuses the existing Narrator / NeuralNarrator. Cognitive
//  Shuffle is generated fresh each night.

import Foundation

enum SleepAids {
    /// Sentinel: narrate the chosen lecture/story instead of a guided session.
    static let storyName = "Bedtime story"

    /// Names for the Sleep "Guided" picker (story first).
    static let names: [String] = [
        storyName, "Body Scan", "Yoga Nidra", "Loving-Kindness",
        "Safe Place", "Gentle River", "Cognitive Shuffle",
        // — sessions drawn from CBT-I / sleep-hypnosis techniques —
        "Let Go of Trying", "Drifting Deeper", "Awake in the Night", "Put the Day to Rest",
    ]

    /// Old names (saved in settings before the 2026-11-13 rename) -> current names.
    static let renamed: [String: String] = [
        "Deeper Sleep": "Drifting Deeper",          // legacy name
        "Yoga Nidra (NSDR)": "Yoga Nidra",          // legacy name
    ]
    static func canonical(_ n: String) -> String { renamed[n] ?? n }

    /// Lines to narrate for a guided session, or nil to use the story.
    static func lines(for name: String) -> [String]? {
        switch canonical(name) {
        case "Body Scan":        return bodyScan
        case "Yoga Nidra":        return yogaNidra
        case "Loving-Kindness":  return lovingKindness
        case "Safe Place":       return safePlace
        case "Gentle River":     return gentleRiver
        case "Cognitive Shuffle": return cognitiveShuffle()
        case "Let Go of Trying":  return paradoxical
        case "Drifting Deeper":   return deeperSleep
        case "Awake in the Night": return awakeInNight
        case "Put the Day to Rest": return putDayToRest
        default:                 return nil
        }
    }

    // MARK: scripts

    private static let bodyScan = [
        "Let your eyes close, and let the day settle behind you.",
        "There is nothing to do now but rest.",
        "Bring your attention to the top of your head, and let it soften.",
        "Let your forehead smooth, and the small muscles around your eyes let go.",
        "Feel your jaw unclench. Let your tongue rest soft in your mouth.",
        "Let your neck lengthen, and your shoulders drop away from your ears.",
        "Feel your arms grow heavy — your elbows, your wrists, each finger.",
        "Let your chest rise and fall on its own, slow and easy.",
        "Soften your belly. Let it be loose and round with each breath.",
        "Feel your back, held by the bed beneath you.",
        "Let your hips settle, and the weight of your legs sink down.",
        "Your thighs, your knees, your calves, growing heavier.",
        "Feel your ankles loosen, and the soles of your feet let go.",
        "Your whole body, heavy and warm, held and safe.",
        "There is nowhere to be, and nothing to hold.",
        "Just rest here, and let sleep find you.",
        "Heavy, and warm, and still.",
    ]

    private static let yogaNidra = [
        "Find a comfortable stillness, and let your body be completely supported.",
        "This is a time of deep rest. You may drift, or you may stay. Both are welcome.",
        "Become aware of the points where your body touches the bed.",
        "The back of your head. Your shoulders. Your hands. Your heels.",
        "Now bring your awareness to your right hand, and simply notice it.",
        "Move your attention slowly up the right arm, to the shoulder.",
        "And across to the left hand, and up the left arm.",
        "Feel both legs, from the toes to the hips, heavy and warm.",
        "Sense the whole front of the body, soft and open.",
        "Sense the whole back of the body, held and safe.",
        "Now feel your breath, moving on its own, without any effort.",
        "With each out-breath, let yourself sink a little deeper.",
        "You are calm. You are rested. You are exactly where you need to be.",
        "Let your awareness widen, soft and spacious, like the night sky.",
        "And rest.",
    ]

    private static let lovingKindness = [
        "Let your breath slow, and bring to mind someone you love.",
        "Silently wish them well. May you be safe. May you be peaceful.",
        "May you be healthy. May you rest with ease.",
        "Now turn that same kindness toward yourself.",
        "May I be safe. May I be peaceful. May I be at ease.",
        "Let the warmth widen to someone nearby, perhaps in the next room.",
        "May you be safe. May you be peaceful. May you rest well.",
        "Widen it further — to your street, your town, all who are trying to sleep tonight.",
        "May you be safe. May you be at ease. May you find rest.",
        "Let the kindness spread as far as it will go, soft and boundless.",
        "And let it settle back over you, like a warm blanket.",
        "May you be peaceful. May you sleep deeply. May you be well.",
    ]

    private static let safePlace = [
        "Let your eyes close, and imagine a place where you feel completely safe.",
        "It might be real, or somewhere only you know. Let it appear.",
        "Notice what is around you — the colours, the soft shapes, the light.",
        "Hear the gentle sounds of this place. Perhaps water, or wind, or quiet.",
        "Feel the air on your skin, warm or cool, just as you like it.",
        "There is a comfortable place here to rest. Settle into it.",
        "Nothing can reach you here. You are held, and at ease.",
        "With every breath, this place grows softer and more peaceful.",
        "Let yourself sink into its calm. You can return any night.",
        "Rest now, in your safe and quiet place.",
    ]

    private static let gentleRiver = [
        "Imagine you are lying in a small wooden boat on a slow, gentle river.",
        "The water is calm, and it carries you without any effort at all.",
        "Above you, a soft sky drifts by. Branches lean over and pass.",
        "The boat rocks, the smallest amount, from side to side.",
        "You hear the quiet lap of water against the wood.",
        "Around each slow bend, the world grows quieter.",
        "There is nothing to steer, and nothing to do. The river knows the way.",
        "Let the current carry you, deeper and slower.",
        "The banks grow soft and dim, and the light grows low.",
        "You are drifting now, warm and safe, carried gently downstream.",
        "Let go, and let the river carry you into sleep.",
    ]

    /// Based on paradoxical intention: gently giving up the effort to fall asleep,
    /// so there is less pressure to "get it right"; sleep is allowed to arrive.
    private static let paradoxical = [
        "For these few minutes, you have permission to give up trying to sleep.",
        "You do not have to fall asleep tonight. You only have to rest.",
        "Sleep is not something you can force. It comes on its own, when you stop reaching for it.",
        "So let go of the effort entirely. Let your body lie here, simply awake and calm.",
        "If you happen to stay awake, that is completely fine. Resting is enough.",
        "Notice how it feels to stop chasing sleep. The pressure begins to ease.",
        "There is nothing to achieve, nothing to fix, nowhere to get to.",
        "Just your breath, moving in and out, and your body, heavy and still.",
        "Let the wish to sleep float away. You are content simply to lie here.",
        "And in that letting go, with no effort at all, sleep is free to find you.",
        "Rest easy. Stay as awake as you like. There is all the time in the world.",
    ]

    /// A slow, permissive "sleep deeper" suggestion, in the style of the
    /// sleep-hypnosis scripts used in research by Cordi & Rasch (2014).
    private static let deeperSleep = [
        "Let your breathing slow, and let every word settle gently into your body.",
        "With each breath out, you drift a little further down, into deeper rest.",
        "Your mind is growing calm and quiet, like a still lake at night.",
        "Imagine yourself sinking, slowly and safely, into soft, deep water.",
        "Down, and down, each layer warmer and more peaceful than the last.",
        "As you sink, your sleep grows deeper. Long, slow waves of deep sleep.",
        "Your body knows how to do this. Let it carry you into deep, restoring sleep.",
        "Deeper now. Slower. Heavier. Wonderfully calm.",
        "Let tonight's sleep be deep and easy, and let the morning come gently.",
        "Every breath takes you deeper. Down into the slow, restful depths of sleep.",
        "Let yourself go completely. Deep, deep sleep, all through the night.",
        "Drifting down… deeper… and deeper… into a full and restful sleep.",
    ]

    /// Stimulus control for the 3 a.m. wake — the quarter-hour rule, made kind.
    /// Strengthens the bed–sleep association; clock-watching and effort are
    /// gently set aside, and prolonged wakefulness is met with a calm reset.
    private static let awakeInNight = [
        "Waking in the night is normal. Everyone does it. Nothing has gone wrong.",
        "There is no need to check the time. Knowing it will only stir the mind.",
        "You don't have to fall back asleep right now. Just rest, and breathe.",
        "Let your body stay soft and warm under the covers, eyes gently closed.",
        "Breathe out slowly, a little longer than you breathe in. Let it lengthen.",
        "If your thoughts start to race, that's alright. Let them pass like clouds.",
        "If you've been lying awake a long while and feel tense or frustrated,",
        "it's okay to slip out of bed for a few minutes, somewhere dim and quiet,",
        "and do something gentle until you feel sleepy again. Then return to bed.",
        "Your bed is a place for rest. Sleep will come back; it always does.",
        "For now, simply breathe, and let your body be heavy, and wait without waiting.",
        "Soft, and slow, and patient. Rest is already happening.",
    ]

    /// Constructive worry / cognitive offloading — writing or naming tomorrow's
    /// tasks before bed so they can be set down for the night (the idea behind
    /// Scullin et al., 2018).
    private static let putDayToRest = [
        "Before you sleep, let's set the day down, so your mind can rest.",
        "Bring to mind anything still turning over — a worry, a task, a loose end.",
        "You don't need to solve it now. Night is not the time for solving.",
        "Picture a small notebook by your bed. In it, you place each concern.",
        "For each one, name the single next small step, and then set it on the page.",
        "It is written down now. It will keep until morning. You can let it go.",
        "One by one, lay each thought into the notebook, and close the cover.",
        "Tomorrow has been given what it needs. Tonight has only rest.",
        "Whatever is left undone can wait. The day is complete, just as it is.",
        "Let your shoulders drop. The carrying is finished for today.",
        "Your mind is lighter now, the loops are closed, the page is full.",
        "There is nothing left to hold. Let yourself sink softly into sleep.",
    ]

    /// A fresh "serial diverse imagining" sequence each night.
    private static func cognitiveShuffle() -> [String] {
        let bank = [
            "a lantern", "a pebble", "an apple", "a feather", "a teapot", "a sailboat",
            "a candle", "a meadow", "a snail", "a kite", "a pinecone", "a violin",
            "a mitten", "a doorway", "a bicycle", "a seashell", "a haystack", "a pillow",
            "a window", "a daisy", "a saucer", "a lighthouse", "a balloon", "a ribbon",
            "a chestnut", "a teaspoon", "a hammock", "a willow", "a marble", "a basket",
            "a feather quill", "a snowflake", "a pebbled path", "a wooden spoon",
            "a paper boat", "a garden gate", "a round stone", "a soft cloud",
            "a quiet pond", "a folded map",
        ]
        let intro = "Let your mind wander gently. Picture each thing for a moment, then let it go."
        let words = bank.shuffled().prefix(30).map { "Picture \($0)." }
        return [intro] + Array(words)
    }
}
