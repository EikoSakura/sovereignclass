"""Summons Unleashed homebrew: the Convoker summoner class archetype and eight new eidolons.

Two packs:
  summons-unleashed  the summoner's side: Convoker features, feats and focus spells, the new eidolon
                     choices (tagged summoner-eidolon so the pf2e Eidolon class feature offers them), and effects.
  su-eidolons        the eidolon actor's side, modeled on PF2e Companion Compendia's AC-Eidolons pack: one
                     ancestry per eidolon, its Strength/Dexterity key-attribute builds, and its initial,
                     symbiosis and transcendence abilities.
"""
from common import HR, MIG, _base, action_item, block, effect, feat, p, slugify, uuid

SU = "summons-unleashed"
EI = "su-eidolons"
PUB = {"license": "ORC", "remaster": True, "title": "Summons Unleashed"}

CC = "Compendium.pf2e-animal-companions.AC-Features.Item."
CC_EIDOLON_CLASS = CC + "xPn27nNxcLOByTXJ"
CC_EIDOLON_ABILITY = CC + "5E71mdImeRE9Fh1D"

SPELL = {
    "evolution surge": "Compendium.pf2e.spells-srd.Item.lV8FkHZtzZu7Cy6j",
    "boost eidolon": "Compendium.pf2e.spells-srd.Item.HStu2Yhw3iQER9tY",
    "dominate": "Compendium.pf2e.spells-srd.Item.OsOhx3TGIZ7AhD0P",
    "execute": "Compendium.pf2e.spells-srd.Item.Z9OrRXKgAPv6Hn5l",
    "regenerate": "Compendium.pf2e.spells-srd.Item.2Vkd1IxylPceUAAF",
    "truespeech": "Compendium.pf2e.spells-srd.Item.SwUiVavHKMWG7t5K",
    "clairaudience": "Compendium.pf2e.spells-srd.Item.HXhWYJviWalN5tQ2",
    "clairvoyance": "Compendium.pf2e.spells-srd.Item.zvKWclOZ7A53DObE",
    "slow": "Compendium.pf2e.spells-srd.Item.WsUwpfmhKrKwoIe3",
}
ACTION = {
    "Manifest Eidolon": "Compendium.pf2e.actionspf2e.Item.n5vwBnLSlIXL9ptp",
    "Change Shape": "Compendium.pf2e.actionspf2e.Item.34E7k2YRcsOU5uyl",
    "Recall Knowledge": "Compendium.pf2e.actionspf2e.Item.1OagaWtBpVXExToo",
    "Stride": "Compendium.pf2e.actionspf2e.Item.Bcxarzksqt9ezrs6",
    "Strike": "Compendium.pf2e.actionspf2e.Item.VjxZFuUXrCU94MWR",
}
COND = {
    "blinded": "Compendium.pf2e.conditionitems.Item.XgEqL1kFApUbl5Z2",
    "dazzled": "Compendium.pf2e.conditionitems.Item.TkIyaNPgTZFBCCuh",
    "stunned": "Compendium.pf2e.conditionitems.Item.dfCMdR4wnpbYNTix",
    "frightened": "Compendium.pf2e.conditionitems.Item.TBSHQspnbcqxsmjL",
    "off-guard": "Compendium.pf2e.conditionitems.Item.AJh5ex99aV6VTggg",
    "sickened": "Compendium.pf2e.conditionitems.Item.fesd1n5eVhpCSS18",
    "stupefied": "Compendium.pf2e.conditionitems.Item.e1XGnhKNSQIm5IXg",
    "quickened": "Compendium.pf2e.conditionitems.Item.nlCjDvLMf2EkV2dl",
    "slowed": "Compendium.pf2e.conditionitems.Item.xYTAsEpcJE1Ccni3",
    "grabbed": "Compendium.pf2e.conditionitems.Item.kWc1fhmv9LBiTuei",
    "restrained": "Compendium.pf2e.conditionitems.Item.VcDeM8A5oI6VqhbM",
    "concealed": "Compendium.pf2e.conditionitems.Item.DmAIPqOBomZ7H95W",
    "undetected": "Compendium.pf2e.conditionitems.Item.VRSef5y1LmL2Hkjf",
}

SKILLS = ["acrobatics", "arcana", "athletics", "crafting", "deception", "diplomacy", "intimidation", "medicine",
          "nature", "occultism", "performance", "religion", "society", "stealth", "survival", "thievery"]
TRADITION_SKILL = {"arcane": "arcana", "divine": "religion", "occult": "occultism", "primal": "nature"}

EIDOLON_IMG = "systems/pf2e/icons/features/classes/eidolon.webp"
SYMBIOSIS_IMG = "systems/pf2e/icons/features/classes/eidolon-symbiosis.webp"
TRANSCEND_IMG = "systems/pf2e/icons/features/classes/eidolon-transcendence.webp"
CONVOKER_IMG = "icons/magic/symbols/runes-star-pentagon-blue.webp"


def L(u, label):
    return f"@UUID[{u}]{{{label}}}"


def sp(name, label=None):
    return f"<em>{L(SPELL[name], label or name)}</em>"


def cond(name, label=None):
    return L(COND[name], label or name.capitalize())


def tmpl(kind, dist):
    return f"@Template[type:{kind}|distance:{dist}]"


def degrees(cs, s, f, cf):
    return (f"<p><strong>Critical Success</strong> {cs}</p><p><strong>Success</strong> {s}</p>"
            f"<p><strong>Failure</strong> {f}</p><p><strong>Critical Failure</strong> {cf}</p>")


def pub(doc):
    doc["system"]["publication"] = dict(PUB)
    return doc


def skill_label(s):
    return f"PF2E.Skill.{s.capitalize()}"


def lore_skill(slug, label, rank=1, attribute="int"):
    return {"key": "ActiveEffectLike", "mode": "override", "path": f"system.skills.{slug}",
            "value": {"attribute": attribute, "label": label, "rank": rank}}


def skill_rank(skill, rank=1):
    return {"key": "ActiveEffectLike", "mode": "upgrade", "path": f"system.skills.{skill}.rank", "value": rank}


def spell(key, name, rank, desc, *, time, traits, range_="", target="", area=None, duration="",
          defense=None, img, rarity="uncommon"):
    system = {
        "area": area,
        "cost": {"value": ""},
        "counteraction": False,
        "damage": {},
        "defense": defense,
        "description": {"value": desc},
        "duration": {"sustained": False, "value": duration},
        "level": {"value": rank},
        "publication": dict(PUB),
        "range": {"value": range_},
        "requirements": "",
        "rules": [],
        "target": {"value": target},
        "time": {"value": time},
        "traits": {"rarity": rarity, "traditions": [], "value": list(traits)},
        "slug": slugify(name),
        "_migration": dict(MIG),
    }
    return _base(SU, key, name, "spell", img, system)


# =====================================================================================================================
# Eidolon data
# =====================================================================================================================
# Each entry: summoner-side text + rules data, eidolon-side ancestry data, and its three abilities.
# Ability tuples: (name, action, actions, traits, frequency, desc, rules, extra)
EIDOLONS = []


def eidolon(**kw):
    EIDOLONS.append(kw)


