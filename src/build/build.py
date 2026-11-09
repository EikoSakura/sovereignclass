"""Assemble, validate, and write the pf2e-sovereign module sources."""
import glob
import json
import os
import re
import shutil
import sys

import class_data
import feats_data
from common import MISSING_ICONS, MODULE_DIR, MODULE_ID

VERSION = "1.0.4"
REPO = "https://github.com/EikoSakura/sovereignclass"

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ref")

PACKS = [
    ("classes", "Classes", "Item"),
    ("class-features", "Class Features", "Item"),
    ("feats", "Feats", "Item"),
    ("actions", "Actions", "Item"),
    ("effects", "Effects", "Item"),
]

data = {k: [] for k, _, _ in PACKS}
for part in (class_data.build_all(), feats_data.build_all()):
    for k, docs in part.items():
        data[k].extend(docs)

errors = []

# ---- unique ids per pack
for pack, docs in data.items():
    ids = [d["_id"] for d in docs]
    if len(ids) != len(set(ids)):
        errors.append(f"duplicate ids in {pack}")
    for d in docs:
        for it in d.get("items", []):
            pass

# ---- internal links
index = {pack: {d["_id"] for d in docs} for pack, docs in data.items()}
blob = json.dumps(data)
for pack, doc, _id in re.findall(rf"Compendium\.{MODULE_ID}\.([a-z-]+)\.(Item|Actor)\.([A-Za-z0-9]{{16}})", blob):
    if _id not in index.get(pack, set()):
        errors.append(f"broken internal link {pack}.{_id}")

# ---- pf2e links (needs extracted reference packs in ../ref; skipped when absent)
HAVE_REF = os.path.isdir(os.path.join(REF, "feats"))
if not HAVE_REF:
    print("note: reference packs not found, skipping pf2e and Companion Compendia link checks")
ref_map = {"actionspf2e": "actions", "feats-srd": "feats", "classfeatures": "class-features",
           "spells-srd": "spells", "conditionitems": "conditions", "feat-effects": "feat-effects"}
for pack, _id in set(re.findall(r"Compendium\.pf2e\.([a-z-]+)\.Item\.([A-Za-z0-9]{16})", blob)):
    folder = ref_map.get(pack)
    if HAVE_REF and (not folder or not glob.glob(os.path.join(REF, folder, f"*_{_id}.json"))):
        errors.append(f"unverified pf2e link {pack}.{_id}")

# ---- Companion Compendia links
cc_map = {"AC-Followers": "acf", "AC-Features": "acfeat"}
for pack, _id in set(re.findall(r"Compendium\.pf2e-animal-companions\.([A-Za-z-]+)\.Item\.([A-Za-z0-9]{16})", blob)):
    folder = cc_map.get(pack)
    if HAVE_REF and (not folder or not glob.glob(os.path.join(REF, folder, f"*_{_id}.json"))):
        errors.append(f"unverified Companion Compendia link {pack}.{_id}")

# ---- banned dashes
for ch, name in (("—", "em dash"), ("–", "en dash")):
    if ch in blob:
        errors.append(f"{name} found in output")

if MISSING_ICONS:
    errors.append("missing icons: " + ", ".join(sorted(set(MISSING_ICONS))))

if errors:
    print("ERRORS:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

# ---- write module
src_root = os.path.join(MODULE_DIR, "src", "packs")
if os.path.isdir(src_root):
    shutil.rmtree(src_root)
for pack, docs in data.items():
    out = os.path.join(src_root, pack)
    os.makedirs(out, exist_ok=True)
    for d in docs:
        fname = re.sub(r"[^A-Za-z0-9]+", "_", d["name"]).strip("_") + f"_{d['_id']}.json"
        with open(os.path.join(out, fname), "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2, ensure_ascii=False)

manifest = {
    "id": MODULE_ID,
    "title": "Sovereign Class (PF2e Homebrew)",
    "description": "The Sovereign: a ruler who leads a loyal follower, bears regalia, and draws power from their "
                   "court. Includes the class, class features, feats, and effects. Followers come from PF2e "
                   "Companion Compendia.",
    "version": VERSION,
    "authors": [{"name": "Eiko"}],
    "url": REPO,
    "manifest": f"{REPO}/releases/latest/download/module.json",
    "download": f"{REPO}/releases/download/v{VERSION}/module.zip",
    "compatibility": {"minimum": "13", "verified": "14"},
    "relationships": {
        "systems": [{"id": "pf2e", "type": "system", "compatibility": {}}],
        "requires": [{"id": "pf2e-animal-companions", "type": "module", "compatibility": {}}],
    },
    "esmodules": ["scripts/sovereign.mjs"],
    "styles": ["styles/sovereign.css"],
    "packs": [
        {"name": name, "label": f"Sovereign {label}", "path": f"packs/{name}", "type": typ, "system": "pf2e",
         "ownership": {"PLAYER": "OBSERVER", "ASSISTANT": "OWNER"}, "flags": {}}
        for name, label, typ in PACKS
    ],
    "packFolders": [{"name": "Sovereign", "sorting": "m", "color": "#6b4f1d",
                     "packs": [name for name, _, _ in PACKS], "folders": []}],
    "flags": {"canUpload": True},
}
os.makedirs(MODULE_DIR, exist_ok=True)
with open(os.path.join(MODULE_DIR, "module.json"), "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2)

# scripts/ and styles/ are hand-written and live in the repo; build.py does not touch them.

for pack, docs in data.items():
    print(f"{pack}: {len(docs)}")
print("OK")
