"""Sovereign class feats and the effects they hand out."""
from common import *
from class_data import AC, CF, EF, REGALIA

FT = "feats"
SPEECH = ["auditory", "concentrate", "emotion", "linguistic", "mental"]


def eff_link(key):
    return link(uuid(EF, key))


def build_feat_effects():
    E = []
    E.append(effect(EF, "glorious-inspiration", "Effect: Glorious Inspiration",
        p("Granted by Glorious Inspiration. +1 circumstance bonus to Strikes until the start of the sovereign's next "
          "turn."),
        rules=[{"key": "FlatModifier", "selector": "strike-attack-roll", "type": "circumstance", "value": 1}],
        img="icons/skills/social/thumbsup-approval-like.webp"))
    for tier, val in (("Success", 1), ("Critical Success", 2)):
        E.append(effect(EF, f"death-to-the-tyrant-{val}", f"Effect: Death to the Tyrant ({tier})",
            p(f"The tyrant's minions take a -{val} circumstance penalty to attack rolls for 1 minute. Once the tyrant "
              "is slain, these minions might be willing to end combat early if they have not been harmed."),
            rules=[{"key": "FlatModifier", "selector": "attack-roll", "type": "circumstance", "value": -val}],
            duration=("minutes", 1, "turn-start"), img="icons/skills/social/wave-halt-stop.webp"))
        E.append(effect(EF, f"excommunicated-{val}", f"Effect: Excommunicated ({tier})",
            p(f"Use this on a creature that knows no divine spells: -{val} circumstance penalty to saves and AC "
              f"against divine spells for 1 minute. A creature that knows divine spells is "
              f"{link('stupefied', f'Stupefied {val}')} instead."),
            rules=[{"key": "FlatModifier", "selector": ["ac", "saving-throw"], "type": "circumstance",
                    "value": -val,
                    "predicate": [{"or": ["item:trait:divine", "origin:item:trait:divine"]}]}],
            duration=("minutes", 1, "turn-start"), img="icons/magic/holy/barrier-shield-winged-cross.webp"))
    E.append(effect(EF, "rousing-speech", "Effect: Rousing Speech",
        p("Temporary Hit Points equal to the sovereign's level + 2 for 10 minutes. Apply from the sovereign's chat "
          "card so the effect knows whose level to use."),
        rules=[{"key": "TempHP", "value": "@item.origin.level + 2"}],
        duration=("minutes", 10, "turn-start"), img="icons/skills/social/diplomacy-peace-alliance.webp"))
    E.append(effect(EF, "deep-reflection", "Effect: Deep Reflection",
        p("+1 circumstance bonus to your next skill check. Removed automatically after the roll."),
        rules=[{"key": "FlatModifier", "selector": "skill-check", "type": "circumstance", "value": 1,
                "removeAfterRoll": "if-enabled"}],
        duration=("unlimited", -1, None), img="icons/sundries/survival/mirror-plain.webp"))
    E.append(effect(EF, "golden-touch", "Effect: Golden Touch",
        p(f"For 1 minute, you gain the {link(uuid(AC, 'sovereigns-grace'))} reaction."),
        rules=[grant(uuid(AC, "sovereigns-grace"))],
        duration=("minutes", 1, "turn-start"), img="icons/commodities/treasure/crown-gold-satin-gems-red.webp"))
    E.append(effect(EF, "off-with-their-head", "Effect: Off With Their Head",
        p("Weakness to slashing damage equal to half the sovereign's level until the start of the sovereign's next "
          "turn. If reduced to 0 Hit Points by slashing damage during this time, the creature is decapitated. "
          "Apply from the sovereign's chat card."),
        rules=[{"key": "Weakness", "type": "slashing", "value": "max(1,floor(@item.origin.level/2))"}],
        img="icons/skills/wounds/injury-pain-body-orange.webp"))
    E.append(effect(EF, "queens-gambit", "Effect: Queen's Gambit",
        p(f"You are {link('off-guard', 'off-guard')} until the start of your next turn and can use "
          f"{link(uuid(AC, 'accept-the-gambit'))}."),
        rules=[grant(PF["off-guard"], inMemoryOnly=True), grant(uuid(AC, "accept-the-gambit"))],
        img="icons/skills/melee/maneuver-sword-katana-yellow.webp"))
    E.append(effect(EF, "call-to-halt", "Effect: Call to Halt",
        p("-10-foot penalty to all Speeds for 1 minute."),
        rules=[{"key": "FlatModifier", "selector": "all-speeds", "value": -10}],
        duration=("minutes", 1, "turn-start"), img="icons/skills/social/wave-halt-stop.webp"))
    E.append(effect(EF, "weight-of-the-crown", "Effect: Weight of the Crown",
        p("Set the counter to the number of allies (including your follower) who became wounded or died during this "
          "encounter. You gain a +2 circumstance bonus to damage per ally, or +3 per ally once any ally has died."),
        rules=[
            toggle("weight-of-the-crown-death", "An Ally Has Died", domain="damage"),
            {"key": "FlatModifier", "selector": "damage", "type": "circumstance",
             "value": "2*@item.badge.value", "predicate": [{"not": "weight-of-the-crown-death"}],
             "label": "Weight of the Crown"},
            {"key": "FlatModifier", "selector": "damage", "type": "circumstance",
             "value": "3*@item.badge.value", "predicate": ["weight-of-the-crown-death"],
             "label": "Weight of the Crown"},
        ],
        duration=("encounter", -1, None), badge={"type": "counter", "value": 1, "min": 1},
        img="icons/equipment/head/crown-thorns-gold.webp"))
    return E