def _abilities():
    """Defined in a function so the uuid() helper resolves keys consistently."""
    E = {}

    # ---------------------------------------------------------------- Coatl
    serpent_hope_eff = uuid(SU, "effect-serpent-hope")
    E["coatl"] = dict(
        name="Coatl", tradition="divine", img="icons/creatures/reptiles/serpent-horned-green.webp",
        flavor="Your eidolon is a sacred feathered serpent. Coatl eidolon can resemble all manner of coatl, though "
               "a majestic skybound serpent covered in radiant plumage is the most common. A bond with a coatl comes "
               "most often when a coatl has already chosen to guide and defend the settlement the summoner resides.",
        traits=["beast", "coatl", "eidolon", "holy"], home="the Universe", sizes=("med", "sm"),
        attacks="coil (bludgeoning), wings (bludgeoning), jaws (piercing)",
        attrs={"con": 1, "int": 0, "wis": 1, "cha": 1}, skills=["diplomacy", "religion"],
        senses="darkvision", vision="darkvision", language=None, language_text="one common language",
        speed=15, speed_text="15 feet; fly 20 feet", other_speeds=[("fly", 20)],
        initial=("Skybound Serpent", "passive", None, [], None,
                 p("When flying due to the eidolon's innate fly speed, it must begin and end its movement on a solid "
                   "surface or immediately fall. If it gains another fly speed, increase that fly speed by 10 feet. "
                   "Additionally, your eidolon's unarmed Strikes gain the holy trait."),
                 [{"key": "AdjustStrike", "mode": "add", "property": "traits", "value": "holy",
                   "definition": ["item:category:unarmed"]}], {}),
        symbiosis=("Radiant Wings", "action", 2, ["divine", "eidolon", "light", "mental", "visual"],
                   {"max": 1, "per": "PT10M"},
                   p(f"Your eidolon unfurls its radiant wings in a grand display. Each creature in a "
                     f"{tmpl('emanation', 30)} must attempt a @Check[will|against:class|options:area-effect] save "
                     f"against your class DC.")
                   + degrees("The creature is unaffected.",
                             f"The creature is {cond('dazzled')} for 1 round.",
                             f"The creature is {cond('blinded')} for 1 round, and dazzled for 1 minute. If the "
                             f"creature was unholy, the creature is also {cond('stunned', 'Stunned 1')}.",
                             "The creature is blinded for 1 round, dazzled for 1 minute, and stunned 1. If the "
                             "creature was unholy, the creature is stunned 2."),
                   [], {}),
        transcendence=("Serpent Hope", "passive", None, ["aura", "divine"], None,
                       p(f"Your eidolon is surrounded by an aura of hope in a {tmpl('emanation', 30)}. It has the "
                         f"aura and divine traits. Whenever your eidolon becomes {cond('frightened')}, reduce the "
                         "condition value by 1 (to a minimum of 0). At the end of your turn, each ally in the "
                         "eidolon's aura reduces its frightened value by 1. Allies within your eidolon's aura gain a "
                         "+2 status bonus to saves against fear and unholy effects and are immune to the effects of "
                         "your eidolon's Radiant Wings.",
                         f"Allies in the aura receive {L(serpent_hope_eff, 'Effect: Serpent Hope')} automatically."),
                       [{"key": "Aura", "slug": "serpent-hope", "radius": 30, "traits": ["aura", "divine"],
                         "effects": [{"uuid": serpent_hope_eff, "affects": "allies", "includesSelf": False}]}], {}),
    )

    # ---------------------------------------------------------------- Kami
    kami_ward_eff = uuid(SU, "effect-kami-ward")
    warded_regen_eff = uuid(SU, "effect-warded-regeneration")
    E["kami"] = dict(
        name="Kami", tradition="primal", img="icons/magic/nature/leaf-glow-teal.webp",
        flavor="Your eidolon is a spirit bound to the land. A kami eidolon's appearance is as varied as the spirits "
               "are, and can appear as humanoids, animals, objects, and many other forms. While most kami choose to "
               "ward a specific place, you've earned the favor of these spirits enough to harness this bond.",
        traits=["eidolon", "kami", "spirit"], home="the Universe", sizes=("med", "sm"),
        attacks="fist (bludgeoning), spade (slashing), staff (bludgeoning), katana (slashing)",
        attrs={"con": 1, "int": -1, "wis": 3, "cha": 0}, skills=["nature", "religion"],
        senses="low-light vision", vision="low-light-vision", language=None, language_text="one common language",
        speed=25, speed_text="25 feet", other_speeds=[],
        initial=("Kami Ward", "action", 1, ["eidolon"], None,
                 p("Your eidolon can spend a single action to gain a +1 circumstance bonus to AC and saving throws "
                   "until the start of its next turn, and you gain this bonus so long as you are adjacent to your "
                   "eidolon. This bonus increases to +2 against unholy effects or effects originating from unholy "
                   "creatures.",
                   f"Using this action applies {L(kami_ward_eff, 'Effect: Kami Ward')} to the eidolon. While its "
                   "summoner's token is adjacent, the summoner gets the same effect automatically, and loses it when "
                   "they move apart or the ward ends."),
                 [], {"selfEffect": {"name": "Effect: Kami Ward", "uuid": kami_ward_eff}}),
        symbiosis=("Warded Regeneration", "action", 1, ["eidolon", "healing", "primal", "vitality"],
                   {"max": 1, "per": "PT10M"},
                   p("Your eidolon can enter you as its ward to bolster your health. You regain "
                     "@Damage[(4+floor((@actor.level-7)/2))d8[healing]] Hit Points and gain a +1 status bonus to "
                     f"your AC for 1 minute ({L(warded_regen_eff, 'Effect: Warded Regeneration')}), and then your "
                     f"eidolon unmanifests. After using Warded Regeneration, you can "
                     f"{L(ACTION['Manifest Eidolon'], 'Manifest Eidolon')} as a single action until the end of your "
                     "next turn. At 9th level and every 2 levels thereafter, the healing increases by 1d8. If your "
                     "eidolon has an active Kami Ward, you gain the benefits of that action as if your eidolon was "
                     "adjacent to you until the start of your next turn."),
                   [], {}),
        transcendence=("Bloom and Wilt", "passive", None, [], None,
                       p(f"Your kami empowers the life around it or saps at it. They can cast either "
                         f"{sp('execute')} or {sp('regenerate')} once per day as a 9th-rank divine innate spell. At "
                         "19th level, the spell becomes 10th-rank instead."),
                       [], {}),
    )

    # ---------------------------------------------------------------- Mycological
    E["mycological"] = dict(
        name="Mycological", tradition="primal", img="icons/consumables/mushrooms/mushroom-spotted-red.webp",
        flavor="Your eidolon is a vitae inhabiting the form of a fungus. These eidolons are as varied as the many "
               "fungi on the world and beyond. Though others may have trouble relating to the strange nature of your "
               "eidolon, your ability to share senses with your eidolon has given you a unique outlook on life.",
        traits=["eidolon", "fungus"], home="the Universe", sizes=("med", "sm"),
        attacks="spore pod (bludgeoning), claw (slashing), jaw (piercing)",
        attrs={"con": 2, "int": -1, "wis": 2, "cha": 0}, skills=["nature", "survival"],
        senses="darkvision", vision="darkvision", language="fey", language_text="Fey",
        speed=20, speed_text="20 feet", other_speeds=[],
        initial=("Fungal Hyphae", "passive", None, [], None,
                 p("Your eidolon has an imprecise tremorsense with a range of 30 feet and they gain a +2 circumstance "
                   "bonus to saving throws against poison and disease effects."),
                 [{"key": "Sense", "selector": "tremorsense", "acuity": "imprecise", "range": 30},
                  {"key": "FlatModifier", "selector": "saving-throw", "type": "circumstance", "value": 2,
                   "predicate": [{"or": ["poison", "disease"]}]}], {}),
        symbiosis=("Release Spores", "action", 2, ["eidolon", "fungus", "poison", "primal"],
                   {"max": 1, "per": "PT10M"},
                   p(f"Your eidolon releases a cloud of spores in a {tmpl('emanation', 15)}. Creatures in the area "
                     "take @Damage[(6+@actor.level-7)d4[poison]|options:area-damage] damage with a "
                     "@Check[fortitude|against:spell|options:area-effect] save against your spell DC. The damage "
                     "increases by 1d4 for each level you have beyond 7th.")
                   + degrees("The creature is unaffected.", "The creature takes half damage.",
                             f"The creature takes full damage and is {cond('sickened', 'Sickened 1')}.",
                             "The creature takes double damage and is sickened 2."),
                   [], {}),
        transcendence=("Fungal Domination", "action", 2, ["eidolon", "fungus", "incapacitation", "primal"],
                       {"max": 1, "per": "day"},
                       p("Your eidolon releases spores that invade the body of a creature within 30 feet. That "
                         "creature attempts a @Check[fortitude|against:spell] saving throw against your spell DC "
                         f"with the effects of {sp('dominate')} based on the results of its saving throw."),
                       [], {}),
    )

    # ---------------------------------------------------------------- Program (SF2e)
    E["program"] = dict(
        name="Program", tradition="arcane", img="icons/skills/trades/electronics-tech-circuit-blue.webp",
        flavor="Your eidolon is a digital interface given form. It may resemble a virtual pet, a video game "
               "character, a digital assistant, or any other form that exists within your holopad. Given form, your "
               "eidolon most resembles hardlight constructs and can similarly adept at causing interference with "
               "other tech beings.",
        traits=["construct", "eidolon", "tech"], home="the Universe", sizes=("med", "sm"),
        attacks="sword (slashing), jaws (piercing), advert (bludgeoning)",
        attrs={"con": 1, "int": 2, "wis": -1, "cha": 1}, skills=["arcana"], extra_skills=["Computers"],
        senses="darkvision", vision="darkvision", language=None, language_text="one common language",
        speed=25, speed_text="25 feet", other_speeds=[], sf2e=True,
        initial=("Digital Form", "passive", None, [], None,
                 p("Your eidolon's digital form is materialized, but retains a connection to digital wavelengths. "
                   "Your eidolon's unarmed attacks gain the versatile force trait. Additionally, when it critically "
                   "succeeds a Strike against a creature or hazard with the tech trait or a creature that wields or "
                   "wears a tech item, the target or one required tech item of your choice becomes Glitching 1."),
                 [{"key": "AdjustStrike", "mode": "add", "property": "traits", "value": "versatile-force",
                   "definition": ["item:category:unarmed"]},
                  {"key": "Note", "selector": "strike-attack-roll", "outcome": ["criticalSuccess"],
                   "title": "{item|name}",
                   "predicate": [{"or": ["target:trait:tech", "target:item:trait:tech"]}],
                   "text": "The target, or one required tech item of your choice, becomes Glitching 1."}], {}),
        symbiosis=("Digitized Countermeasures", "passive", None, ["aura", "eidolon", "visual"], None,
                   p("Your eidolon creates visible digitized signals on all creatures nearby. Your eidolon gains a "
                     f"digitized aura in a {tmpl('emanation', 30)}. Visible creatures in the aura can't be "
                     f"{cond('concealed')}, and invisible creatures are concealed rather than "
                     f"{cond('undetected')}. Your eidolon can disable these countermeasures by spending a single "
                     "action, which has the concentrate trait and they can take this action again to reinstate "
                     "their aura.",
                     "Use the toggle on the eidolon's sheet to switch the aura on or off."),
                   [{"key": "RollOption", "domain": "all", "option": "digitized-countermeasures",
                     "toggleable": True, "value": True, "label": "Digitized Countermeasures"},
                    {"key": "Aura", "slug": "digitized-countermeasures", "radius": 30,
                     "traits": ["aura", "visual"], "predicate": ["digitized-countermeasures"]}], {}),
        transcendence=("Technomatic Mastery", "passive", None, [], None,
                       p("Your eidolon can cast <em>read memory</em>, <em>holographic stand-in</em>, and "
                         "<em>overload systems</em> once per day each as 9th-rank arcane innate spells."),
                       [], {}),
    )

    # ---------------------------------------------------------------- Rakshasa
    malefic_eff = uuid(SU, "effect-malefic-consumption")
    E["rakshasa"] = dict(
        name="Rakshasa", tradition="divine", img="icons/equipment/head/mask-tiger-silver.webp",
        flavor="Your eidolon is a spirit charged with being an incarnation of all that is foul. Though these spirits "
               "seem to delight in atrocity, it's simply the rakshasa's role in the world rather than out of innate "
               "personal malice. Summoners bonded to rakshasa eidolons walk a tight line, as some rakshasa are bound "
               "to their maleficent role despite personal conscience finding freedom in this bond, while others seek "
               "to subvert and corrupt their summoner.",
        traits=["eidolon", "rakshasa", "spirit", "unholy"], home="the Universe", sizes=("med", "sm"),
        attacks="taravati (slashing), fangs (piercing), fist (bludgeoning)",
        attrs={"con": 2, "int": -1, "wis": 0, "cha": 2}, skills=["deception", "religion"],
        senses="darkvision", vision="darkvision", language=None, language_text="one common language",
        speed=25, speed_text="25 feet", other_speeds=[],
        initial=("Hidden Malice", "passive", None, [], None,
                 p("Your eidolon's unarmed Strikes gain the unholy trait. Your eidolon gains the Change Shape "
                   "summoner feat (<em>Summoners+</em> pg 17), despite not meeting the prerequisite level.",
                   f"The eidolon is granted the {L(ACTION['Change Shape'], 'Change Shape')} action as a stand-in; "
                   "use the Summoners+ feat's details for its forms."),
                 [{"key": "AdjustStrike", "mode": "add", "property": "traits", "value": "unholy",
                   "definition": ["item:category:unarmed"]},
                  {"key": "GrantItem", "uuid": ACTION["Change Shape"], "allowDuplicate": False}], {}),
        symbiosis=("Malice Incarnate", "action", 2, ["concentrate", "divine", "eidolon", "unholy"],
                   {"max": 1, "per": "PT1H"},
                   p("Your eidolon prepares itself to exemplify some ancient profane edict. It gains one of the "
                     "following effects depending on its current shape, which gives Malice Incarnate additional "
                     "traits:")
                   + "<ul><li><p><strong>Cruel Majesty</strong> (mental, visual) <strong>Requirements</strong> your "
                     "eidolon is not in its true shape; <strong>Effect</strong> Your eidolon Changes Shape into its "
                     "true form in a display that is equal parts terrifying and majestic. Creatures within 30 feet "
                     "of your eidolon must attempt a @Check[will|against:spell] save against your spell DC.</p>"
                   + degrees("The creature is unaffected.",
                             f"The creature is {cond('off-guard', 'Off-Guard')} against your eidolon's next Strike "
                             "before the end of your turn.",
                             f"The creature is off-guard for 1 round and {cond('frightened', 'Frightened 1')}.",
                             "As failure except the creature is frightened 2.")
                   + "</li><li><p><strong>Malefic Consumption</strong> (morph) <strong>Requirements</strong> your "
                     "eidolon is in its true form; <strong>Effect</strong> For 1 minute, your eidolon can use the "
                     f"Swallow Whole ability on creatures of its size or smaller that it has {cond('grabbed')} or "
                     f"{cond('restrained')}. A swallowed creature takes "
                     "@Damage[(4+floor((@actor.level-7)/2))d6[bludgeoning]] damage and the eidolon has a rupture "
                     "value of [[/r 17+3*floor((@actor.level-7)/2)]]. At 9th level and every two levels thereafter, "
                     f"increase the bludgeoning damage by 1d6 and the rupture value by 3. "
                     f"({L(malefic_eff, 'Effect: Malefic Consumption')})</p></li></ul>",
                   [], {}),
        transcendence=("Exemplify the Profane", "action", 2, ["divine", "eidolon", "unholy"], None,
                       p(f"The eidolon carves into their foe in a gruesome display. The eidolon makes a "
                         f"{L(ACTION['Strike'], 'Strike')}. The Strike deals "
                         "@Damage[(@actor.level)[persistent,bleed]] damage and each enemy within 15 feet of the "
                         "target must succeed at a @Check[fortitude|against:spell] save against your spell DC or "
                         f"become {cond('sickened', 'Sickened 1')} (sickened 2 on a critical failure). Creatures "
                         "that succeed their save are immune to further attempts to sicken them from Exemplify the "
                         "Profane."),
                       [], {}),
    )

    # ---------------------------------------------------------------- Saboteur
    skill_choice = {"key": "ChoiceSet", "prompt": "PF2E.SpecificRule.Prompt.Skill", "adjustName": True,
                    "choices": [{"label": skill_label(s), "value": s} for s in SKILLS]}
    E["saboteur"] = dict(
        name="Saboteur", tradition="arcane", img="icons/creatures/magical/spirit-undead-masked-blue.webp",
        flavor="Your eidolon is the spirit of an ancient trickster of great prowess, their deeds given form in the "
               "astral through arcane magic. This phantom might be an ancient ancestor, echoes of a noble thief from "
               "a great legend, or perhaps something you envisioned once in an astral daydream.",
        traits=["eidolon", "phantom", "spirit"], home="any plane, commonly Astral", sizes=("med", "sm"),
        attacks="dagger (piercing), fighting fan (slashing), sword-cane sheath (bludgeoning)",
        attrs={"con": 0, "int": 1, "wis": 1, "cha": 1}, skills=["arcana", "stealth"],
        senses="low-light vision", vision="low-light-vision", language=None, language_text="one common language",
        speed=25, speed_text="25 feet", other_speeds=[],
        initial=("Expert Lessons", "passive", None, [], None,
                 p("Your eidolon gains a 1st-level skill feat. At second level, your eidolon increases their "
                   "proficiency rank in one of their skills from trained to expert.",
                   "Choose the skill when this ability is granted; it becomes expert at 2nd level. Add the skill "
                   "feat to the eidolon by hand."),
                 [dict(skill_choice, flag="expertLessons"),
                  {"key": "ActiveEffectLike", "mode": "upgrade",
                   "path": "system.skills.{item|flags.system.rulesSelections.expertLessons}.rank",
                   "value": "ternary(gte(@actor.level,2),2,1)"}], {}),
        symbiosis=("Masterful Saboteur", "passive", None, [], None,
                   p("Your eidolon increases their proficiency rank in one of their skills from expert to master and "
                     "gains a 7th-level skill feat for the chosen skill. While a creature is off-guard to your "
                     "eidolon, that creature also takes a -1 circumstance penalty to saving throws against your "
                     "spells."),
                   [dict(skill_choice, flag="masterfulSaboteur"),
                    {"key": "ActiveEffectLike", "mode": "upgrade",
                     "path": "system.skills.{item|flags.system.rulesSelections.masterfulSaboteur}.rank", "value": 3}],
                   {}),
        transcendence=("Legendary Debilitator", "passive", None, [], None,
                       p("Your eidolon increases their proficiency rank in one of their skills from master to "
                         "legendary and gains a 15th-level skill feat for the chosen skill. When your eidolon Strikes "
                         f"and deals damage to an off-guard creature, the target becomes "
                         f"{cond('stupefied', 'Stupefied 1')} until the end of your next turn."),
                       [dict(skill_choice, flag="legendaryDebilitator"),
                        {"key": "ActiveEffectLike", "mode": "upgrade",
                         "path": "system.skills.{item|flags.system.rulesSelections.legendaryDebilitator}.rank",
                         "value": 4},
                        {"key": "Note", "selector": "strike-damage", "title": "{item|name}",
                         "predicate": ["target:condition:off-guard"],
                         "text": "If this Strike deals damage, the target becomes stupefied 1 until the end of "
                                 "your next turn."}], {}),
    )

    # ---------------------------------------------------------------- Sphinx
    bk_s = uuid(SU, "effect-befuddling-knowledge-success")
    bk_f = uuid(SU, "effect-befuddling-knowledge-failure")
    E["sphinx"] = dict(
        name="Sphinx", tradition="occult", img="icons/commodities/materials/feather-white-glowing-beams.webp",
        flavor="Your eidolon is a mystical beast steeped in knowledge. These eidolons most often resemble the form "
               "of a lion with the wings of a mighty falcon and the head of a human. Sphinx eidolons most often come "
               "to bond with humanoids they find interesting, either for the humanoid themself or for where they "
               "might travel.",
        traits=["beast", "eidolon", "sphinx"], home="the Universe", sizes=("med", "sm"),
        attacks="claw (slashing), jaw (piercing), wing (bludgeoning)",
        attrs={"con": 0, "int": 3, "wis": 0, "cha": 0}, skills=["occultism", "society"],
        senses="darkvision", vision="darkvision", language="sphinx", language_text="Sphinx",
        speed=25, speed_text="25 feet", other_speeds=[],
        initial=("Riddlemaster", "passive", None, [], None,
                 p("Your eidolon is trained in Bardic Lore, a special Lore skill that can be used only to "
                   f"{L(ACTION['Recall Knowledge'], 'Recall Knowledge')}, but on any topic. If you have legendary "
                   "proficiency in Occultism, you gain expert proficiency in Bardic Lore, but you can't increase "
                   "your proficiency rank in Bardic Lore by any other means."),
                 [lore_skill("bardic-lore", "Bardic Lore", 1)], {}),
        symbiosis=("Befuddling Knowledge", "action", 2, ["auditory", "concentrate", "eidolon", "emotion", "mental"],
                   None,
                   p(f"Your eidolon shares some strange bit of lore that distracts the target's mind. Your eidolon "
                     f"{L(ACTION['Recall Knowledge'], 'Recalls Knowledge')} on the target and the target must "
                     "attempt a @Check[will|against:spell] save against your spell DC. The target takes a -1 "
                     "circumstance penalty to its Will DC against this effect if your eidolon succeeded its Recall "
                     "Knowledge check (-2 on a critical success).")
                   + degrees("The creature is unaffected.",
                             f"The creature is off-guard and takes a -2 circumstance penalty to Perception and Will "
                             f"saves for 1 round ({L(bk_s, 'Effect: Befuddling Knowledge (Success)')}).",
                             f"As success except the circumstance penalty is -3 and it doesn't end automatically. "
                             f"The target can end the effect early by succeeding a Recall Knowledge check against "
                             f"your spell DC ({L(bk_f, 'Effect: Befuddling Knowledge (Failure)')}).",
                             "As failure except the target is also stunned 1 as it processes new information."),
                   [], {}),
        transcendence=("Words of the Ancients", "passive", None, [], None,
                       p(f"Your eidolon is permanently affected by the {sp('truespeech')} spell. Additionally, it "
                         f"can spend 10 minutes to produce the effects of both a {sp('clairaudience')} and "
                         f"{sp('clairvoyance')} spell, but both spells must target the same location."),
                       [], {}),
    )

    # ---------------------------------------------------------------- Time
    time_dilation_eff = uuid(SU, "effect-time-dilation")
    E["time"] = dict(
        name="Time", tradition="occult", img="icons/magic/time/hourglass-tilted-glowing-gold.webp",
        flavor="Your eidolon is from the rivers of time itself. The forms of these eidolons are innumerable and at "
               "times inscrutable, sometimes emotional echoes given form like a siktempora while others something "
               "utterly alien like a hound of Tindalos or ancient one. These bonds are liminal, as the eidolon often "
               "has a unique perspective of their summoner's timeline.",
        traits=["aberration", "eidolon", "time"], home="Dimension of Time", sizes=("med", "sm"),
        attacks="tentacle (bludgeoning), claws (slashing), jaws (piercing)",
        attrs={"con": 2, "int": 1, "wis": 1, "cha": -1}, skills=["occultism", "stealth"],
        senses="darkvision", vision="darkvision", language="aklo", language_text="Aklo",
        speed=25, speed_text="25 feet", other_speeds=[],
        initial=("Time and Time Again", "reaction", None, ["eidolon"], {"max": 1, "per": "day"},
                 p(f"Your eidolon gains a +1 circumstance bonus against effects that inflict the {cond('slowed')} "
                   "condition. Once per day, it can use a reaction when it or you fail a skill check or saving throw "
                   "to revert the timeline, allowing you to roll again with a +1 circumstance bonus."),
                 [{"key": "FlatModifier", "selector": "saving-throw", "type": "circumstance", "value": 1,
                   "predicate": ["inflicts:slowed"]}], {}),
        symbiosis=("Time Flicker Strike", "action", 2, ["eidolon"], None,
                   p(f"Your eidolon flickers through time toward an unsuspecting target. Your eidolon "
                     f"{L(ACTION['Stride'], 'Strides')} up to its Speed. While it takes this action, time pauses. "
                     "All other creatures are completely unaware of its actions, can't speak, and can't use any "
                     "actions that would be triggered by your movement. If they end their movement within melee "
                     "reach of at least one enemy, they can make a melee Strike against that enemy and then teleport "
                     "back to the square from which they began their Time Flicker Strike. Your eidolon can use Time "
                     "Flicker Strike while Burrowing, Climbing, Flying, or Swimming instead of Striding."),
                   [], {}),
        transcendence=("Time Dilation", "action", 2, ["concentrate", "eidolon", "time"], {"max": 1, "per": "day"},
                       p("Your eidolon siphons time from its foes and imbues it into its allies. Choose up to 6 "
                         "creatures within 30 feet of you, at least one must be an enemy and one must be an ally. "
                         f"Allies you target become {cond('quickened', 'Quickened 1')} for 1 minute "
                         f"({L(time_dilation_eff, 'Effect: Time Dilation')}) and enemies you target must make a "
                         "@Check[fortitude|against:class] save against your class DC with the effects of "
                         f"{sp('slow')}."),
                       [], {}),
    )
    return E


