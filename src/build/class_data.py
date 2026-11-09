"""Sovereign class item, class features, regalia, courts, and shared actions."""
from common import *

CF = "class-features"
AC = "actions"
EF = "effects"


def cf_uuid(key):
    return uuid(CF, key)


# ============================================================ ACTIONS
def build_actions():
    docs = []
    docs.append(action_item(AC, "sovereigns-grace", "Sovereign's Grace",
        block("Frequency", "once per day") +
        block("Trigger", "You fail or critically fail a roll.") + HR +
        p("Your jewellery empowers your fate, giving you control of your future. You can reroll the triggering check, "
          "but you must use the new result, even if it's worse."),
        action="reaction", traits=["fortune"], frequency={"max": 1, "per": "day"},
        img="icons/commodities/treasure/crown-gold-satin-gems-red.webp"))

    docs.append(action_item(AC, "scepters-command", "Scepter's Command",
        block("Requirements", "You are wielding your scepter regalia.") + HR +
        p(f"When you {link('Direct Follower')}, you can spend 1 extra action to give your follower 1 additional action "
          "(3 actions total). If you spend all 3 of your actions this way, your follower gets 4 actions instead, but "
          "must then attempt a Fortitude save against your class DC or become "
          f"{link('fatigued', 'Fatigued')}: @Check[fortitude|against:class]."),
        action="action", actions=2, traits=["auditory", "concentrate"],
        img="icons/commodities/treasure/sceptre-jeweled-gold.webp"))

    docs.append(action_item(AC, "final-stand", "Final Stand",
        block("Frequency", "once per day (once per hour with Court's Legends)") +
        block("Trigger", "The follower would be reduced to 0 Hit Points but not immediately killed.") + HR +
        p("Your follower is so loyal to your cause that they fight to the finish. They avoid being knocked out and "
          f"remain at 1 Hit Point, and their {link('wounded', 'Wounded')} condition increases by 1."),
        action="free", frequency={"max": 1, "per": "day"}, category="defensive",
        img="icons/skills/wounds/injury-pain-body-orange.webp"))

    docs.append(action_item(AC, "heros-heart-guard", "Hero's Heart Guard",
        p("<em>Add this to your follower at 4th level (Court's Training, Court of Hero's Heart).</em>") +
        p("Your follower is taught to put the needs of others first in battle. Allies adjacent to the follower (a "
          f"5-foot aura) have lesser cover, a +1 circumstance bonus to AC ({link(uuid(EF, 'heros-heart-cover'))}). "
          "While guarding, the follower has resistance to physical damage equal to half its level. Turn off "
          "<em>Hero's Heart Guard</em> to drop the aura."),
        action="passive", category="defensive", img="icons/equipment/shield/heater-steel-worn.webp",
        rules=[
            toggle("heros-heart-guard", "Hero's Heart Guard", default=True),
            {"key": "Aura", "slug": "heros-heart-guard", "radius": 5, "traits": ["aura"],
             "predicate": ["heros-heart-guard"],
             "effects": [{"affects": "allies", "includesSelf": False,
                          "uuid": uuid(EF, "heros-heart-cover")}]},
            {"key": "Resistance", "type": "physical", "value": "max(1,floor(@actor.level/2))",
             "predicate": ["heros-heart-guard"]},
        ]))

    docs.append(action_item(AC, "accept-the-gambit", "Accept the Gambit",
        block("Trigger", "A creature attempts to Strike you while you are off-guard due to Queen's Gambit.") + HR +
        p(f"Your follower {link('Stride', 'Strides')} and {link('Strike', 'Strikes')} the triggering creature. If the "
          "creature failed its Strike, the follower gains a +1 circumstance bonus to their Strike; on a critical "
          "failure, a +2 circumstance bonus. The Strike deals additional precision damage equal to "
          "[[/r (floor(@actor.level/2))d6[precision]]] (1d6 per 2 of your levels)."),
        action="reaction", img="icons/skills/melee/maneuver-sword-katana-yellow.webp"))
    return docs


