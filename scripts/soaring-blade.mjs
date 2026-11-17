// Soaring Blade (Martial Memoires): mark the Favored Blade from the inventory, and count the blades flying above
// you when you enter Bladework Stance.
const MODULE_ID = "pf2e-sovereign";
const TAG = "favored-blade";
const DEDICATION = "soaring-blade-dedication";
const STANCE = "stance-bladework-stance";

function hasDedication(actor) {
  return actor?.itemTypes?.feat?.some((f) => f.slug === DEDICATION) ?? false;
}

function isFavored(weapon) {
  return (weapon._source.system.traits?.otherTags ?? []).includes(TAG);
}

export function favoredBlade(actor) {
  return actor?.itemTypes?.weapon?.find(isFavored) ?? null;
}

// Moves the favored-blade tag to the clicked weapon, or clears it when the current one is clicked again.
async function setFavoredBlade(actor, weaponId) {
  const updates = [];
  for (const weapon of actor.itemTypes.weapon) {
    const tags = weapon._source.system.traits?.otherTags ?? [];
    const has = tags.includes(TAG);
    const want = weapon.id === weaponId ? !has : false;
    if (has === want) continue;
    updates.push({
      _id: weapon.id,
      "system.traits.otherTags": want ? [...tags, TAG] : tags.filter((t) => t !== TAG),
    });
  }
  if (updates.length) await actor.updateEmbeddedDocuments("Item", updates);
}

Hooks.on("renderCharacterSheetPF2e", (app, html) => {
  const actor = app.actor;
  if (!hasDedication(actor)) return;
  const root = html instanceof HTMLElement ? html : html?.[0];
  if (!root) return;

  for (const row of root.querySelectorAll(".tab.inventory li[data-item-id]")) {
    const weapon = actor.items.get(row.dataset.itemId);
    if (!weapon?.isOfType("weapon")) continue;
    const active = isFavored(weapon);
    if (!app.isEditable && !active) continue;

    const toggle = document.createElement("a");
    toggle.classList.add(`${MODULE_ID}-favored-blade`);
    if (active) toggle.classList.add("active");
    toggle.dataset.tooltip = active ? "Favored Blade" : "Set as Favored Blade";
    toggle.innerHTML = '<i class="fa-solid fa-feather-pointed fa-fw"></i>';
    if (app.isEditable) {
      toggle.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        setFavoredBlade(actor, weapon.id);
      });
    } else {
      toggle.classList.add("readonly");
    }
    const controls = row.querySelector(".item-controls");
    const name = row.querySelector(".item-name h4");
    if (controls) controls.prepend(toggle);
    else if (name) name.append(toggle);
  }
});

// Entering Bladework Stance: one blade per weapon damage die of the Favored Blade (striking runes included).
Hooks.on("createItem", async (item, _options, userId) => {
  if (userId !== game.user.id || item.type !== "effect" || item.slug !== STANCE) return;
  const actor = item.actor;
  if (!actor) return;
  const blade = favoredBlade(actor);
  if (!blade) {
    ui.notifications.warn("Soaring Blade | Mark your Favored Blade in the inventory (the feather on its row).");
    return;
  }
  const dice = Math.max(1, Number(blade.system.damage?.dice ?? 1));
  if (item.system.badge?.type === "counter" && item.system.badge.value !== dice) {
    await item.update({ "system.badge.value": dice });
  }
});