# =====================================================================================================================
# Builders
# =====================================================================================================================
def _ability(slug, tier, data, level):
    name, action, actions, traits, freq, desc, rules, extra = data
    img = {"initial": EIDOLON_IMG, "symbiosis": SYMBIOSIS_IMG, "transcendence": TRANSCEND_IMG}[tier]
    doc = pub(feat(EI, f"{slug}-{tier}", name, level, desc, category="classfeature", action=action,
                   actions=actions, traits=traits, frequency=freq, rules=rules, img=img))
    doc["system"].update(extra)
    return doc


def _attr_line(a):
    def f(v):
        return f"+{v}" if v >= 0 else f"-{-v}"
    return (f"<em>Con</em> {f(a['con'])}, <em>Int</em> {f(a['int'])}, <em>Wis</em> {f(a['wis'])}, "
            f"<em>Cha</em> {f(a['cha'])}")


def _ability_line(tier, level, data, link_uuid=None):
    name, action, actions, *_ = data
    glyph = ""
    if action == "action":
        glyph = f' <span class="action-glyph">{actions}</span>'
    elif action == "reaction":
        glyph = ' <span class="action-glyph">R</span>'
    label = L(link_uuid, name) if link_uuid else name
    return f"<p><strong>{tier} ({level}) {label}</strong>{glyph}</p>"


