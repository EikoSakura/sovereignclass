"""Non-Sovereign extras: automated versions of rules the pf2e system doesn't ship yet."""
from common import HR, block, effect, feat, action_item, p, uuid

PACK = "extras"
FEYBOUND = {"license": "ORC", "remaster": True, "title": "Pathfinder Feybound"}

STANCE_NAME = "Stance: Stellar Dance Stance"
STANCE_SLUG = "stance-stellar-dance-stance"
ZENITH_NAME = "Effect: Stellar Dance Zenith"
ZENITH_SLUG = "effect-stellar-dance-zenith"

STAR_IMG = "icons/magic/light/explosion-star-glow-blue.webp"
ZENITH_IMG = "icons/magic/light/explosion-star-glow-yellow.webp"


def _feybound(doc):
    doc["system"]["publication"] = dict(FEYBOUND)
    return doc


def build_all():
    zenith_uuid = uuid(PACK, "stellar-dance-zenith")
    stance_uuid = uuid(PACK, "stellar-dance-stance-effect")
    action_uuid = uuid(PACK, "stellar-dance-stance")

    stance_desc = (
        block("Requirements", "You aren't encumbered or wearing medium or heavy armor.")
        + HR
        + p("You dance as freely as the stars above. While in this stance, you can attempt a Performance check "
            "instead of an Acrobatics check to [[/act escape skill=performance]] or "
            "[[/act tumble-through skill=performance]]. When you succeed at such a check, your stance reaches its "
            "zenith. While your dance is at its zenith, your Strikes with agile or finesse weapons and unarmed "
            "attacks deal additional force damage equal to the number of weapon damage dice.",
            "Your stance stays at its zenith until the start of your next turn or until you leave the stance, "
            "whichever comes first, and you can't bring your stance to its zenith if it's already at its zenith. "
            "If you gain more ways to reach the zenith through other feats, these restrictions apply to those "
            "methods, too.")
    )

    action = _feybound(action_item(
        PACK, "stellar-dance-stance", "Stellar Dance Stance", stance_desc,
        action="action", actions=1, traits=["primal", "stance"], img=STAR_IMG,
    ))
    action["system"]["selfEffect"] = {"name": STANCE_NAME, "uuid": stance_uuid}

    stance = _feybound(effect(
        PACK, "stellar-dance-stance-effect", STANCE_NAME,
        p("You are in Stellar Dance Stance. Use Performance to "
          "[[/act escape skill=performance]] or [[/act tumble-through skill=performance]]; "
          f"success brings your dance to its zenith (@UUID[{zenith_uuid}]{{Zenith}})."),
        duration=("encounter", -1, "turn-start"), img=STAR_IMG,
        rules=[{
            "key": "Note",
            "selector": "performance",
            "outcome": ["success", "criticalSuccess"],
            "predicate": [
                {"or": ["action:escape", "action:tumble-through"]},
                {"not": f"self:effect:{ZENITH_SLUG}"},
            ],
            "title": "{item|name}",
            "text": f"Your dance reaches its zenith. Apply @UUID[{zenith_uuid}]{{Effect: Stellar Dance Zenith}}.",
        }],
    ))

    zenith = _feybound(effect(
        PACK, "stellar-dance-zenith", ZENITH_NAME,
        p("Your stellar dance is at its zenith. Your Strikes with agile or finesse weapons and unarmed attacks "
          "deal additional force damage equal to the number of weapon damage dice.",
          "Ends at the start of your next turn or when you leave Stellar Dance Stance."),
        duration=("rounds", 1, "turn-start"), img=ZENITH_IMG,
        rules=[{
            "key": "FlatModifier",
            "selector": "strike-damage",
            "slug": "stellar-dance-zenith",
            "damageType": "force",
            "value": "@weapon.system.damage.dice",
            "predicate": [
                f"self:effect:{STANCE_SLUG}",
                {"or": ["item:trait:agile", "item:trait:finesse", "item:category:unarmed"]},
            ],
        }],
    ))

    dedication = _feybound(feat(
        PACK, "stellar-dancer-dedication", "Stellar Dancer Dedication", 2,
        p("<strong>Access</strong> You were granted permission to learn it by a member of the Starlit Crown.")
        + HR
        + p("You've learned the stellar dance, a fey art honoring the celestial bodies. You become an expert in "
            "Performance. If you were already an expert in Performance, you instead become trained in Nature or "
            "Fey Lore (your choice).",
            f"You also gain the @UUID[{action_uuid}]{{Stellar Dance Stance}} action."),
        category="class", traits=["archetype", "dedication"], rarity="uncommon",
        prereqs=["trained in Performance", "trained in Nature or Fey Lore"], img=STAR_IMG,
        rules=[
            {"key": "ActiveEffectLike", "mode": "upgrade", "path": "system.skills.performance.rank", "value": 2},
            {"key": "GrantItem", "uuid": action_uuid},
        ],
    ))

    return {PACK: [dedication, action, stance, zenith]}
