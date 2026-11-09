"""Shared helpers for building the pf2e-sovereign module's compendium sources."""
import hashlib
import os
import re

MODULE_ID = "pf2e-sovereign"
_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_HERE) == "build" and os.path.basename(os.path.dirname(_HERE)) == "src":
    MODULE_DIR = os.path.dirname(os.path.dirname(_HERE))
else:
    MODULE_DIR = r"C:/Users/sword/AppData/Local/FoundryVTT/Data/modules/pf2e-sovereign"
CORE_PUBLIC = r"C:/Program Files/Foundry Virtual Tabletop/resources/app/public"
PF2E_DIR = r"C:/Users/sword/AppData/Local/FoundryVTT/Data/systems/pf2e"

STATS = {"coreVersion": "14.361", "systemId": "pf2e", "systemVersion": "8.6.1"}
PUB = {"license": "ORC", "remaster": True, "title": "Sovereign (Homebrew)"}
MIG = {"version": 0.959, "previous": None}

ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

MISSING_ICONS = []


def mkid(key):
    h = hashlib.sha256(("sovereign:" + key).encode()).digest()
    return "".join(ALNUM[b % 62] for b in h[:16])


def uuid(pack, key, doc="Item"):
    return f"Compendium.{MODULE_ID}.{pack}.{doc}.{mkid(pack + ':' + key)}"


def slugify(name):
    s = name.lower().replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def icon(path):
    """Validate that an icon path exists in Foundry core or the pf2e system."""
    if path.startswith("systems/pf2e/"):
        full = os.path.join(PF2E_DIR, path[len("systems/pf2e/"):])
    else:
        full = os.path.join(CORE_PUBLIC, path)
    if not os.path.exists(full):
        MISSING_ICONS.append(path)
    return path