def _entry_html(e, slug, with_bodies):
    skills = [s.capitalize() for s in e["skills"]] + e.get("extra_skills", [])
    head = (p(e["flavor"])
            + block("Tradition", e["tradition"].capitalize())
            + block("Traits", ", ".join(e["traits"]))
            + block("Home Plane", e["home"]) + HR
            + block("Size", "Medium or Small")
            + block("Suggested Attacks", e["attacks"])
            + block("Eidolon Attributes", _attr_line(e["attrs"]))
            + block("Skills", ", ".join(skills))
            + block("Senses", e["senses"])
            + block("Language", e["language_text"])
            + block("Speed", e["speed_text"]) + HR)
    out = head
    for tier, lvl, key in (("Initial", "1st", "initial"), ("Symbiosis", "7th", "symbiosis"),
                           ("Transcendence", "17th", "transcendence")):
        ab = e[key]
        out += _ability_line(tier, lvl, ab, uuid(EI, f"{slug}-{key}"))
        if with_bodies:
            out += ab[5]
    if e.get("sf2e"):
        out += p("<em>Starfinder 2e content.</em> Computers is a Starfinder skill; in a Pathfinder-only game it is "
                 "tracked as a Computers Lore skill.")
    return out


def _summoner_option(slug, e):
    """The summoner's Eidolon choice (picked from the pf2e Eidolon class feature)."""
    rules = [skill_rank(s) for s in e["skills"]]
    if e.get("sf2e"):
        rules.append(lore_skill("computers-lore", "Computers", 1))
    rules.append({"key": "ActiveEffectLike", "mode": "override", "path": "flags.system.eidolon.tradition",
                  "value": e["tradition"]})
    desc = _entry_html(e, slug, with_bodies=True)
    desc += HR + p(f"<strong>Eidolon actor:</strong> give your eidolon the "
                   f"{L(uuid(EI, slug + '-ancestry'), e['name'] + ' Eidolon')} ancestry from the Summons Unleashed "
                   "Eidolons compendium.")
    doc = pub(feat(SU, f"{slug}-eidolon", f"{e['name']} Eidolon", 1, desc, category="classfeature",
                   traits=["summoner"], other_tags=["summoner-eidolon"], rules=rules, img=e["img"]))
    doc["system"]["subfeatures"] = {
        "languages": {"granted": [e["language"]] if e["language"] else [], "slots": 0 if e["language"] else 1},
        "proficiencies": {}, "senses": {}, "suppressedFeatures": [],
    }
    return doc