# ============================================================ EFFECTS used by features
def build_feature_effects():
    docs = []
    docs.append(effect(EF, "heros-heart-cover", "Effect: Hero's Heart Cover",
        p(f"Granted by a follower's {link(uuid(AC, 'heros-heart-guard'))} aura.") +
        p("You have lesser cover (+1 circumstance bonus to AC) while adjacent to the follower. The effect ends when "
          "you leave the aura."),
        rules=[{"key": "FlatModifier", "selector": "ac", "type": "circumstance", "value": 1,
                "label": "Lesser Cover (Hero's Heart)"}],
        duration=("unlimited", -1, None), img="icons/equipment/shield/heater-steel-worn.webp"))
    return docs


# ============================================================ REGALIA
REGALIA = ["armor", "scepter", "jewellery", "orb", "mirror", "weapon"]


def edicts(ed, an):
    return block("Edicts", ed) + block("Anathema", an)


def build_regalia():
    docs = []
    common_tags = ["sovereign-regalia"]

    docs.append(feat(CF, "regalia-armor", "Armor Regalia", 1,
        p("Your regalia is a suit of armor, crafted of the finest metals and emblazoned with symbols of your court. "
          "A sovereign who dons armor as their regalia shows that they are totally loyal to their court, and are "
          "willing to die for their people.") +
        edicts("Defend the people of your court with your life.", "Harm the people of your court.") +
        block("Regalia's Gift", "You are trained in heavy armor. When your proficiency for light and medium armor "
              "increases, your heavy armor proficiency increases too. While you are wearing heavy armor, you gain "
              "resistance to physical damage equal to half your level."),
        category="classfeature", traits=["sovereign"], other_tags=common_tags,
        img="icons/equipment/chest/breastplate-banded-steel-gold.webp",
        rules=[
            {"key": "ActiveEffectLike", "mode": "upgrade", "path": "system.proficiencies.defenses.heavy.rank",
             "value": "ternary(gte(@actor.level,17),3,ternary(gte(@actor.level,11),2,1))"},
            {"key": "Resistance", "type": "physical", "value": "floor(@actor.level/2)",
             "predicate": ["armor:category:heavy"]},
        ]))

    docs.append(feat(CF, "regalia-scepter", "Scepter Regalia", 1,
        p("A scepter is an ornamental rod topped with a finial that illustrates the ruler's ideals. It highlights a "
          "sovereign's capable leadership, tactical acumen and right to rule over their subjects.") +
        edicts("Make decisive choices that benefit your court.",
               "Put a decision off for being difficult on a personal level.") +
        block("Regalia's Gift", "While wielding your scepter, you gain greater control of your followers. When you "
              "issue a command to a follower, you can spend an extra action to give your follower an additional "
              "action. You can spend all three actions to give your follower four actions, though your follower must "
              "then make a Fortitude save against your class DC or become fatigued.") +
        p(f"You gain {link(uuid(AC, 'scepters-command'))}."),
        category="classfeature", traits=["sovereign"], other_tags=common_tags,
        img="icons/commodities/treasure/sceptre-jeweled-gold.webp",
        rules=[grant(uuid(AC, "scepters-command"))]))

    docs.append(feat(CF, "regalia-jewellery", "Jewellery Regalia", 1,
        p("Jewellery regalia can take many forms: a crown on one's head, rings on one's fingers, amulets or studded "
          "clothing. Jewellery that acts as regalia is often excessively ornate, made of unbelievably rare materials "
          "to highlight the total supremacy of its sovereign.") +
        edicts("Prove yourself absolutely superior to your foes.",
               "Give up on something because of your personal failures.") +
        block("Regalia's Gift", f"While you are wearing your jewellery, you gain the "
              f"{link(uuid(AC, 'sovereigns-grace'))} reaction."),
        category="classfeature", traits=["sovereign"], other_tags=common_tags,
        img="icons/commodities/treasure/crown-gold-satin-gems-red.webp",
        rules=[grant(uuid(AC, "sovereigns-grace"))]))

    docs.append(feat(CF, "regalia-orb", "Orb Regalia", 1,
        p("An orb is a golden sphere, crusted in gems and with a holy symbol atop it. It represents the world, with "
          "your deity reigning above it. A sovereign who wields an orb shows that their rulership is divinely "
          "ordained.") +
        edicts("Those of your deity.", "Those of your deity; allow a creature to besmirch the name of your deity.") +
        block("Regalia's Gift", f"You gain the {link('Domain Initiate')} cleric feat, using a domain of your deity. "
              "You can only cast domain spells while wielding the orb. While wielding the orb, you count as a divine "
              "spellcaster for the purposes of wands, staves or other magic items that cast divine spells. At 8th "
              f"level, you gain access to the {link('Advanced Domain')} cleric feat and can take it as a class feat. "
              "You use your class DC as your spell DC for domain spells.") +
        p("<em>Setup:</em> create a Focus spellcasting entry (divine, Charisma) for your domain spells; its DC "
          "should match your class DC."),
        category="classfeature", traits=["sovereign"], other_tags=common_tags,
        img="icons/skills/social/orb-gold-claw-yellow.webp",
        rules=[grant(PF["Domain Initiate"])]))

    docs.append(feat(CF, "regalia-mirror", "Mirror Regalia", 1,
        p("Common with obsidian mirrors in Arcadia or bronze mirrors in Tian Xia, a handheld mirror is often used by "
          "sovereigns to keep themselves humble. A mirror inspires self-reflection and wisdom.") +
        edicts("Take measured action that weighs out the good and evil of any outcome.",
               "Allow yourself to become vain and stop serving your own people.") +
        block("Regalia's Gift", "While wielding your mirror, you have a +2 circumstance bonus to saves against "
              "mental effects and resistance equal to half your level to mental and spirit damage. You are immune "
              "to the stupefied and confused conditions."),
        category="classfeature", traits=["sovereign"], other_tags=common_tags,
        img="icons/sundries/survival/mirror-plain.webp",
        rules=[
            toggle("mirror-regalia", "Wielding Mirror Regalia", default=True),
            {"key": "FlatModifier", "selector": "saving-throw", "type": "circumstance", "value": 2,
             "predicate": ["mirror-regalia", "item:trait:mental"], "label": "Mirror Regalia"},
            {"key": "Resistance", "type": ["mental", "spirit"], "value": "floor(@actor.level/2)",
             "predicate": ["mirror-regalia"]},
            {"key": "Immunity", "type": ["stupefied", "confused"], "predicate": ["mirror-regalia"]},
        ]))

    docs.append(feat(CF, "regalia-weapon", "Weapon Regalia", 1,
        p("A weapon is perhaps the simplest piece of regalia in terms of symbolism: no matter how ornate it is, it is "
          "a tool of war that shows that you are willing to slay others for your court.") +
        edicts("Execute those who pose a threat to your court when imprisoning them could lead to further danger.",
               "Flee from a fight you could reasonably win.") +
        block("Regalia's Gift", "Your weapon is more powerful than others of its kind. Increase its damage die size "
              "by one step, to a maximum of d12.") +
        p("<em>Setup:</em> you pick the weapon from your inventory when this feature is added. If you didn't own it "
          "yet, delete this feature and drag it back on from the Sovereign Class Features compendium."),
        category="classfeature", traits=["sovereign"], other_tags=common_tags,
        img="icons/weapons/swords/sword-guard-gold-red.webp",
        rules=[
            {"key": "ChoiceSet", "flag": "regaliaWeapon", "choices": {"ownedItems": True, "types": ["weapon"]},
             "prompt": "PF2E.SpecificRule.Prompt.Weapon", "allowNoSelection": True},
            {"key": "DamageDice", "selector": "strike-damage", "override": {"upgrade": True},
             "predicate": ["item:id:{item|flags.system.rulesSelections.regaliaWeapon}"]},
        ]))

    # The picker feature
    regalia_list = "".join(f"<li>{link(uuid(CF, 'regalia-' + r))}</li>" for r in REGALIA)
    docs.append(feat(CF, "regalia", "Regalia", 1,
        p("A lot can be learned of a sovereign and the way they rule depending on the regalia they carry. Choose a "
          "regalia. Your regalia is a physical object which defines your personal abilities as well as how you lead "
          "others. So long as you have your regalia on your person, you gain its effects.") +
        f"<ul>{regalia_list}</ul>",
        category="classfeature", traits=["sovereign"],
        img="icons/commodities/treasure/crown-gold-laurel-wreath.webp",
        rules=[
            {"key": "ChoiceSet", "flag": "regalia", "prompt": "Choose a regalia.",
             "choices": [{"value": uuid(CF, "regalia-" + r)} for r in REGALIA]},
            grant("{item|flags.system.rulesSelections.regalia}"),
        ]))
    return docs


