const MODULE_ID = "pf2e-sovereign";
const REGALIA_TAG = "regalia-weapon";
const WEAPON_REGALIA_SLUG = "weapon-regalia";

// Extra base weapon types missing from the pf2e system.
const BASE_WEAPONS = {
  "chain-blade": "Chain Blade",
};

// Registers the Sovereign trait so class feats filter correctly in the pf2e feat browser,
// and adds the extra base weapons to the weapon sheet's Base Weapon list.
Hooks.once("init", () => {
  const PF2E = CONFIG.PF2E;
  if (!PF2E) return;
  for (const key of ["classTraits", "featTraits", "actionTraits"]) {
    if (PF2E[key]) PF2E[key].sovereign = "Sovereign";
  }
  if (PF2E.traitsDescriptions) {
    PF2E.traitsDescriptions.sovereign = "Abilities with this trait come from the sovereign class.";
  }
  if (PF2E.baseWeaponTypes) {
    for (const [slug, label] of Object.entries(BASE_WEAPONS)) PF2E.baseWeaponTypes[slug] ??= label;
  }
});

function hasWeaponRegalia(actor) {
  return actor?.itemTypes?.feat?.some((f) => f.slug === WEAPON_REGALIA_SLUG) ?? false;
}

function isRegalia(weapon) {
  return (weapon._source.system.traits?.otherTags ?? []).includes(REGALIA_TAG);
}

// Moves the regalia tag to the clicked weapon, or clears it when the active weapon is clicked again.
async function setRegaliaWeapon(actor, weaponId) {
  const updates = [];
  for (const weapon of actor.itemTypes.weapon) {
    const tags = weapon._source.system.traits?.otherTags ?? [];
    const has = tags.includes(REGALIA_TAG);
    const want = weapon.id === weaponId ? !has : false;
    if (has === want) continue;
    updates.push({
      _id: weapon.id,
      "system.traits.otherTags": want ? [...tags, REGALIA_TAG] : tags.filter((t) => t !== REGALIA_TAG),
    });
  }
  if (updates.length) await actor.updateEmbeddedDocuments("Item", updates);
}

// Adds a crown to each weapon row in the inventory of a sovereign with Weapon Regalia.
Hooks.on("renderCharacterSheetPF2e", (app, html) => {
  const actor = app.actor;
  if (!hasWeaponRegalia(actor)) return;
  const root = html instanceof HTMLElement ? html : html?.[0];
  if (!root) return;

  for (const row of root.querySelectorAll(".tab.inventory li[data-item-id]")) {
    const weapon = actor.items.get(row.dataset.itemId);
    if (!weapon?.isOfType("weapon")) continue;

    const active = isRegalia(weapon);
    if (!app.isEditable && !active) continue;

    const crown = document.createElement("a");
    crown.classList.add(`${MODULE_ID}-crown`);
    if (active) crown.classList.add("active");
    crown.dataset.tooltip = active ? "Regalia Weapon" : "Set as Regalia";
    crown.innerHTML = '<i class="fa-solid fa-crown fa-fw"></i>';

    if (app.isEditable) {
      crown.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        setRegaliaWeapon(actor, weapon.id);
      });
    } else {
      crown.classList.add("readonly");
    }

    const controls = row.querySelector(".item-controls");
    const name = row.querySelector(".item-name h4");
    if (controls) controls.prepend(crown);
    else if (name) name.append(crown);
  }
});