def _key_builds(slug, e):
    out = []
    for key, prim, sec, ac, cap in (("str", "str", "dex", 2, 3), ("dex", "dex", "str", 1, 4)):
        a = dict(e["attrs"], **{prim: 4, sec: 2})
        word = {"str": "Strength", "dex": "Dexterity"}[key]
        rules = []
        for ab in ("str", "dex", "con", "int", "wis", "cha"):
            v = a[ab]
            rules.append({"key": "ActiveEffectLike", "mode": "upgrade" if v >= 0 else "downgrade",
                          "path": f"system.abilities.{ab}.mod", "value": v})
        rules += [{"key": "FlatModifier", "selector": "ac", "type": "item", "value": ac, "fromEquipment": False},
                  {"key": "DexterityModifierCap", "value": cap}]
        line = ", ".join(f"{ab.capitalize()} {'+' if a[ab] >= 0 else '-'}{abs(a[ab])}"
                         for ab in ("str", "dex", "con", "int", "wis", "cha"))
        desc = p(f"{word} is this eidolon's key attribute.", f"{line}; +{ac} AC (+{cap} Dex cap)")
        out.append(pub(feat(EI, f"{slug}-key-{key}", f"{e['name']} Eidolon ({word})", 1, desc,
                            category="ancestryfeature", img=e["img"], rules=rules)))
    return out