# ============================================================ COURTS
def build_courts():
    docs = []
    cover = link(uuid(EF, "heros-heart-cover"))
    guard = link(uuid(AC, "heros-heart-guard"))
    stand = link(uuid(AC, "final-stand"))

    docs.append(feat(CF, "court-heros-heart", "The Court of Hero's Heart", 1,
        p("<em>Your court may not be powerful or large necessarily, but both you and its people aspire to fight for "
          "a better tomorrow.</em>") +
        block("Trained Skills", "Athletics or Acrobatics, Folktale Lore") +
        block("Court's Values (1st)", "Your court values heroism and bravery above all else. When your follower "
              f"reduces their {link('frightened', 'frightened')} condition, it reduces by 2 instead of 1. If you are "
              "adjacent to your follower, your frightened condition is reduced by 1 at the end of their turn.") +
        block("Court's Training (4th)", f"Your followers become experienced followers "
              f"({link('Experienced Advancement')}) and are taught to put the needs of others first in battle. Allies "
              "adjacent to your follower have lesser cover, and while giving cover this way, the follower gains "
              f"resistance to physical damage equal to half your level. Add {guard} to your follower.") +
        block("Court's Champion (8th)", f"Your followers become veteran followers "
              f"({link('Veteran Advancement')}) and gain {stand}.") +
        block("Court's Legends (14th)", f"Your followers become exceptional followers "
              f"({link('Exceptional Advancement')}). Final Stand can be used once "
              "per hour rather than once per day."),
        category="classfeature", traits=["sovereign"], other_tags=["sovereign-court"],
        img="icons/magic/holy/meditation-chi-focus-blue.webp",
        rules=[
            {"key": "ChoiceSet", "flag": "courtSkill", "prompt": "PF2E.SpecificRule.Prompt.Skill",
             "adjustName": False,
             "choices": [{"label": "PF2E.Skill.Athletics", "value": "athletics"},
                         {"label": "PF2E.Skill.Acrobatics", "value": "acrobatics"}]},
            {"key": "ActiveEffectLike", "mode": "upgrade",
             "path": "system.skills.{item|flags.system.rulesSelections.courtSkill}.rank", "value": 1},
            {"key": "ActiveEffectLike", "mode": "override", "path": "system.skills.folktale-lore",
             "value": {"attribute": "int", "label": "Folktale Lore", "rank": 1}},
            {"key": "RollOption", "option": "sovereign-court:heros-heart"},
        ]))

    docs.append(feat(CF, "court", "Sovereign's Court", 1,
        p("A sovereign is a ruler, and thus must have subjects to rule. Choose a sovereign's court. Your court "
          "represents the place from which you came: the politics of your home, how the people view you, and the "
          "benefits it has given you and your followers. As you grow higher in level, your court grows in power, "
          "and so do your followers.") +
        f"<ul><li>{link(uuid(CF, 'court-heros-heart'))}</li></ul>",
        category="classfeature", traits=["sovereign"],
        img="icons/environment/settlement/castle.webp",
        rules=[
            {"key": "ChoiceSet", "flag": "court", "prompt": "Choose a court.",
             "choices": [{"value": uuid(CF, "court-heros-heart")}]},
            grant("{item|flags.system.rulesSelections.court}"),
        ]))

    # Level milestones (text reminders that point back at the chosen court)
    docs.append(feat(CF, "courts-training", "Court's Training", 4,
        p("Your followers become experienced followers, and you gain your court's Court's Training benefit. Add "
          f"{link('Experienced Advancement')} to your follower.") +
        block("Hero's Heart", f"Allies adjacent to your follower have lesser cover, and the follower gains "
              f"physical resistance while guarding. Add {guard} to your follower."),
        category="classfeature", traits=["sovereign"], img="icons/skills/social/diplomacy-unity-alliance.webp"))
    docs.append(feat(CF, "courts-champion", "Court's Champion", 8,
        p("Your followers become veteran followers, and you gain your court's Court's Champion benefit. Add "
          f"{link('Veteran Advancement')} to your follower.") +
        block("Hero's Heart", f"Your followers gain {stand}. Drag it onto your follower."),
        category="classfeature", traits=["sovereign"], img="icons/skills/social/intimidation-impressing.webp"))
    docs.append(feat(CF, "courts-legends", "Court's Legends", 14,
        p("Your followers become exceptional followers, and you gain your court's Court's Legends benefit. Add "
          f"{link('Exceptional Advancement')} to your follower.") +
        block("Hero's Heart", "Final Stand can be used once per hour rather than once per day. Update the "
              "frequency on your follower's Final Stand."),
        category="classfeature", traits=["sovereign"], img="icons/magic/holy/angel-winged-humanoid-blue.webp"))
    return docs


