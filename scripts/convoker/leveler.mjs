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