def _ancestry(slug, e):
    builds = [uuid(EI, f"{slug}-key-str"), uuid(EI, f"{slug}-key-dex")]
    rules = [
        {"key": "ChoiceSet", "flag": "eidolonType", "adjustName": False,
         "prompt": "Choose your eidolon's key attribute.",
         "choices": [{"value": builds[0], "label": "Strength"}, {"value": builds[1], "label": "Dexterity"}]},
        {"key": "GrantItem", "uuid": "{item|flags.system.rulesSelections.eidolonType}", "allowDuplicate": False},
        *[skill_rank(s) for s in e["skills"]],
        {"key": "ChoiceSet", "flag": "companionSize", "adjustName": False,
         "prompt": "PF2E.SpecificRule.Prompt.CreatureSize",
         "choices": [{"label": "PF2E.ActorSizeMedium", "value": "med"},
                     {"label": "PF2E.ActorSizeSmall", "value": "sm"}]},
        {"key": "ActiveEffectLike", "mode": "override", "path": "system.traits.size.value",
         "value": "{item|flags.system.rulesSelections.companionSize}"},
        {"key": "GrantItem", "uuid": CC_EIDOLON_CLASS, "allowDuplicate": False},
        {"key": "ActiveEffectLike", "mode": "override", "path": "flags.pf2e.eidolon-features",
         "value": {"initial": uuid(EI, f"{slug}-initial"), "symbiosis": uuid(EI, f"{slug}-symbiosis"),
                   "transcendence": uuid(EI, f"{slug}-transcendence")}},
    ]
    if e.get("sf2e"):
        rules.append(lore_skill("computers-lore", "Computers", 1))
    for typ, val in e["other_speeds"]:
        rules.append({"key": "BaseSpeed", "selector": typ, "value": val})
    if e["language"] is None:
        langs, extra = [], {"count": 1, "value": [], "custom": ""}
    else:
        langs, extra = [e["language"]], {"count": 0, "value": [], "custom": ""}
    desc = _entry_html(e, slug, with_bodies=False)
    desc += HR + p(f"The summoner's half of this eidolon is "
                   f"{L(uuid(SU, slug + '-eidolon'), e['name'] + ' Eidolon')} in the Summons Unleashed compendium.")
    system = {
        "description": {"gm": "", "value": desc},
        "rules": rules,
        "slug": f"{slug}-eidolon",
        "traits": {"otherTags": [], "value": [t for t in e["traits"] if t in VALID_TRAITS], "rarity": "common"},
        "publication": dict(PUB),
        "hp": 4, "size": "med", "hands": 2, "reach": 5, "speed": e["speed"],
        "boosts": {"0": {"value": []}, "1": {"value": []}, "2": {"value": []}},
        "flaws": {"0": {"value": []}},
        "languages": {"value": langs, "custom": ""},
        "additionalLanguages": extra,
        "items": {"eidab": {"img": EIDOLON_IMG, "name": "Eidolon Ability", "level": 1, "uuid": CC_EIDOLON_ABILITY}},
        "vision": e["vision"],
        "_migration": dict(MIG),
    }
    return _base(EI, f"{slug}-ancestry", f"{e['name']} Eidolon", "ancestry", e["img"], system)


# pf2e creature traits the ancestry can carry (sphinx is not a pf2e trait yet; it stays in the text).
VALID_TRAITS = {"aberration", "beast", "coatl", "construct", "eidolon", "fungus", "holy", "kami", "phantom",
                "rakshasa", "spirit", "tech", "time", "unholy"}