# ============================================================ CORE FEATURES
def build_core_features():
    docs = []
    docs.append(feat(CF, "loyal-follower", "Loyal Follower", 1,
        p("You are always accompanied by a loyal follower, a retainer who has sworn to fight and die for your cause. "
          "They have the minion trait and begin as a novice follower.") +
        p(f"Use {link('Direct Follower')} to command your follower. Your follower's level equals yours, and their "
          "tier advances through your court's features at 4th, 8th and 14th level.") +
        p("<em>Setup (PF2e Companion Compendia):</em> create a character actor for your follower, add the "
          f"{link('Follower')} ancestry and one follower type: " +
          ", ".join(link(t) for t in FOLLOWER_TYPES) + "."),
        category="classfeature", traits=["sovereign"], img="icons/skills/social/diplomacy-handshake-yellow.webp",
        rules=[grant(PF["Direct Follower"])]))

    docs.append(feat(CF, "vast-coffers", "Vast Coffers", 1,
        p(f"As a sovereign, you have quite an amount of wealth to draw from. You can roll Society to "
          f"{link('Earn Income')} no matter where you are, as members of your court bring you gold from your "
          "treasury. You begin with double the starting gold a normal character begins play with."),
        category="classfeature", traits=["sovereign"], img="icons/commodities/currency/coins-assorted-mix-copper-silver-gold.webp"))

    docs.append(feat(CF, "martial-expertise", "Martial Expertise", 5,
        p("You've trained alongside your retainers to ensure that you are able to endure in combat. Your proficiency "
          "rank for martial weapons, simple weapons, and unarmed attacks increases to expert. When you critically "
          "succeed at an attack roll with a weapon you are at least an expert with, you apply the weapon's critical "
          "specialization effect."),
        category="classfeature", traits=["sovereign"], img="icons/skills/melee/hand-grip-sword-orange.webp",
        subfeatures={"proficiencies": {"martial": {"rank": 2}, "simple": {"rank": 2}, "unarmed": {"rank": 2}}},
        rules=[{"key": "CriticalSpecialization", "predicate": [{"gte": ["item:proficiency:rank", 2]}]}]))

    def classdc(key, name, level, rank, text, img):
        return feat(CF, key, name, level, p(text), category="classfeature", traits=["sovereign"], img=img,
                    rules=[{"key": "ActiveEffectLike", "mode": "upgrade",
                            "path": "system.proficiencies.classDCs.sovereign.rank", "value": rank}])

    docs.append(classdc("expert-leader", "Expert Leader", 7, 2,
        "Even while adventuring, you ensure that you are able to effectively guide your people. Your proficiency "
        "rank for your sovereign class DC increases to expert.", "icons/sundries/flags/banner-yellow.webp"))
    docs.append(classdc("master-ruler", "Master Ruler", 15, 3,
        "Legends are being written of your exploits with each passing day, earning your court a place in history. "
        "Your proficiency rank for your sovereign class DC increases to master.", "icons/sundries/flags/banner-purple.webp"))
    docs.append(classdc("legendary-ruler", "Legendary Ruler", 19, 4,
        "None can ever doubt your place at the head of your court. Your proficiency rank for your sovereign class "
        "DC increases to legendary.", "icons/sundries/flags/banner-pink.webp"))

    docs.append(feat(CF, "fortitude-expertise", "Fortitude Expertise", 9,
        p("Your physique has grown hardy in your adventures. Your proficiency rank for Fortitude saves increases to "
          "expert."),
        category="classfeature", traits=["sovereign"], img="icons/magic/life/cross-explosion-burst-green.webp",
        subfeatures={"proficiencies": {"fortitude": {"rank": 2}}}))

    medium_spec = [
        ("composite", "piercing", "1"), ("leather", "bludgeoning", "1"), ("plate", "slashing", "1"),
        ("skeletal", "precision", "3"), ("chain", "critical-hits", "4"),
    ]
    docs.append(feat(CF, "armor-expertise", "Armor Expertise", 11,
        p("You have spent so much time in armor that you know how to make the most of its protection. Your "
          "proficiency ranks for light and medium armor, as well as for unarmored defense, increase to expert. You "
          "gain the armor specialization effects of medium armor."),
        category="classfeature", traits=["sovereign"], img="icons/equipment/chest/breastplate-banded-steel-gold.webp",
        subfeatures={"proficiencies": {"light": {"rank": 2}, "medium": {"rank": 2}, "unarmored": {"rank": 2}}},
        rules=[{"key": "Resistance", "type": t, "value": f"{v} + @armor.system.runes.potency",
                "predicate": ["armor:category:medium", f"armor:group:{g}"]} for g, t, v in medium_spec]))

    docs.append(feat(CF, "rulers-resolve", "Ruler's Resolve", 11,
        p("You show control and grace in the face of adversity. Your proficiency rank for Will saves increases to "
          "master. When you roll a success on a Will save, you get a critical success instead."),
        category="classfeature", traits=["sovereign"], img="icons/magic/control/silhouette-hold-change-blue.webp",
        subfeatures={"proficiencies": {"will": {"rank": 3}}},
        rules=[{"key": "AdjustDegreeOfSuccess", "selector": "will",
                "adjustment": {"success": "to-critical-success"}}]))

    docs.append(feat(CF, "perception-mastery", "Perception Mastery", 13,
        p("You have a naturally discerning eye. Your proficiency rank for Perception increases to master."),
        category="classfeature", traits=["sovereign"], img="icons/magic/perception/eye-tendrils-web-purple.webp",
        subfeatures={"proficiencies": {"perception": {"rank": 3}}}))

    docs.append(feat(CF, "weapon-mastery", "Weapon Mastery", 13,
        p("Your weapon is an extension of yourself, and therefore an extension of your court. Your proficiency ranks "
          "for unarmed attacks, simple weapons, and martial weapons increase to master."),
        category="classfeature", traits=["sovereign"], img="icons/skills/melee/blade-tip-chipped-blood-red.webp",
        subfeatures={"proficiencies": {"martial": {"rank": 3}, "simple": {"rank": 3}, "unarmed": {"rank": 3}}}))

    docs.append(feat(CF, "graceful-mastery", "Graceful Mastery", 15,
        p("You cannot afford to look oafish or clumsy, and have learned to be quick on your feet. Your proficiency "
          "rank for Reflex saves increases to master. When you roll a success on a Reflex save, you get a critical "
          "success instead."),
        category="classfeature", traits=["sovereign"], img="icons/skills/movement/arrow-upward-yellow.webp",
        subfeatures={"proficiencies": {"reflex": {"rank": 3}}},
        rules=[{"key": "AdjustDegreeOfSuccess", "selector": "reflex",
                "adjustment": {"success": "to-critical-success"}}]))

    docs.append(feat(CF, "armor-mastery", "Armor Mastery", 17,
        p("Your armor protects your heart, and the heart of your people. Your proficiency ranks for light and medium "
          "armor, as well as for unarmored defense, increase to master."),
        category="classfeature", traits=["sovereign"], img="icons/equipment/chest/breastplate-banded-steel-gold.webp",
        subfeatures={"proficiencies": {"light": {"rank": 3}, "medium": {"rank": 3}, "unarmored": {"rank": 3}}}))
    return docs