# ---------------------------------------------------------------- pf2e links
PF = {
    # actions
    "Direct Follower": "Compendium.pf2e.actionspf2e.Item.H72AAzknXiojqXdY",
    "Aid": "Compendium.pf2e.actionspf2e.Item.HCl3pzVefiv9ZKQW",
    "Recall Knowledge": "Compendium.pf2e.actionspf2e.Item.1OagaWtBpVXExToo",
    "Earn Income": "Compendium.pf2e.actionspf2e.Item.QyzlsLrqM0EEwd7j",
    "Stride": "Compendium.pf2e.actionspf2e.Item.Bcxarzksqt9ezrs6",
    "Step": "Compendium.pf2e.actionspf2e.Item.UHpkTuCtyaPqiCAB",
    "Strike": "Compendium.pf2e.actionspf2e.Item.VjxZFuUXrCU94MWR",
    "Raise a Shield": "Compendium.pf2e.actionspf2e.Item.xjGwis0uaC2305pm",
    "Sense Motive": "Compendium.pf2e.actionspf2e.Item.1xRFPTFtWtGJ9ELw",
    "Sustain": "Compendium.pf2e.actionspf2e.Item.3f5DMFu8fPiqHpRg",
    "Administer First Aid": "Compendium.pf2e.actionspf2e.Item.MHLuKy4nQO2Z4Am1",
    "Treat Poison": "Compendium.pf2e.actionspf2e.Item.KjoCEEmPGTeFE4hh",
    "Avoid Notice": "Compendium.pf2e.actionspf2e.Item.IE2nThCmoyhQA0Jn",
    "Scout": "Compendium.pf2e.actionspf2e.Item.kV3XM0YJeS2KCSOb",
    "Search": "Compendium.pf2e.actionspf2e.Item.TiNDYUGlMmxzxBYU",
    "Investigate": "Compendium.pf2e.actionspf2e.Item.EwgTZBWsc8qKaViP",
    # feats
    "Domain Initiate": "Compendium.pf2e.feats-srd.Item.hT4INKGtly4QY8KN",
    "Advanced Domain": "Compendium.pf2e.feats-srd.Item.uR44wELN9OlU68cL",
    "Battle Medicine": "Compendium.pf2e.feats-srd.Item.wYerMk6F1RZb0Fwt",
    "Shield Block": "Compendium.pf2e.feats-srd.Item.jM72TjJ965jocBV8",
    # class features reused as-is
    "Weapon Specialization": "Compendium.pf2e.classfeatures.Item.9EqIasqfI8YIM3Pt",
    "Greater Weapon Specialization": "Compendium.pf2e.classfeatures.Item.Z7HX6TeFsaup7Dx9",
    # spells
    "banishment": "Compendium.pf2e.spells-srd.Item.bay4AfSu2iIozNNW",
    "clairvoyance": "Compendium.pf2e.spells-srd.Item.zvKWclOZ7A53DObE",
    "overwhelming presence": "Compendium.pf2e.spells-srd.Item.fkDeKktdmbeplYRY",
    # conditions
    "off-guard": "Compendium.pf2e.conditionitems.Item.AJh5ex99aV6VTggg",
    "frightened": "Compendium.pf2e.conditionitems.Item.TBSHQspnbcqxsmjL",
    "stupefied": "Compendium.pf2e.conditionitems.Item.e1XGnhKNSQIm5IXg",
    "fatigued": "Compendium.pf2e.conditionitems.Item.HL2l2VRSaQHu9lUw",
    "paralyzed": "Compendium.pf2e.conditionitems.Item.6uEgoh53GbXuHpTF",
    "wounded": "Compendium.pf2e.conditionitems.Item.Yl48xTdMh3aeQYL2",
    "clumsy": "Compendium.pf2e.conditionitems.Item.i3OJZU2nk64Df3xm",
    "enfeebled": "Compendium.pf2e.conditionitems.Item.MIRkyAjyBeXivMa7",
    "sickened": "Compendium.pf2e.conditionitems.Item.fesd1n5eVhpCSS18",
    "confused": "Compendium.pf2e.conditionitems.Item.yblD8fOR1J8rDwEQ",
    "quickened": "Compendium.pf2e.conditionitems.Item.nlCjDvLMf2EkV2dl",
    "dying": "Compendium.pf2e.conditionitems.Item.yZRUzMqrMmfLu0V1",
    "unconscious": "Compendium.pf2e.conditionitems.Item.fBnFDH2MTzgFijKf",
    # PF2e Companion Compendia (pf2e-animal-companions) followers
    "Follower": "Compendium.pf2e-animal-companions.AC-Features.Item.mefI4QYwzSIQiwGj",
    "Adept": "Compendium.pf2e-animal-companions.AC-Followers.Item.A4lRasm15Gtkhj9G",
    "Berserker": "Compendium.pf2e-animal-companions.AC-Followers.Item.UGypwzL2kf2lpvGK",
    "Medic": "Compendium.pf2e-animal-companions.AC-Followers.Item.ZgVoPylxwZuz9B4k",
    "Scout": "Compendium.pf2e-animal-companions.AC-Followers.Item.BrQt3St9A9ntCRus",
    "Sharpshooter": "Compendium.pf2e-animal-companions.AC-Followers.Item.qexqlVIb13Z8Yub6",
    "Shieldbearer": "Compendium.pf2e-animal-companions.AC-Followers.Item.HO6R7mNIBU6LgJpo",
    "Experienced Advancement": "Compendium.pf2e-animal-companions.AC-Followers.Item.Drsjs3tJmr7xVXvl",
    "Veteran Advancement": "Compendium.pf2e-animal-companions.AC-Followers.Item.TtGZS1qWyw25EXNC",
    "Exceptional Advancement": "Compendium.pf2e-animal-companions.AC-Followers.Item.FVB4oQEeV2f1Ga7J",
}

FOLLOWER_TYPES = ["Adept", "Berserker", "Medic", "Scout", "Sharpshooter", "Shieldbearer"]


def link(target, label=None):
    u = PF.get(target, target)
    return f"@UUID[{u}]" + (f"{{{label}}}" if label else "")