# =====================================================================================================================
# Convoker
# =====================================================================================================================
def _convoker():
    D = []
    convoke = uuid(SU, "spell-convoke")
    assault = uuid(SU, "spell-assembled-assault")
    combo = uuid(SU, "spell-combination-convocation")
    combo_eff = uuid(SU, "effect-combination-convocation-size")
    assembly = uuid(SU, "convoker-assembly")
    dedication = uuid(SU, "convoker-dedication")

    # ---------------------------------------------------------------- 1st level: Assembly (picked as the Eidolon)
    trad_choices = [{"label": f"PF2E.Trait{t.capitalize()}", "value": t} for t in TRADITION_SKILL]
    rules = [
        {"key": "ChoiceSet", "flag": "convokerTradition", "rollOption": "convoker-tradition", "adjustName": False,
         "prompt": "Choose your assembly's magical tradition.", "choices": trad_choices},
        {"key": "ActiveEffectLike", "mode": "override", "path": "flags.system.eidolon.tradition",
         "value": "{item|flags.system.rulesSelections.convokerTradition}"},
        *[dict(skill_rank(sk), predicate=[f"convoker-tradition:{t}"]) for t, sk in TRADITION_SKILL.items()],
        {"key": "ChoiceSet", "flag": "convokerKey", "adjustName": False,
         "prompt": "Choose your key attribute and spellcasting attribute.",
         "choices": [{"label": "PF2E.AbilityCha", "value": "cha"}, {"label": "PF2E.AbilityInt", "value": "int"}]},
        {"key": "ActiveEffectLike", "mode": "override", "path": "system.details.keyability.value",
         "value": "{item|flags.system.rulesSelections.convokerKey}"},
    ]
    # The assembly's eidolons are chosen per slot in the Assembly window (any eidolon ancestry from any
    # compendium), so character builders like PF2e Leveler only have to handle the two simple choices above.

    desc = (
        p("<em>Convoker class archetype.</em> Choose this as your eidolon when you take the Eidolon class feature. "
          "Though many summoners draw their power from a singular connection they forge with an eidolon, you "
          "harness the power of many, switching between them as the situation demands. Unlike Summoners, a "
          "Convoker is rarely born by accident. Many who take up this practice commonly study and perform a Binding "
          "Pact with their soon-to-be eidolons. While many are content with managing a triumvirate of eidolons, "
          "others seek to expand their convocation over time.")
        + block("Prerequisites", "You must be a summoner.")
        + block("Convoker Adjustments", "Your number of skills changes to equal 3 plus your Intelligence modifier, "
                "you do not gain your eidolon's languages, or obtain the "
                f"{sp('evolution surge')} focus spell at 1st level. Furthermore, you can choose for your key "
                "attribute and spellcasting modifier to be Intelligence instead of Charisma. You become a prepared "
                "caster instead of spontaneous, preparing spells each day directly from your assembly much like a "
                "magus preparing their spells during daily preparations. Your assembly contains spells much like a "
                "spellbook but is an intangible repository of knowledge and cannot be destroyed. You must select "
                f"{L(dedication, 'Convoker Dedication')} as your 2nd-level class feat.")
        + HR
        + "<h2>Assembly</h2>"
        + p("Your connection is shared amongst many, a cacophony of voices bound to your form. At 1st level, instead "
            "of selecting a single eidolon, you choose a single tradition of magic from which to draw your power: "
            "arcane, divine, occult, or primal. This choice determines your casting tradition and you become trained "
            "in the associated tradition's skill. Choose 3 eidolons from the tradition matching your spellcasting "
            "tradition; these eidolons form your assembly. When choosing eidolons, they can be variations of the same "
            "eidolon type, such as multiple dragon eidolons with different damage type selections for their breath "
            "weapon, or entirely different types of eidolons so long as they are from the same tradition. When "
            "forming your assembly and selecting eidolons, you can have them have different primary and secondary "
            "attacks if you so choose. Each day, choose one eidolon from your assembly to be your primary eidolon, "
            f"allowing you to {L(ACTION['Manifest Eidolon'], 'Manifest that Eidolon')} and work alongside it as "
            "normal for the summoner class. When you Refocus, you can change which of your eidolons in your assembly "
            "is your primary eidolon. Each eidolon in your assembly shares the same items and benefits; for example, "
            "any items with the eidolon trait are shared across each eidolon in the assembly and your handwraps of "
            "mighty blows applies to all of them.",
            "When you gain evolution feats, you can choose a number of evolution feats equal to the size of your "
            "assembly that you could qualify for, applying each to an eidolon in your assembly. Additionally, when "
            "you make your daily preparations, you can retrain any evolution feats you know for any other evolution "
            "feats available at the level you took the exchanged feats (including lower-level feats, as usual). You "
            "must meet all the new feat's other prerequisites. If you choose the Magical Understudy, Magical Adept, "
            "or Magical Master feats, the innate spells are shared across each eidolon, and you can still only cast "
            "them once per day, regardless of how many eidolons have these evolution feats.")
        + HR
        + "<h2>Running a Convoker in Foundry</h2>"
        + "<ul><li><p>This item records your tradition (and trains its skill) and your key attribute. It doesn't "
          "grant the eidolons' skills or languages to you. Your summoner spellcasting becomes prepared, using your "
          "tradition and key attribute.</p></li>"
          "<li><p>Each eidolon is its own actor. Open the <strong>Assembly</strong> tab on your sheet (or the "
          "window from the header button), choose each slot's eidolon from its dropdown (any eidolon from any "
          "compendium, Summoners+ included), and click Create: it gets the right ancestry, your level, and a link "
          "back to you. You can also drop an eidolon ancestry or an existing eidolon actor onto a slot. Click a "
          "portrait or token picture to change the art.</p></li>"
          f"<li><p>Casting {L(convoke, 'convoke')}, <em>assembled assault</em> or <em>combination convocation</em> "
          "from your sheet (or from the window) swaps, calls forth, or fuses your eidolons on the scene. Using "
          "Manifest Eidolon places or removes your primary eidolon.</p></li>"
          "<li><p>With pf2e-toolbelt's Shared Data turned on, every eidolon shares your Hit Points automatically.</p></li>"
          "<li><p>Exporting this actor (from the sidebar or the window) saves your whole assembly and its images "
          "in one file; importing it restores and relinks every eidolon.</p></li>"
          "<li><p>Put Convoker Dedication in your 2nd-level class feat slot. Your focus spells are added as you "
          "take the feats that grant them.</p></li></ul>"
    )
    doc = pub(feat(SU, "convoker-assembly", "Convoker Assembly", 1, desc, category="classfeature",
                   traits=["summoner"], other_tags=["summoner-eidolon"], rules=rules,
                   img=CONVOKER_IMG))
    doc["system"]["subfeatures"] = {"languages": {"granted": [], "slots": 0}, "proficiencies": {}, "senses": {},
                                    "suppressedFeatures": []}
    D.append(doc)

    # ---------------------------------------------------------------- focus spells
    D.append(spell(
        "spell-convoke", "Convoke", 1,
        p("You summon a member of your assembly, summoning it in the original's place. Pick one of your non-primary "
          "eidolons in your assembly; you change your primary eidolon to that eidolon, swapping your currently "
          "manifested eidolon for that one. The new eidolon retains all conditions and effects from the previous "
          "eidolon, including things like persistent damage and damage suffered. If the new eidolon is larger than "
          "the current eidolon and it doesn't have space to accommodate it, <em>convoke</em> fails. For 1 round "
          "after casting <em>convoke</em> your eidolon cannot use any action with a frequency, such as an elemental "
          "eidolon's elemental burst action.",
          f"<em>Warping Convoke:</em> you can teleport the new eidolon up to 15 feet (30 feet at 16th level) without "
          f"triggering reactions."),
        time="1", traits=["concentrate", "focus", "manipulate", "summoner", "teleportation"], range_="100 feet",
        target="your eidolon", img="icons/magic/movement/portal-vortex-orange.webp"))
    D.append(spell(
        "spell-assembled-assault", "Assembled Assault", 3,
        p("Coordinating with your primary eidolon, you briefly summon a secondary eidolon to launch a combined "
          "attack against your foes. You summon a secondary eidolon from your assembly within range; that eidolon "
          "provides flanking for you and your allies using their reach. Your primary eidolon and secondary eidolon "
          f"both make a {L(ACTION['Strike'], 'Strike')} against a creature within their reach. If your primary "
          f"eidolon is currently under the effects of {sp('boost eidolon')}, the secondary eidolon is as well. If "
          "both hit the same creature, combine their damage for the purpose of resistances and weaknesses. "
          "Furthermore, both attacks count toward your multiple attack penalty, but the penalty doesn't increase "
          "until after both attacks have been made. The secondary eidolon returns to your assembly upon the spell's "
          "completion."),
        time="2", traits=["concentrate", "focus", "manipulate", "summon", "summoner"], range_="60 feet",
        target="1 creature", img="icons/magic/symbols/runes-triangle-blue.webp"))
    D.append(spell(
        "spell-combination-convocation", "Combination Convocation", 6,
        p("You call forth another eidolon within your assembly, using the threads of connection between it and your "
          "currently deployed eidolon to combine the two into a new form. When you Cast the Spell, choose a "
          "non-primary eidolon in your assembly. It's temporarily called forth, and your magic fuses it with your "
          "primary eidolon, granting it up to two benefits. During this spell's duration, if you Cast "
          "<em>convoke</em> or unmanifest your eidolon, the spell ends.")
        + "<ul>"
          "<li><p>One evolution feat from the other eidolon. It must be a feat not currently on the primary eidolon, "
          "and the primary eidolon must meet the prerequisites for that feat, if any.</p></li>"
          "<li><p>The initial ability of the other eidolon. If the ability has a choice, it must be the same choice "
          "as the other eidolon's.</p></li>"
          "<li><p>One of the eidolon's unarmed attacks.</p></li>"
          "<li><p>The two combine their forms into a greater size, increasing one category larger and increasing "
          f"its reach by 5 feet ({L(combo_eff, 'Effect: Combination Convocation (Greater Size)')}).</p></li>"
          "<li><p>You use excess power released from the fusion into a blast that knocks foes away. Creatures in a "
          f"{tmpl('emanation', 30)} of the primary eidolon when you Cast this Spell must succeed at a "
          "@Check[fortitude|against:spell] save or be pushed 10 feet away (20 feet on a critical failure).</p></li>"
          "</ul>" + HR
        + p("<strong>Heightened (+1)</strong> You can choose up to three benefits. Additionally, you can choose up to "
            "two eidolons in your assembly to determine benefits from."),
        time="3", traits=["concentrate", "focus", "manipulate", "polymorph", "summoner"], range_="100 feet",
        target="your eidolon", duration="1 minute", img="icons/magic/symbols/circle-ouroboros.webp"))

    # ---------------------------------------------------------------- feats
    def cfeat(key, name, level, desc, prereq="Convoker Dedication", **kw):
        return pub(feat(SU, key, name, level, desc, category="class", traits=kw.pop("traits", ["archetype"]),
                        prereqs=[prereq], img=kw.pop("img", CONVOKER_IMG), **kw))

    D.append(cfeat("convoker-dedication", "Convoker Dedication", 2,
        p(f"You call upon a member of your assembly to assist you. You obtain the {L(convoke, 'convoke')} focus "
          "spell.", "Add <em>convoke</em> to your summoner focus spells."),
        prereq="Convoker Assembly", traits=["archetype", "class", "dedication"]))
    D.append(cfeat("assembly-evolution", "Assembly Evolution", 4,
        p(f"You regain the power to transform your assembly at a moment's notice. You obtain the "
          f"{sp('evolution surge')} focus spell. If you cast {L(convoke, 'convoke')} while <em>evolution surge</em> "
          "is active, you can choose a new effect for the newly summoned eidolon.")))

    sk_rules = [{"key": "RollOption", "domain": "all", "option": "shared-knowledge", "toggleable": True,
                 "alwaysActive": True, "label": "Shared Knowledge skill",
                 "suboptions": [{"label": skill_label(s), "value": s} for s in SKILLS]}]
    for s in SKILLS:
        sk_rules.append({"key": "ActiveEffectLike", "mode": "upgrade", "path": f"system.skills.{s}.rank",
                         "priority": 51, "predicate": [f"shared-knowledge:{s}", {"not": "shared-knowledge-bonus"}],
                         "value": "ternary(gte(@actor.level,16),3,ternary(gte(@actor.level,8),2,1))"})
    sk_rules.append({"key": "RollOption", "domain": "all", "option": "shared-knowledge-bonus", "toggleable": True,
                     "label": "Already at this rank (+1 circumstance instead)"})
    for s in SKILLS:
        sk_rules.append({"key": "FlatModifier", "selector": s, "type": "circumstance", "value": 1,
                         "predicate": [f"shared-knowledge:{s}", "shared-knowledge-bonus"]})
    D.append(cfeat("shared-knowledge", "Shared Knowledge", 4,
        p("The wisdom and knowledge of your assembly fills your mind. You become trained in one of the skills "
          "corresponding to your current primary eidolon. At 8th level, you become expert in this skill and at 16th "
          "level you become master in this skill. When you change your primary eidolon, this skill changes as well.",
          "Since this proficiency is temporary, it can't be used for prerequisites. If you have the same proficiency "
          "rank or higher in the skill your primary eidolon would grant, you instead gain a +1 circumstance bonus to "
          "that skill.",
          "Pick the skill from the dropdown on your sheet's Actions tab when your primary eidolon changes, and turn "
          "on the second toggle if you already have that rank."),
        rules=sk_rules))
    D.append(cfeat("assembled-assault", "Assembled Assault", 6,
        p("Though you can only maintain the form of one eidolon of your assembly at a time, you can temporarily call "
          "upon ephemeral manifestations to push the offensive. You gain access to the "
          f"{L(assault, 'assembled assault')} focus spell."),
        prereq="Convoker Assembly"))
    D.append(cfeat("expanded-assemblage", "Expanded Assemblage", 6,
        p("Your connection to your wellspring of magic grows, allowing you to call upon an even greater repository "
          "of eidolons for aid. Add an additional eidolon to your assembly; this eidolon can be of your tradition, "
          "or any non-opposing tradition. For instance, an arcane convoker could select an arcane, primal, or occult "
          "eidolon, but not a divine eidolon. If you choose an eidolon from a tradition other than your own, it is "
          "considered an eidolon of that tradition for the sake of feats and prerequisites.")
        + block("Special", "You can select this feat two additional times, gaining an additional eidolon to add to "
                "your assembly.")
        + p("Taking this feat opens another slot in your Assembly; choose its eidolon there.")))
    D[-1]["system"]["maxTakable"] = 3
    D.append(cfeat("warping-convoke", "Warping Convoke", 8,
        p("By drawing on the very teleportation magicks that allow for the summoning of your convocation, you "
          f"tactically reposition your active eidolon. When you cast {L(convoke, 'convoke')}, you can choose to "
          "teleport your eidolon up to 15 feet without triggering reactions. At 16th level, the range of this "
          "teleport increases to 30 feet.")))
    D.append(cfeat("combination-convocation", "Combination Convocation", 12,
        p("You fuse two members of your assembly into a single, greater form. You obtain the "
          f"{L(combo, 'combination convocation')} focus spell."),
        prereq="Convoker Assembly"))

    D.append(pub(effect(SU, "effect-combination-convocation-size", "Effect: Combination Convocation (Greater Size)",
        p("Your eidolon is fused with another member of your assembly. It is one size larger and its reach "
          "increases by 5 feet."),
        duration=("minutes", 1, "turn-start"), img="icons/magic/symbols/circle-ouroboros.webp",
        rules=[{"key": "CreatureSize", "value": 1},
               {"key": "ActiveEffectLike", "mode": "add", "path": "system.attributes.reach.base", "value": 5}])))
    D.append(pub(effect(SU, "effect-combination-convocation", "Effect: Combination Convocation",
        p("Your eidolon is fused with another member of your assembly and has the benefits listed in the chat card. "
          "When this effect ends (or you cast convoke or unmanifest the eidolon), the fused abilities and attacks "
          "are removed."),
        duration=("minutes", 1, "turn-start"), img="icons/magic/symbols/circle-ouroboros.webp")))
    D.append(pub(effect(SU, "effect-convoked", "Effect: Convoked",
        p("This eidolon was just convoked. It can't use any action with a frequency (such as an elemental "
          "eidolon's elemental burst) until the summoner's next turn."),
        duration=("rounds", 1, "turn-start"), img="icons/magic/movement/portal-vortex-orange.webp",
        rules=[{"key": "RollOption", "domain": "all", "option": "convoked"}])))
    return D


