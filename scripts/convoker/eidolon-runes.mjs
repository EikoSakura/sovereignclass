// A summoner can Invest a magic weapon to share its fundamental and property runes with their eidolon, but only
// while holding it. pf2e-toolbelt's Shared Data "Weapon Runes" option shares the runes of the summoner's
// invested weapons, yet ordinary weapons can't be invested in pf2e. So, for every summoner with linked
// eidolons, the weapon they're holding (with a potency rune; the best one if several) is invested automatically
// and un-invested when it's put away. Invested handwraps of mighty blows keep working as before.
import { MODULE_ID, eidolonsOf } from "./core.mjs";

const FLAG = "eidolonInvested";

function candidate(summoner) {
  return summoner.itemTypes.weapon
    .filter((w) => w.isHeld && Number(w.system.runes?.potency ?? 0) > 0 && !w.flags?.[MODULE_ID]?.syncedFrom)
    .sort((a, b) => (b.system.runes.potency - a.system.runes.potency)
      || (b.system.runes.striking - a.system.runes.striking)
      || ((b.system.runes.property?.length ?? 0) - (a.system.runes.property?.length ?? 0)))[0] ?? null;
}

export async function syncInvestedWeapon(summoner) {
  if (!summoner?.isOwner || !summoner.isOfType?.("character")) return;
  const hasEidolons = eidolonsOf(summoner).length > 0;
  const pick = hasEidolons ? candidate(summoner) : null;
  const updates = [];
  for (const weapon of summoner.itemTypes.weapon) {
    const flag = weapon.flags?.[MODULE_ID]?.[FLAG];
    const traits = weapon._source.system.traits?.value ?? [];
    if (weapon === pick) {
      const update = { _id: weapon.id };
      if (!traits.includes("invested")) {
        update["system.traits.value"] = [...traits, "invested"];
        update[`flags.${MODULE_ID}.${FLAG}`] = { addedTrait: true };
      } else if (!flag) {
        update[`flags.${MODULE_ID}.${FLAG}`] = { addedTrait: false };
      }
      if (!weapon._source.system.equipped?.invested) update["system.equipped.invested"] = true;
      if (Object.keys(update).length > 1) updates.push(update);
    } else if (flag) {
      // Put away (or replaced by a better weapon): undo what was done for the eidolon.
      const update = { _id: weapon.id, "system.equipped.invested": false, [`flags.${MODULE_ID}.-=${FLAG}`]: null };
      if (flag.addedTrait) update["system.traits.value"] = traits.filter((t) => t !== "invested");
      updates.push(update);
    }
  }
  if (updates.length) await summoner.updateEmbeddedDocuments("Item", updates);
}

const timers = new Map();
export function scheduleInvestedWeaponSync(summoner) {
  if (!summoner?.isOwner) return;
  clearTimeout(timers.get(summoner.id));
  timers.set(summoner.id, setTimeout(() => {
    timers.delete(summoner.id);
    syncInvestedWeapon(summoner).catch((err) => console.error(`${MODULE_ID} | eidolon weapon sync failed`, err));
  }, 500));
}