def p(*parts):
    return "".join(f"<p>{x}</p>" for x in parts)


def block(label, text):
    return f"<p><strong>{label}</strong> {text}</p>"


HR = "<hr />"


# ---------------------------------------------------------------- documents
def _base(pack, key, name, type_, img, system, extra=None):
    _id = mkid(pack + ":" + key)
    doc = {
        "_id": _id,
        "_key": f"!items!{_id}",
        "name": name,
        "type": type_,
        "img": icon(img),
        "system": system,
        "effects": [],
        "folder": None,
        "sort": 0,
        "flags": {},
        "_stats": dict(STATS),
    }
    if extra:
        doc.update(extra)
    return doc


def feat(pack, key, name, level, desc, *, category="class", action="passive", actions=None,
         traits=(), rarity="common", prereqs=(), rules=(), frequency=None, img=None,
         subfeatures=None, other_tags=()):
    system = {
        "actionType": {"value": action},
        "actions": {"value": actions},
        "category": category,
        "description": {"value": desc},
        "level": {"value": level},
        "prerequisites": {"value": [{"value": x} for x in prereqs]},
        "publication": dict(PUB),
        "rules": list(rules),
        "traits": {"rarity": rarity, "value": list(traits), "otherTags": list(other_tags)},
        "slug": slugify(name),
        "_migration": dict(MIG),
    }
    if frequency:
        system["frequency"] = frequency
    if subfeatures:
        system["subfeatures"] = subfeatures
    return _base(pack, key, name, "feat", img or "systems/pf2e/icons/default-icons/feat.svg", system)


def action_item(pack, key, name, desc, *, action="action", actions=1, traits=(), rules=(),
                frequency=None, img=None, category=None, rarity="common"):
    system = {
        "actionType": {"value": action},
        "actions": {"value": actions if action == "action" else None},
        "category": category,
        "description": {"value": desc},
        "publication": dict(PUB),
        "rules": list(rules),
        "slug": slugify(name),
        "traits": {"rarity": rarity, "value": list(traits)},
        "_migration": dict(MIG),
    }
    if frequency:
        system["frequency"] = frequency
    default_img = {
        "action": {1: "systems/pf2e/icons/actions/OneAction.webp",
                   2: "systems/pf2e/icons/actions/TwoActions.webp",
                   3: "systems/pf2e/icons/actions/ThreeActions.webp"}.get(actions, "systems/pf2e/icons/actions/OneAction.webp"),
        "reaction": "systems/pf2e/icons/actions/Reaction.webp",
        "free": "systems/pf2e/icons/actions/FreeAction.webp",
        "passive": "systems/pf2e/icons/actions/Passive.webp",
    }[action]
    return _base(pack, key, name, "action", img or default_img, system)


def effect(pack, key, name, desc, *, rules=(), duration=("rounds", 1, "turn-start"), img=None,
           badge=None, level=1):
    unit, value, expiry = duration
    system = {
        "description": {"value": desc},
        "duration": {"expiry": expiry, "sustained": False, "unit": unit,
                     "value": value if unit not in ("unlimited", "encounter") else -1},
        "level": {"value": level},
        "publication": dict(PUB),
        "rules": list(rules),
        "start": {"initiative": None, "value": 0},
        "tokenIcon": {"show": True},
        "traits": {"value": []},
        "slug": slugify(name),
        "_migration": dict(MIG),
    }
    if badge:
        system["badge"] = badge
    return _base(pack, key, name, "effect", img or "systems/pf2e/icons/default-icons/effect.svg", system)


# ---------------------------------------------------------------- rule helpers
def toggle(option, label, default=False, domain="all"):
    r = {"key": "RollOption", "domain": domain, "option": option, "toggleable": True, "label": label}
    if default:
        r["value"] = True
    return r


def grant(u, **kw):
    r = {"key": "GrantItem", "uuid": u}
    r.update(kw)
    return r


def gte(n):
    return {"gte": ["self:level", n]}


def lt(n):
    return {"lt": ["self:level", n]}