# =====================================================================================================================
# Effects used by the eidolon abilities
# =====================================================================================================================
def _effects():
    E = []
    E.append(pub(effect(SU, "effect-serpent-hope", "Effect: Serpent Hope",
        p("You are in a coatl eidolon's aura of hope: +2 status bonus to saves against fear and unholy effects, and "
          "you reduce your frightened value by 1 at the end of the summoner's turn."),
        duration=("unlimited", -1, "turn-start"), img="icons/creatures/reptiles/serpent-horned-green.webp",
        rules=[{"key": "FlatModifier", "selector": "saving-throw", "type": "status", "value": 2,
                "predicate": [{"or": ["fear", "unholy"]}]}])))
    E.append(pub(effect(SU, "effect-kami-ward", "Effect: Kami Ward",
        p("+1 circumstance bonus to AC and saving throws, +2 against unholy effects or effects from unholy "
          "creatures. The summoner gains this while adjacent to the eidolon."),
        duration=("rounds", 1, "turn-start"), img="icons/magic/nature/leaf-glow-teal.webp",
        rules=[{"key": "FlatModifier", "slug": "kami-ward", "selector": ["ac", "saving-throw"],
                "type": "circumstance", "value": 1, "predicate": [{"not": "unholy"}, {"not": "origin:trait:unholy"}]},
               {"key": "FlatModifier", "slug": "kami-ward-unholy", "selector": ["ac", "saving-throw"],
                "type": "circumstance", "value": 2,
                "predicate": [{"or": ["unholy", "origin:trait:unholy"]}]}])))
    E.append(pub(effect(SU, "effect-warded-regeneration", "Effect: Warded Regeneration",
        p("Your kami eidolon wards you: +1 status bonus to AC."),
        duration=("minutes", 1, "turn-start"), img="icons/magic/nature/leaf-glow-teal.webp",
        rules=[{"key": "FlatModifier", "selector": "ac", "type": "status", "value": 1}])))
    E.append(pub(effect(SU, "effect-malefic-consumption", "Effect: Malefic Consumption",
        p("Your rakshasa eidolon can use Swallow Whole on creatures of its size or smaller that it has grabbed or "
          "restrained. A swallowed creature takes @Damage[(4+floor((@actor.level-7)/2))d6[bludgeoning]] damage; "
          "rupture [[/r 17+3*floor((@actor.level-7)/2)]]."),
        duration=("minutes", 1, "turn-start"), img="icons/equipment/head/mask-tiger-silver.webp")))
    for tier, val, dur in (("Success", 2, ("rounds", 1, "turn-start")), ("Failure", 3, ("unlimited", -1, "turn-start"))):
        E.append(pub(effect(SU, f"effect-befuddling-knowledge-{tier.lower()}",
            f"Effect: Befuddling Knowledge ({tier})",
            p(f"Off-guard, and a -{val} circumstance penalty to Perception and Will saves."
              + ("" if tier == "Success" else " Ends when the creature succeeds at a Recall Knowledge check "
                 "against the summoner's spell DC.")),
            duration=dur, img="icons/commodities/materials/feather-white-glowing-beams.webp",
            rules=[{"key": "FlatModifier", "selector": ["perception", "will"], "type": "circumstance",
                    "value": -val},
                   {"key": "GrantItem", "uuid": COND["off-guard"],
                    "onDeleteActions": {"grantee": "restrict"}}])))
    E.append(pub(effect(SU, "effect-time-dilation", "Effect: Time Dilation",
        p("A time eidolon siphoned time into you: quickened 1 for 1 minute."),
        duration=("minutes", 1, "turn-start"), img="icons/magic/time/hourglass-tilted-glowing-gold.webp",
        rules=[{"key": "GrantItem", "uuid": COND["quickened"], "onDeleteActions": {"grantee": "restrict"}}])))
    return E


def build_all():
    su = _convoker()
    ei = []
    for slug, e in _abilities().items():
        su.append(_summoner_option(slug, e))
        ei.append(_ancestry(slug, e))
        ei.extend(_key_builds(slug, e))
        for tier, lvl in (("initial", 1), ("symbiosis", 7), ("transcendence", 17)):
            ei.append(_ability(slug, tier, e[tier], lvl))
    su.extend(_effects())
    return {SU: su, EI: ei}
