// PF2e Leveler only offers content from the compendiums enabled in its settings (pf2e's own by default).
// Once per world, the GM's client adds Summons Unleashed to Leveler's Class Features (Convoker Assembly and the
// new eidolons) and Feats (Convoker archetype feats) lists. A GM who removes it later is respected.
import { MODULE_ID, SU_PACK, notify } from "./core.mjs";

const LEVELER = "pf2e-leveler";
const CATEGORIES = ["classFeatures", "feats"];

export function registerLevelerSetting() {
  game.settings.register(MODULE_ID, "levelerRegistered", {
    scope: "world",
    config: false,
    type: Boolean,
    default: false,
  });
}

function addKeys(selections) {
  const out = foundry.utils.deepClone(selections ?? {});
  for (const category of CATEGORIES) {
    const keys = Array.isArray(out[category]) ? out[category] : [];
    out[category] = [...new Set([...keys, SU_PACK])];
  }
  return out;
}

export async function registerWithLeveler() {
  if (!game.modules.get(LEVELER)?.active || !game.packs.get(SU_PACK)) return;
  if (game.users.activeGM?.id !== game.user.id) return;
  if (game.settings.get(MODULE_ID, "levelerRegistered")) return;
  try {
    await game.settings.set(LEVELER, "customCompendiums", addKeys(game.settings.get(LEVELER, "customCompendiums")));
    // If the GM limits which compendiums players can use in Leveler, allow this one there too.
    const access = game.settings.get(LEVELER, "playerCompendiumAccess");
    if (access && typeof access === "object" && access.selections) {
      await game.settings.set(LEVELER, "playerCompendiumAccess", { ...access, selections: addKeys(access.selections) });
    }
    await game.settings.set(MODULE_ID, "levelerRegistered", true);
    notify("Added Summons Unleashed (Convoker and new eidolons) to PF2e Leveler's compendiums.");
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
