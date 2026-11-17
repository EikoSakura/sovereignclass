// PF2e Leveler only offers content from the compendiums enabled in its settings (pf2e's own by default).
// The GM's client adds each Sovereign homebrew pack to the right Leveler categories once per world; a pack the
// GM removes later is respected (it's remembered as registered).
import { MODULE_ID, SU_PACK, notify } from "./core.mjs";

const LEVELER = "pf2e-leveler";
const REGISTRATIONS = [
  { pack: SU_PACK, categories: ["classFeatures", "feats"], label: "Summons Unleashed (Convoker and new eidolons)" },
  { pack: `${MODULE_ID}.martial-memoires`, categories: ["feats"], label: "Martial Memoires (Soaring Blade)" },
];

export function registerLevelerSetting() {
  game.settings.register(MODULE_ID, "levelerRegistered", { scope: "world", config: false, type: Boolean, default: false });
  game.settings.register(MODULE_ID, "levelerRegisteredPacks", { scope: "world", config: false, type: Array, default: [] });
}

function addKeys(selections, reg) {
  const out = foundry.utils.deepClone(selections ?? {});
  for (const category of reg.categories) {
    const keys = Array.isArray(out[category]) ? out[category] : [];
    out[category] = [...new Set([...keys, reg.pack])];
  }
  return out;
}

export async function registerWithLeveler() {
  if (!game.modules.get(LEVELER)?.active || game.users.activeGM?.id !== game.user.id) return;
  const done = new Set(game.settings.get(MODULE_ID, "levelerRegisteredPacks") ?? []);
  if (game.settings.get(MODULE_ID, "levelerRegistered")) done.add(SU_PACK);
  const todo = REGISTRATIONS.filter((r) => !done.has(r.pack) && game.packs.get(r.pack));
  if (!todo.length) return;
  try {
    let custom = game.settings.get(LEVELER, "customCompendiums");
    let access = game.settings.get(LEVELER, "playerCompendiumAccess");
    for (const reg of todo) {
      custom = addKeys(custom, reg);
      // If the GM limits which compendiums players can use in Leveler, allow this one there too.
      if (access && typeof access === "object" && access.selections) access = { ...access, selections: addKeys(access.selections, reg) };
      done.add(reg.pack);
    }
    await game.settings.set(LEVELER, "customCompendiums", custom);
    if (access?.selections) await game.settings.set(LEVELER, "playerCompendiumAccess", access);
    await game.settings.set(MODULE_ID, "levelerRegisteredPacks", [...done]);
    await game.settings.set(MODULE_ID, "levelerRegistered", true);
    notify(`Added ${todo.map((r) => r.label).join(" and ")} to PF2e Leveler's compendiums.`);
  } catch (err) {
    console.warn(`${MODULE_ID} | Couldn't register with PF2e Leveler`, err);
  }
}

// Leveler works out a subclass's tradition from its own data table (or, failing that, the first tradition word in
// the item's text, which reads "arcane" for Convoker Assembly). Teach it that Convoker Assembly's tradition is the
// item's tradition choice, so its spell step, spell list and spell entry use the tradition you picked.
export async function patchLevelerSubclassData() {
  if (!game.modules.get(LEVELER)?.active) return;
  try {
    const url = foundry.utils.getRoute(`modules/${LEVELER}/scripts/data/subclass-spells.js`);
    const data = await import(url);
    if (!data?.SUBCLASS_SPELLS || data.SUBCLASS_SPELLS["convoker-assembly"]) return;
    data.SUBCLASS_SPELLS["convoker-assembly"] = {
      choiceFlag: "convokerTradition",
      choiceOptions: ["arcane", "divine", "occult", "primal"].map((t) => ({ slug: t, tradition: t })),
    };
  } catch (err) {
    console.warn(`${MODULE_ID} | Couldn't teach PF2e Leveler the Convoker's tradition`, err);
  }
}