def build_feats():
    F = []

    def f(key, name, level, desc, **kw):
        kw.setdefault("traits", ["sovereign"])
        F.append(feat(FT, key, name, level, desc, **kw))

    # ---------------------------------------------------------- 1st
    f("at-your-service", "At Your Service", 1,
      p(f"You are not above aiding others in their work. Designate an ally within 30 feet; this action counts as "
        f"sufficient preparation to {link('Aid')} that ally. When you use the Aid reaction to help that ally, you can "
        "roll Society in place of the usual check."),
      action="action", actions=1, traits=SPEECH + ["sovereign"],
      img="icons/skills/social/diplomacy-handshake-gray.webp")
    f("invoke-rank", "Invoke Rank", 1,
      block("Trigger", "You are about to roll initiative.") + HR +
      p("Invoking your rank as sovereign with confidence can make even the surliest opponents doubt themselves. You "
        "use Society to roll initiative, and creatures that can recognize sovereignty (such as humans, devils or "
        f"vampires, but not demons or animals) must make a Will save against your class DC or be "
        f"{link('off-guard', 'off-guard')} against you or your loyal follower's first Strike this turn: "
        "@Check[will|against:class].") +
      p("<em>Toggle Invoke Rank on before rolling initiative to switch it to Society.</em>"),
      action="free", img="icons/commodities/treasure/crown-gold-laurel-wreath.webp",
      rules=[toggle("invoke-rank", "Invoke Rank (Society Initiative)"),
             {"key": "ActiveEffectLike", "mode": "override", "path": "system.initiative.statistic",
              "value": "society", "predicate": ["invoke-rank"], "phase": "beforeDerived"}])
    f("glorious-inspiration", "Glorious Inspiration", 1,
      p("When you succeed, others around you can't help but feel inspired to do as you do. When you critically "
        "succeed at a Strike, all allies within 60 feet gain a +1 circumstance bonus to their Strikes until the "
        f"start of your next turn. ({eff_link('glorious-inspiration')})"),
      img="icons/skills/social/thumbsup-approval-like.webp",
      rules=[{"key": "Note", "selector": "strike-attack-roll", "outcome": ["criticalSuccess"],
              "title": "{item|name}",
              "text": f"Allies within 60 feet gain {eff_link('glorious-inspiration')}."}])
    f("proscribe-foe", "Proscribe Foe", 1,
      p("You condemn an enemy, decreeing that they should be slain. Select a creature within 30 feet; the creature "
        f"becomes {link('off-guard', 'off-guard')} until the start of your next turn."),
      action="action", actions=1, traits=SPEECH + ["sovereign"], img="icons/skills/social/thumbs-down.webp")
    f("seal-of-approval", "Seal of Approval", 1,
      p("You make it obvious that someone is acting on your behalf by adorning them in some seal of approval, such "
        "as a signet ring, a royal seal, or a coat of arms. Your allies can use your Diplomacy modifier to negotiate "
        "with others on your behalf."),
      img="icons/commodities/treasure/brooch-crown-gold.webp")
    f("trusted-advisor", "Trusted Advisor", 1,
      p("Your loyal follower gives you sage advice and insight into the trustworthiness of others. Despite being a "
        f"minion, your loyal follower gains 1 reaction at the start of its turns, which it can use only to "
        f"{link('Aid')} you on a {link('Recall Knowledge')} check or a Perception check to "
        f"{link('Sense Motive')}. Its very presence counts as preparation to Aid. It automatically succeeds at its "
        "check to Aid you with those skills, or automatically critically succeeds if you're a master of the skill in "
        "question."),
      img="icons/skills/social/diplomacy-writing-letter.webp")

    # ---------------------------------------------------------- 2nd
    f("after-them", "After Them!", 2,
      block("Trigger", "An enemy within line of sight attempts to move away from you.") + HR +
      p("You command your follower to pursue your foe. Your follower Strides up to their Speed, following the enemy "
        "until it stops moving or your follower has moved its full Speed. You can use After Them! to Burrow, Climb, "
        "Fly, or Swim instead of Stride if your follower has the corresponding movement type."),
      action="reaction", img="icons/skills/movement/arrow-upward-yellow.webp")
    f("make-way", "Make Way", 2,
      p("People know to get out of your way as you move through them. You and allies within 60 feet of you do not "
        "treat crowds as difficult terrain. While involved in a chase in an urban environment, you have a +2 "
        "circumstance bonus to all checks involving navigating crowds."),
      img="icons/skills/social/intimidation-impressing.webp",
      rules=[toggle("make-way", "Make Way (Navigating Crowds in a Chase)"),
             {"key": "FlatModifier", "selector": ["skill-check", "perception"], "type": "circumstance",
              "value": 2, "predicate": ["make-way"]}])
    f("loyal-protector", "Loyal Protector", 2,
      p("Your loyal follower is trained to keep you safe. So long as your follower is adjacent to you, you benefit "
        "from lesser cover."),
      prereqs=["Loyal Follower"], img="icons/equipment/shield/heater-steel-worn.webp",
      rules=[toggle("loyal-protector", "Follower Adjacent (Lesser Cover)"),
             {"key": "FlatModifier", "selector": "ac", "type": "circumstance", "value": 1,
              "predicate": ["loyal-protector"], "label": "Loyal Protector"}])
    f("my-champion", "My Champion", 2,
      p("You can have your follower act on your behalf for competitions and challenges, backed by your royal "
        "approval. Your follower gains a +1 circumstance bonus on all rolls made on your behalf, and uses their own "
        "skill or your Society modifier, whichever is higher, when partaking in contests on your behalf."),
      prereqs=["Loyal Follower"], img="icons/skills/social/diplomacy-offering-ritual.webp")
    f("poison-taster", "Poison Taster", 2,
      p("Your follower acts as a poison taster, checking your and your companions' food before you eat, and carrying "
        "solutions to poison when you need it. Every day, your follower creates a number of antidotes and "
        "antiplagues equal to your party size, of an item level equal to your level. Your follower has a +2 "
        "circumstance bonus to detect poison or disease in your meals, and samples your and your allies' meals "
        "every day."),
      img="icons/consumables/potions/bottle-round-corked-green.webp")
    f("royal-impedimenta", "Royal Impedimenta", 2,
      p("Your follower is accustomed to carrying things for you. Your follower's Bulk limit increases by 2. Your "
        "follower can use an action to draw an item and hand it to you."),
      img="icons/containers/bags/pack-leather-white-tan.webp")

    # ---------------------------------------------------------- 4th
    f("by-my-side", "By My Side", 4,
      p(f"Wherever you go, your follower goes with you. When you {link('Stride')} while adjacent to your follower, "
        "your follower Strides with you."),
      img="icons/skills/social/diplomacy-unity-alliance.webp")
    f("death-to-the-tyrant", "Death to the Tyrant", 4,
      p("You stoke the fires of the people to take down those that abuse their position of leadership. Select a "
        "creature within 60 feet that has other creatures obeying it, and make a Society check against the "
        "creature's Will DC: @Check[society|defense:will].") + HR +
      block("Critical Success", f"You shake the confidence of the creature's minions. They take a -2 circumstance "
            f"penalty to their attack rolls for 1 minute. Once the creature is slain, these minions might be willing "
            f"to end combat early if you have not harmed them. ({eff_link('death-to-the-tyrant-2')})") +
      block("Success", f"As critical success, but the penalty is -1. ({eff_link('death-to-the-tyrant-1')})") +
      block("Critical Failure", "You ignite the fury of the creature's minions. They gain a +2 circumstance bonus "
            "to their next attack roll against you within 1 minute."),
      action="action", actions=2, traits=SPEECH + ["sovereign"], img="icons/skills/social/wave-halt-stop.webp")
    f("excommunicate", "Excommunicate!", 4,
      p("You forbid your foes from benefitting from the divine, using your word as a religious leader. Make a "
        "Religion check against the Will DC of a creature within 30 feet: @Check[religion|defense:will].") + HR +
      block("Critical Success", f"You forbid the creature from drawing on the divine. If it knows any divine "
            f"spells, it becomes {link('stupefied', 'stupefied 2')} for 1 minute. If it does not, it takes a -2 "
            f"circumstance penalty to its saves and AC against divine spells for the duration. "
            f"({eff_link('excommunicated-2')})") +
      block("Success", f"As critical success, but stupefied 1 or a -1 penalty. ({eff_link('excommunicated-1')})") +
      block("Failure", "The creature is unaffected.") +
      block("Critical Failure", f"Others doubt your authority over the divine. You become "
            f"{link('stupefied', 'stupefied 1')} for 1 minute."),
      action="action", actions=2, traits=SPEECH + ["sovereign"], prereqs=["expert in Religion"],
      img="icons/magic/holy/barrier-shield-winged-cross.webp")
    f("rousing-speech", "Rousing Speech", 4,
      p("By speaking from the heart, you ignite the passion of your allies and inspire them to fight on. You and all "
        f"allies gain temporary Hit Points equal to your level + 2 for 10 minutes. ({eff_link('rousing-speech')})"),
      action="action", actions=2, traits=SPEECH + ["sovereign"],
      img="icons/skills/social/diplomacy-peace-alliance.webp")
    f("royal-libations", "Royal Libations", 4,
      p("You raise a glass and drink it, passing it to your allies. Whenever you consume a potion or an alchemical "
        "consumable while adjacent to an ally or follower, both you and that ally gain the effects of the "
        "consumable. Only one other creature can benefit from this effect."),
      img="icons/consumables/drinks/wine-amphora-clay-pink.webp")

    # ---------------------------------------------------------- 6th
    f("ascribed-weapon", "Ascribed Weapon", 6,
      p("You have named your weapon, and its name is as well known as your own. When you invest in a specific magic "
        "weapon, you can choose to transfer its powers into your weapon regalia. Your weapon regalia gains the "
        "abilities, runes and activations of the specific magic weapon, but retains its form; for example, if your "
        "weapon regalia is a longsword and you invested a <em>Chainbreaker</em>, you would have a +1 striking "
        "longsword with the Chainbreaker's abilities and Liberating Strike activation."),
      prereqs=["weapon regalia"], img="icons/weapons/swords/sword-guard-gold-red.webp")
    f("burden-of-the-world", "Burden of the World", 6,
      block("Requirements", "You are wielding your orb regalia.") + HR +
      p("You accept the suffering of your allies upon yourself. Select an ally within 30 feet who is suffering from "
        "a negative condition. You cure the ally of the condition, and gain it yourself, for the same duration that "
        "your ally would have been affected by it."),
      action="action", actions=1, traits=["divine", "sovereign"], prereqs=["orb regalia"],
      img="icons/skills/social/orb-gold-claw-yellow.webp")
    f("deep-reflection", "Deep Reflection", 6,
      block("Requirements", "You are wielding your mirror regalia.") + HR +
      p(f"You gaze into your mirror, thinking carefully of the possible consequences of your actions. You "
        f"{link('Recall Knowledge')} using Society. Rather than ask questions about things around you or that have "
        "already happened, you can ask questions about the near future, especially the consequences of your "
        "actions, such as what is likely to happen if you go left down a dungeon rather than right. You have a +1 "
        f"circumstance bonus to your next skill action after using Deep Reflection. ({eff_link('deep-reflection')})"),
      action="action", actions=1, prereqs=["mirror regalia"], img="icons/sundries/survival/mirror-plain.webp")
    f("devoted-subjects", "Devoted Subjects", 6,
      p("A group of your subjects have come to follow you, aiding their sovereign however they can. These "
        "individuals don't function as followers and won't accompany you into dangerous areas or situations. "
        "However, they can train by your side, assist you in creating items, or help you spread your heroic tales.") +
      p("When you are in a place where your subjects could reasonably assist you, you gain a +1 circumstance bonus "
        "to checks to Craft, Coerce, Earn Income, Make an Impression, and Subsist, as well as other downtime "
        "activities at the GM's discretion. Your subjects also help you train: for every 5 days you spend "
        "retraining, you make a week's worth of progress."),
      img="icons/skills/social/diplomacy-unity-alliance.webp",
      rules=[toggle("devoted-subjects", "Subjects Assisting (Craft, Coerce, Earn Income, Impression, Subsist)",
                    domain="skill-check"),
             {"key": "FlatModifier", "selector": "skill-check", "type": "circumstance", "value": 1,
              "predicate": ["devoted-subjects"], "label": "Devoted Subjects"}])
    f("effortless-gesture", "Effortless Gesture", 6,
      block("Requirements", "You are wielding your scepter regalia.") + HR +
      p(f"You command your allies as if they were your most devout followers. You command an ally to perform a basic "
        f"action, such as {link('Step')}, {link('Stride')} or {link('Strike')}. You are then "
        f"{link('off-guard', 'off-guard')} until the start of your next turn as you split your attention between "
        "yourself and them."),
      action="action", actions=1, traits=["flourish", "manipulate", "sovereign"], prereqs=["scepter regalia"],
      img="icons/commodities/treasure/sceptre-jeweled-gold.webp")
    f("golden-touch", "Golden Touch", 6,
      block("Requirements", "You are wearing your jewellery regalia.") +
      block("Frequency", "once per day") + HR +
      p("Anything you touch seems to improve in quality, be it the plans of your court or the luck of your allies. "
        "You lay your hand on an adjacent ally. For the next minute, your ally gains the Sovereign's Grace reaction. "
        f"({eff_link('golden-touch')})"),
      action="action", actions=1, traits=["manipulate", "sovereign"], prereqs=["jewellery regalia"],
      frequency={"max": 1, "per": "day"}, img="icons/commodities/treasure/crown-gold-satin-gems-red.webp")
    f("noble-sacrifice", "Noble Sacrifice", 6,
      block("Trigger", "Your follower would take damage that reduces them to 0 Hit Points.") + HR +
      p("You have a duty to protect your subjects, including those who would lay their lives down for you. You "
        "Stride to your follower, repositioning them so that you stand in their space. You take the damage that the "
        "follower would have taken. If you would have taken damage from this source already, you take both "
        "instances of damage."),
      action="reaction", img="icons/skills/wounds/injury-pain-body-orange.webp")
    f("sovereigns-escort", "Sovereign's Escort", 6,
      block("Requirements", "You are wearing your armor regalia.") +
      block("Trigger", "An adjacent ally Strides.") + HR +
      p("You escort the meek through danger, taking hits aimed for them when needed. You Stride alongside your ally "
        "up to their Speed. If the ally triggers any reactions during this movement, your Stride ends, and you are "
        "subject to the reaction instead of your ally."),
      action="reaction", prereqs=["armor regalia"], img="icons/equipment/chest/breastplate-banded-steel-gold.webp")

    # ---------------------------------------------------------- 8th
    f("generous-benefactor", "Generous Benefactor", 8,
      p("By sponsoring others, you motivate them to do much better in their work. For every 150 gp you spend on "
        "another creature, you give them an increasing +1 circumstance bonus (up to +4) on a downtime roll to Craft. "
        "The money is used up in the Crafting attempt, so if you give it to another player, they cannot return it."),
      img="icons/commodities/currency/coins-assorted-mix-copper-silver-gold.webp")
    f("off-with-their-head", "Off With Their Head", 8,
      p("You command that a creature be decapitated. The creature gains weakness to slashing damage equal to half "
        "your level until the start of your next turn. If the creature is reduced to 0 Hit Points by slashing "
        "damage during this time, it is decapitated. All hostile creatures within 15 feet of the creature become "
        f"{link('frightened', 'frightened 1')}. If the creature has multiple heads and loses one through this "
        f"effect, it becomes {link('frightened', 'frightened 2')}. ({eff_link('off-with-their-head')})"),
      action="action", actions=1, traits=["auditory", "concentrate", "linguistic", "mental", "sovereign"],
      img="icons/skills/wounds/injury-pain-body-orange.webp")
    regalia_choices = [{"value": uuid(CF, "regalia-" + r)} for r in REGALIA]
    f("expanded-regalia", "Expanded Regalia", 8,
      p("Your power has grown to the point of expanding your regalia to greater levels. You gain a second regalia, "
        "including its edicts and anathema."),
      img="icons/commodities/treasure/crown-gold-laurel-wreath.webp",
      rules=[{"key": "ChoiceSet", "flag": "secondRegalia", "prompt": "Choose a second regalia.",
              "choices": regalia_choices},
             grant("{item|flags.system.rulesSelections.secondRegalia}")])
    f("queens-gambit", "Queen's Gambit", 8,
      p(f"By leaving yourself open to attack, you can tempt your opponents into taking up a disadvantageous "
        f"position. You become {link('off-guard', 'off-guard')} until the start of your next turn, and gain the "
        f"{link(uuid(AC, 'accept-the-gambit'))} reaction. ({eff_link('queens-gambit')})"),
      action="action", actions=1, img="icons/skills/melee/maneuver-sword-katana-yellow.webp")
    f("royal-rebuke", "Royal Rebuke", 8,
      block("Requirements", "An ally within 60 feet failed a saving throw against a mental or linguistic effect "
            "since your last turn.") + HR +
      p("You give a short, impassioned speech explaining why your foes are wrong, and you and your allies are "
        "righteous. You roll Society to counteract the effect, recovering half of any lost HP if applicable."),
      action="action", actions=1, traits=["auditory", "concentrate", "emotion", "exploration", "linguistic",
                                         "mental", "sovereign"],
      img="icons/skills/social/peace-luck-insult.webp")
    f("sovereigns-double", "Sovereign's Double", 8,
      p("You have gained the service of an impersonator, a double who is trained to look and speak like you. They "
        "have a Deception modifier equal to your class DC - 10, and will Disguise themselves as you when needed. "
        "When they Disguise themselves as you, they can simultaneously Disguise you as an ordinary citizen, "
        "allowing you to slip out of the spotlight. Your double has the same AC, Hit Points and saves as your "
        "follower, and will not enter combat."),
      img="icons/skills/social/theft-pickpocket-bribery-brown.webp")

    # ---------------------------------------------------------- 10th
    f("a-kings-ransom", "A King's Ransom", 10,
      block("Frequency", "once per day") + HR +
      p(f"You can raise emergency funds rapidly when needed. You roll to {link('Earn Income')}, earning twenty "
        "times the normal value. For the next week, you take a -10 circumstance penalty to Earn Income as your court "
        "recovers from these expenses.") +
      block("Special", "If using the Earn Riches rule from Adventures+, you only earn twice the normal value."),
      frequency={"max": 1, "per": "day"}, img="icons/commodities/currency/coins-assorted-mix-copper-silver-gold.webp")
    f("for-my-liege", "For My Liege!", 10,
      p(f"Even while you lie defeated, your follower fights on. Your follower gains two actions every turn you are "
        f"{link('dying', 'dying')}, {link('paralyzed', 'paralyzed')}, petrified or "
        f"{link('unconscious', 'unconscious')}, as if you had directed them."),
      img="icons/skills/social/intimidation-impressing.webp")
    f("messenger-network", "Messenger Network", 10,
      p("You have messengers traveling the lands in your name. You can learn news of locations within 100 miles "
        "during your daily preparations, and have information issued to members of your court within this area. "
        "Information travels as fast as your couriers, usually about one day per 32 miles, as the messengers are "
        "usually on horseback."),
      img="icons/skills/social/diplomacy-writing-letter.webp")
    f("regalia-bearer", "Regalia-Bearer", 10,
      p("You have entrusted your follower with your regalia, allowing them to wear it in your stead. Your follower "
        "can wield your regalia, gaining use of abilities or feats derived from your regalia."),
      prereqs=["regalia", "loyal follower"], img="icons/commodities/treasure/crown-gold-laurel-wreath.webp")

    # ---------------------------------------------------------- 12th
    f("call-to-halt", "Call to Halt", 12,
      p("You command your foes to stop where they are. Make a Society check against the Will DC of each creature "
        "you choose within 30 feet: @Check[society|defense:will]. Regardless of your result, the targets are "
        "temporarily immune for 10 minutes.") + HR +
      block("Critical Success", f"The target is {link('paralyzed', 'paralyzed')} for 1 round and becomes "
            f"{link('frightened', 'frightened 2')}.") +
      block("Success", f"The target takes a -10-foot penalty to all its Speeds for 1 minute and becomes "
            f"{link('frightened', 'frightened 1')}. ({eff_link('call-to-halt')})"),
      action="action", actions=2,
      traits=["auditory", "concentrate", "emotion", "incapacitation", "mental", "sovereign"],
      img="icons/skills/social/wave-halt-stop.webp")
    f("order-of-exile", "Order of Exile", 12,
      block("Frequency", "once per day") + HR +
      p(f"Your word is so acute that you can banish extraplanar creatures from your reality entirely. You cast "
        f"{link('banishment')} as an occult innate spell, using your class DC as your spell DC."),
      action="action", actions=2, frequency={"max": 1, "per": "day"},
      img="icons/magic/holy/barrier-shield-winged-blue.webp")
    f("mirror-mirror", "Mirror, Mirror", 12,
      block("Frequency", "once per day") + HR +
      p(f"Your mirror allows you to see things not just before you, but all around you. You cast "
        f"{link('clairvoyance')} as an occult innate spell with a range of 1 mile."),
      action="action", actions=2, prereqs=["mirror regalia"], frequency={"max": 1, "per": "day"},
      img="icons/sundries/survival/mirror-plain.webp")

    # ---------------------------------------------------------- 14th
    f("weight-of-the-crown", "Weight of the Crown", 14,
      p("The sacrifices of your allies weigh heavy on your shoulders. For each allied creature who became wounded "
        "during a combat encounter, you gain a +2 circumstance bonus to your damage until the encounter's end. If an "
        "ally (including your follower) dies, the overall bonus increases to +3 for each wounded or dead ally. "
        f"({eff_link('weight-of-the-crown')})"),
      img="icons/equipment/head/crown-thorns-gold.webp")

    # ---------------------------------------------------------- 18th
    f("kneel-before-your-superior", "Kneel Before Your Superior!", 18,
      block("Frequency", "once per day") + HR +
      p(f"Your power is so great that even your foes are forced to bow to you. You can cast "
        f"{link('overwhelming presence')} as a 9th-rank innate divine spell using your class DC."),
      frequency={"max": 1, "per": "day"}, img="icons/equipment/head/crown-gold-red.webp")

    # ---------------------------------------------------------- 20th
    f("long-live-the-king", "Long Live the King", 20,
      p("The title of sovereign is merely that: a title. Anyone can take up your role and lead as you have led. "
        "During your daily preparations, you can spend time designating and training a successor, an NPC you have "
        "chosen to be sovereign when you die. Once per month, when you die, you automatically bestow your power on "
        "your successor. Your successor gains all your abilities and statistics, and if they were present at your "
        "death, they can enter initiative using your character sheet with current and maximum Hit Points equal to "
        "half your maximum Hit Points. Your successor and loyal follower have a +1 circumstance bonus to Strikes "
        "against the creature that felled you."),
      img="icons/commodities/treasure/crown-gold-laurel-wreath.webp")
    f("supreme-sovereign", "Supreme Sovereign", 20,
      p(f"When you have an active follower in an encounter, you are {link('quickened', 'quickened')}; you can use "
        f"the extra action only to {link('Direct Follower', 'Direct your Follower')}."),
      img="icons/commodities/treasure/crown-blue-gold.webp",
      rules=[toggle("supreme-sovereign", "Follower Active in Encounter"),
             grant(PF["quickened"], inMemoryOnly=True, predicate=["supreme-sovereign"])])
    return F


def build_all():
    return {"feats": build_feats(), "effects": build_feat_effects()}