# ============================================================ CLASS ITEM
def build_class():
    entries = [
        (1, "loyal-follower"), (1, "regalia"), (1, "court"), (1, "vast-coffers"),
        (4, "courts-training"), (5, "martial-expertise"), (7, "expert-leader"),
        (8, "courts-champion"), (9, "fortitude-expertise"), (11, "armor-expertise"), (11, "rulers-resolve"),
        (13, "perception-mastery"), (13, "weapon-mastery"), (14, "courts-legends"), (15, "graceful-mastery"),
        (15, "master-ruler"), (17, "armor-mastery"), (19, "legendary-ruler"),
    ]
    names = {d["system"]["slug"]: d for d in build_core_features() + build_regalia() + build_courts()}
    by_key = {}
    for d in build_core_features() + build_regalia() + build_courts():
        by_key[d["_id"]] = d
    items = {}
    for lvl, key in entries:
        u = cf_uuid(key)
        d = by_key[u.split(".")[-1]]
        items[mkid("classitems:" + key)[:5]] = {"img": d["img"], "level": lvl, "name": d["name"], "uuid": u}
    items[mkid("classitems:weapon-spec")[:5]] = {
        "img": "systems/pf2e/icons/features/classes/weapon-specialization.webp", "level": 7,
        "name": "Weapon Specialization", "uuid": PF["Weapon Specialization"]}
    items[mkid("classitems:greater-weapon-spec")[:5]] = {
        "img": "icons/skills/melee/hand-grip-sword-orange.webp", "level": 15,
        "name": "Greater Weapon Specialization", "uuid": PF["Greater Weapon Specialization"]}

    desc = (
        p("<em>Whether crowned by birth, chosen by the people, or simply the one others turn to when hard decisions "
          "must be made, you lead. Your regalia marks the kind of ruler you are, your court shapes the people who "
          "follow you, and your loyal follower fights at your side.</em>") +
        block("Key Attribute", "Charisma") + block("Hit Points", "8 plus your Constitution modifier") +
        HR +
        "<h2>Initial Proficiencies</h2>" +
        block("Perception", "Expert") +
        block("Saving Throws", "Trained in Fortitude, expert in Reflex, expert in Will") +
        block("Skills", "Trained in Society and 2 skills defined by your sovereign's court; trained in a number of "
              "additional skills equal to 2 plus your Intelligence modifier") +
        block("Attacks", "Trained in simple weapons, martial weapons, and unarmed attacks") +
        block("Defenses", "Trained in light and medium armor and unarmored defense") +
        block("Class DC", "Trained in sovereign class DC") +
        HR +
        "<h2>Sidebar: A Ruler By Any Other Name</h2>" +
        p("The sovereign's story does not have to be about kings, queens, or inherited power. A sovereign might "
          "instead be an elected ruler, the leader of a church, a revolutionary organizer, or simply the person "
          "others trust when difficult decisions must be made. Their authority comes from service, competence, "
          "responsibility, or the confidence of their people. The fantasy is not that they were born to lead; it is "
          "that they chose to.")
    )
    _id = mkid("classes:sovereign")
    return {
        "_id": _id, "_key": f"!items!{_id}", "name": "Sovereign", "type": "class",
        "img": icon("icons/commodities/treasure/crown-gold-laurel-wreath.webp"),
        "folder": None, "sort": 0, "flags": {}, "effects": [], "_stats": dict(STATS),
        "system": {
            "ancestryFeatLevels": {"value": [1, 5, 9, 13, 17]},
            "attacks": {"advanced": 0, "martial": 1, "other": {"name": "", "rank": 0}, "simple": 1, "unarmed": 1},
            "classFeatLevels": {"value": [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]},
            "defenses": {"heavy": 0, "light": 1, "medium": 1, "unarmored": 1},
            "description": {"value": desc},
            "generalFeatLevels": {"value": [3, 7, 11, 15, 19]},
            "hp": 8,
            "items": items,
            "keyAbility": {"selected": None, "value": ["cha"]},
            "perception": 2,
            "publication": dict(PUB),
            "rules": [],
            "savingThrows": {"fortitude": 1, "reflex": 2, "will": 2},
            "skillFeatLevels": {"value": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]},
            "skillIncreaseLevels": {"value": [3, 5, 7, 9, 11, 13, 15, 17, 19]},
            "spellcasting": 0,
            "trainedSkills": {"additional": 2, "value": ["society"]},
            "traits": {"rarity": "rare", "value": []},
            "slug": "sovereign",
            "_migration": dict(MIG),
        },
    }


def build_all():
    return {
        "classes": [build_class()],
        "class-features": build_core_features() + build_regalia() + build_courts(),
        "actions": build_actions(),
        "effects": build_feature_effects(),
    }
