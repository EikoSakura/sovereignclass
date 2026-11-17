"""Martial Memoires: the Soaring Blade archetype.

The Favored Blade is whichever weapon carries the `favored-blade` tag (toggled from the inventory by
scripts/soaring-blade.mjs). Bladework Stance's effect counts the blades flying above you in its badge, which
the splash and extra-dice toggles read.
"""
from common import HR, action_item, block, effect, feat, p, uuid

PACK = "martial-memoires"
PUB = {"license": "ORC", "remaster": True, "title": "Martial Memoires"}

TAG = "item:tag:favored-blade"
STANCE_OPTION = "self:effect:bladework-stance"  # pf2e drops the "stance-" prefix from effect roll options
IMG = "icons/weapons/swords/sword-flanged-lightning.webp"
STANCE_IMG = "icons/magic/air/air-burst-spiral-blue-gray.webp"
DC = "class-spell"  # the higher of your class DC and spell DC: your soaring blade DC


def pub(doc):
    doc["system"]["publication"] = dict(PUB)
    return doc


def check(save, basic=True):
    return f"@Check[{save}|against:{DC}{'|basic' if basic else ''}]"


def build_all():
    stance_eff = uuid(PACK, "stance-bladework-stance")
    stance_act = uuid(PACK, "bladework-stance")
    surf_eff = uuid(PACK, "effect-blade-surfing")
    rending = uuid(PACK, "rending-recall")
    punitive = uuid(PACK, "punitive-strike")
    D = []

    def sfeat(key, name, level, desc, *, prereq="Soaring Blade Dedication", req=None, **kw):
        body = (block("Requirements", req) + HR if req else "") + desc
        return pub(feat(PACK, key, name, level, body, category="class",
                        traits=["archetype", *kw.pop("traits", [])], rarity="uncommon", prereqs=[prereq],
                        img=kw.pop("img", IMG), **kw))

    STANCE_REQ = "You're in Bladework Stance."

    # ------------------------------------------------------------------------------------------------ dedication
    D.append(sfeat("soaring-blade-dedication", "Soaring Blade Dedication", 2,
        p("Your mastery of your favored blade lets you wield it with your mind alone. Choose either a single "
          "one-handed slashing or piercing melee weapon with the agile or finesse trait or a single slashing or "
          "piercing one-handed ranged thrown weapon. It becomes your <strong>Favored Blade</strong>. You can change "
          "your favored blade by spending 1 day of downtime with a new weapon. The DC for an ability gained via "
          "this archetype is either your class DC or spell DC, whichever is higher, and is called your soaring "
          "blade DC.",
          f"You gain the @UUID[{stance_act}]{{Bladework Stance}} action.",
          "<em>Foundry:</em> mark your Favored Blade with the flying-blade toggle on its row in your inventory."),
        prereq="trained in martial weapons", traits=["dedication"],
        rules=[{"key": "GrantItem", "uuid": stance_act, "allowDuplicate": False}]))

    stance_desc = (
        block("Requirements", "You are wielding your Favored Blade.") + HR
        + p("You summon a number of copies of your Favored Blade equal to its number of weapon damage dice and make "
            "them fly above you. While a copy is flying above you, you count as wielding it.",
            "While in Bladework Stance, your Favored Blade and its copies gain the thrown 15 ft. trait, or increase "
            "their range increment by 10 feet if they already have it.",
            "You can use a single action with the concentrate trait to call back one or more copies within your "
            "Favored Blade's first range increment, or to move one or more copies flying around you to any place "
            "within your first range increment.",
            "If a copy would return to your hand, due to the effect of a returning rune for example, you can "
            "immediately make it fly above you.",
            "Wielding your copied blades requires focus and synergy with your Favored Blade. Any effect that would "
            "apply only to the Favored Blade, such as the penalty to Strikes from the Disarm action, also applies "
            "to the copies."))
    act = pub(action_item(PACK, "bladework-stance", "Bladework Stance", stance_desc, action="action", actions=1,
                          traits=["stance"], img=STANCE_IMG))
    act["system"]["selfEffect"] = {"name": "Stance: Bladework Stance", "uuid": stance_eff}
    D.append(act)

    split = [{"or": ["feat:raining-assault", "feat:downpour-of-steel"]}]
    D.append(pub(effect(PACK, "stance-bladework-stance", "Stance: Bladework Stance",
        p("Your Favored Blade and its copies fly above you. The badge counts the blades flying above you "
          "(set from your Favored Blade's damage dice when you enter the stance; adjust it as blades leave or "
          "return).",
          "Melee Favored Blades without the thrown trait gain thrown 15 ft.; ranged thrown ones gain +10 feet of "
          "range increment."),
        duration=("unlimited", -1, "turn-start"), img=STANCE_IMG,
        badge={"type": "counter", "value": 1, "label": "Blades flying"},
        rules=[
            {"key": "AdjustStrike", "mode": "add", "property": "weapon-traits", "value": "thrown-15",
             "definition": [TAG, "item:melee", {"not": "item:thrown-melee"}],
             "predicate": [{"not": "feat:ubiquitous-blade"}]},
            {"key": "AdjustStrike", "mode": "add", "property": "weapon-traits", "value": "thrown-25",
             "definition": [TAG, "item:melee", {"not": "item:thrown-melee"}],
             "predicate": ["feat:ubiquitous-blade"]},
            {"key": "AdjustStrike", "mode": "add", "property": "range-increment", "value": 10,
             "definition": [TAG, "item:ranged"]},
            {"key": "RollOption", "domain": "all", "option": "soaring-blade-splash", "toggleable": True,
             "label": "Raining Assault / Downpour of Steel splash", "predicate": split},
            {"key": "FlatModifier", "selector": "strike-damage", "slug": "soaring-blade-splash",
             "damageCategory": "splash", "value": "@item.badge.value",
             "predicate": [TAG, "soaring-blade-splash"]},
            {"key": "RollOption", "domain": "all", "option": "true-blades-strike", "toggleable": True,
             "label": "True Blade's Strike", "predicate": ["feat:true-blades-strike"]},
            {"key": "DamageDice", "selector": "strike-damage", "slug": "true-blades-strike-step",
             "override": {"upgrade": True}, "predicate": [TAG, "item:melee", "true-blades-strike"]},
            {"key": "DamageDice", "selector": "strike-damage", "slug": "true-blades-strike-dice",
             "diceNumber": "@item.badge.value", "predicate": [TAG, "item:melee", "true-blades-strike"]},
        ])))

    # ------------------------------------------------------------------------------------------------ 4th
    D.append(sfeat("slashing-recall", "Slashing Recall", 4,
        p("With a little more concentration, your blades stay deadly even when returning to you. Recall all blades "
          "within your Favored Blade's first range increment. Draw a line between you and the starting position of "
          "each blade. Any creature inside them takes damage equal to your Favored Blade's damage dice with a "
          f"{check('reflex')} save against your soaring blade DC.",
          "The damage type is the same as your Favored Blade. An enemy can only take this damage once, even if "
          "inside the path of two or more blades."),
        req=STANCE_REQ, action="action", actions=2))
    D.append(sfeat("focused-parry", "Focused Parry", 4,
        p("As steel whirls around you, foes who try to attack you are blocked effortlessly. While you're in "
          "Bladework Stance, your Favored Blade gains the parry trait. If it already has it, the circumstance bonus "
          "to AC increases to +2.",
          "<em>Foundry:</em> turn on the toggle if your Favored Blade already had the parry trait."),
        rules=[
            {"key": "AdjustStrike", "mode": "add", "property": "weapon-traits", "value": "parry",
             "definition": [TAG], "predicate": [STANCE_OPTION]},
            {"key": "RollOption", "domain": "all", "option": "focused-parry-native", "toggleable": True,
             "label": "Favored Blade already has parry"},
            {"key": "FlatModifier", "selector": "ac", "type": "circumstance", "value": 2, "slug": "focused-parry",
             "predicate": [STANCE_OPTION, "self:effect:parry", "focused-parry-native"]},
        ]))
    D.append(sfeat("blade-spin", "Blade Spin", 4,
        p("With a quick movement, your blades spin around you, tearing your enemies away. All creatures within your "
          "Favored Blade's reach take damage equal to your Favored Blade's damage dice with a "
          f"{check('reflex')} save against your soaring blade DC. The damage type is the same as your Favored "
          "Blade. The DC of this action is affected by your multiple attack penalty."),
        req="You're in Bladework Stance and your Favored Blade is a melee weapon.",
        action="action", actions=1, traits=["attack"]))

    # ------------------------------------------------------------------------------------------------ 8th
    D.append(sfeat("flying-pincer", "Flying Pincer", 8,
        p("Using two blades at once, you force your enemy between a blade and a sharp place. Make two Strikes "
          "against the same enemy, the first one at your current multiple attack penalty and the second at a -2 "
          "penalty. The enemy is @UUID[Compendium.pf2e.conditionitems.Item.AJh5ex99aV6VTggg]{Off-Guard} against "
          "both Strikes. At least one of them must be a thrown Strike with a copy of your blade."),
        req=STANCE_REQ, action="action", actions=2, traits=["flourish"]))
    D.append(sfeat("blade-barrage", "Blade Barrage", 8,
        p("You fling your blades across the battlefield, focusing on speed rather than precision. Make two thrown "
          "Strikes. Apply your multiple attack penalty to the Strikes normally."),
        req=STANCE_REQ, action="action", actions=1, traits=["flourish"]))

    # ------------------------------------------------------------------------------------------------ 10th
    D.append(sfeat("raining-assault", "Raining Assault", 10,
        p("You let many blades fall down at once, so that your target can't possibly dodge them all. Make a Strike. "
          "It deals splash damage equal to the number of blades flying over you. After this Strike, all your "
          "flying blades fall in the space of your target as if you had thrown them.",
          "<em>Foundry:</em> turn on the splash toggle from Bladework Stance before the Strike; it adds splash "
          "equal to the stance's blade count."),
        req=STANCE_REQ, action="action", actions=1))
    D.append(sfeat("focused-riposte", "Focused Riposte", 10,
        block("Trigger", "An enemy within your weapon's first range increment critically misses you with a "
                         "Strike.")
        + p("Steel flies around you to protect and attack. You Strike the triggering enemy."),
        req="You're in Bladework Stance and have a circumstance bonus to AC from the parry trait.",
        action="reaction"))

    # ------------------------------------------------------------------------------------------------ 12th
    surf = sfeat("blade-surfing", "Blade Surfing", 12,
        p("You hop on one copy of your Favored Blade. You gain a fly Speed equal to your land Speed. As long as "
          "you're surfing on your blade, it doesn't count as flying above you.",
          "You can dismiss this effect as a single action with the concentrate trait, the blade flying back above "
          "you. If you dismiss this effect while in the air, you start falling normally."),
        req=STANCE_REQ, action="action", actions=1)
    surf["system"]["selfEffect"] = {"name": "Effect: Blade Surfing", "uuid": surf_eff}
    D.append(surf)
    D.append(pub(effect(PACK, "effect-blade-surfing", "Effect: Blade Surfing",
        p("You surf on a copy of your Favored Blade: fly Speed equal to your land Speed. That copy doesn't count as "
          "flying above you. Dismiss with a single concentrate action."),
        duration=("unlimited", -1, "turn-start"), img="icons/magic/air/wind-weather-sailing-ship.webp",
        rules=[{"key": "BaseSpeed", "selector": "fly", "value": "@actor.attributes.speed.value"}])))
    D.append(sfeat("sharp-steps", "Sharp Steps", 12,
        p("You dash toward your blade to recover it in a deadly flourish. Stride toward the required blade. If you "
          "end your movement adjacent to it, you immediately pick it up and use Blade Spin."),
        prereq="Blade Spin", req="You're in Bladework Stance and one of your copied blades could be recalled.",
        action="action", actions=1, traits=["flourish"]))
    D.append(sfeat("impaling-strikes", "Impaling Strikes", 12,
        p("When you hit an enemy with a Strike with a copy of your Favored Blade, you can have it stay stuck in "
          "your enemy. They can remove it with a single Interact action.",
          f"You gain the @UUID[{rending}]{{Rending Recall}} action."),
        rules=[{"key": "GrantItem", "uuid": rending, "allowDuplicate": False}]))
    D.append(pub(action_item(PACK, "rending-recall", "Rending Recall",
        block("Requirements", "You're in Bladework Stance and an enemy within your Favored Blade's first range "
                              "increment has at least one copy of your Favored Blade stuck in them.") + HR
        + p("You recall all blades within your weapon's first range increment. Creatures take "
            "@Damage[(1d6+1)[persistent,bleed]] damage for each blade that was stuck in them, with a "
            f"{check('fortitude')} save against your soaring blade DC."),
        action="action", actions=1, traits=["concentrate"], img=IMG)))

    # ------------------------------------------------------------------------------------------------ 14th
    D.append(sfeat("ubiquitous-blade", "Ubiquitous Blade", 14,
        p("You're able to control your blades with more precision over long distances. Your Favored Blade gains the "
          "reach trait and the range of its thrown trait becomes 25 feet. If it already had the thrown trait, it "
          "instead increases its range increment by 10 feet."),
        rules=[
            {"key": "AdjustStrike", "mode": "add", "property": "weapon-traits", "value": "reach",
             "definition": [TAG, "item:melee"]},
            {"key": "AdjustStrike", "mode": "add", "property": "range-increment", "value": 10,
             "definition": [TAG, "item:ranged"]},
        ]))

    # ------------------------------------------------------------------------------------------------ 16th
    D.append(sfeat("battlefield-control", "Battlefield Control", 16,
        p("You leave your blades in place; your enemies shouldn't forget them. Send a blade within a space within "
          "your blade's first range increment. The copy then starts floating in the chosen space for a maximum of "
          "one minute.",
          f"You gain the @UUID[{punitive}]{{Punitive Strike}} reaction."),
        req=STANCE_REQ, action="action", actions=1,
        rules=[{"key": "GrantItem", "uuid": punitive, "allowDuplicate": False}]))
    D.append(pub(action_item(PACK, "punitive-strike", "Punitive Strike",
        block("Trigger", "An enemy within 5 feet of a blade you placed with Battlefield Control uses a Manipulate "
                         "action, makes a ranged Strike, or leaves a square during a move action.") + HR
        + p("You make a melee Strike against the triggering enemy, using the blade you placed to determine your "
            "position. On a critical success, the triggering action is disrupted."),
        action="reaction", traits=["concentrate"], img=IMG)))

    # ------------------------------------------------------------------------------------------------ 20th
    D.append(sfeat("true-blades-strike", "True Blade's Strike", 20,
        p("You coalesce all your blades into your Favored Blade for a killing blow. Make a melee Strike with your "
          "Favored Blade. Its damage die increases by one step, and for every blade flying above you, you deal an "
          "additional die of damage. This Strike counts as three attacks when calculating your multiple attack "
          "penalty. After using this activity, you exit your Bladework Stance.",
          "<em>Foundry:</em> turn on the True Blade's Strike toggle from Bladework Stance for the Strike; it "
          "upgrades the die and adds dice equal to the stance's blade count."),
        req=STANCE_REQ, action="action", actions=2))
    D.append(sfeat("downpour-of-steel", "Downpour of Steel", 20,
        p("Your blades rain down all around you. Make a thrown Strike against each foe within your blade's first "
          "range increment. Those Strikes deal splash damage equal to the number of copied blades flying above you, "
          "but the same enemy can only take splash damage once from this activity. Each Strike counts toward your "
          "multiple attack penalty, but do not increase your penalty until you have made all your attacks. After "
          "using this activity, you exit your Bladework Stance."),
        req=STANCE_REQ, action="action", actions=2))

    return {PACK: D}
