// Soaring Blade (Martial Memoires) automation.
//
// The Favored Blade is the weapon tagged `favored-blade` (feather toggle in the inventory). Bladework Stance's
// effect badge counts the blades flying above you. A small ledger on the actor
// (`flags.pf2e-sovereign.soaring`) remembers where the others went: thrown out, stuck in enemies (Impaling
// Strikes), placed (Battlefield Control), dropped on a target (Raining Assault), or ridden (Blade Surfing).
const MODULE_ID = "pf2e-sovereign";
const TAG = "favored-blade";
const NATIVE_TAG = "favored-blade-thrown";
const DEDICATION = "soaring-blade-dedication";
const STANCE = "stance-bladework-stance";
const SURFING = "effect-blade-surfing";
const PLACED = "effect-battlefield-blade";
const PACK = `${MODULE_ID}.martial-memoires`;
const CARD = `${MODULE_ID}-card`;

const mine = (userId) => userId === game.user.id;
const esc = (s) => foundry.utils.escapeHTML(String(s ?? ""));
const notify = (msg, type = "info") => ui.notifications[type](`Soaring Blade | ${msg}`);

// ============================================================================================================ lookups
function hasFeat(actor, slug) {
  return actor?.itemTypes?.feat?.some((f) => f.slug === slug) ?? false;
}

function isFavored(weapon) {
  return (weapon._source.system.traits?.otherTags ?? []).includes(TAG);
}

export function favoredBlade(actor) {
  return actor?.itemTypes?.weapon?.find(isFavored) ?? null;
}

function stanceOf(actor) {
  return actor?.itemTypes?.effect?.find((e) => e.slug === STANCE) ?? null;
}

function maxBlades(actor) {
  const blade = favoredBlade(actor);
  return blade ? Math.max(1, Number(blade.system.damage?.dice ?? 1)) : 1;
}

function ledger(actor) {
  const raw = actor.getFlag(MODULE_ID, "soaring") ?? {};
  return { stuck: { ...(raw.stuck ?? {}) }, placed: raw.placed ?? 0, out: raw.out ?? 0, fallen: raw.fallen ?? null };
}

async function saveLedger(actor, data) {
  await actor.update({ [`flags.${MODULE_ID}.soaring`]: data }, { render: false });
}

function flying(actor) {
  return Number(stanceOf(actor)?.system.badge?.value ?? 0);
}

async function setFlying(actor, value) {
  const stance = stanceOf(actor);
  if (!stance) return;
  const v = Math.clamp(Math.round(value), 0, maxBlades(actor));
  if (stance.system.badge?.value !== v) await stance.update({ "system.badge.value": v });
}

// Every blade that isn't flying comes back (a surfing blade stays under your feet).
async function recallAll(actor) {
  const surfing = actor.itemTypes.effect.some((e) => e.slug === SURFING) ? 1 : 0;
  const placed = actor.itemTypes.effect.filter((e) => e.slug === PLACED).map((e) => e.id);
  if (placed.length) await actor.deleteEmbeddedDocuments("Item", placed, { soaringRecall: true });
  await saveLedger(actor, { stuck: {}, placed: 0, out: 0, fallen: null });
  await setFlying(actor, maxBlades(actor) - surfing);
}

function soaringDC(actor) {
  const classDCs = Object.values(actor.classDCs ?? {}).map((s) => s?.dc?.value ?? 0);
  const spellDCs = (actor.spellcasting?.contents ?? []).map((e) => e.statistic?.dc?.value ?? 0);
  return Math.max(0, ...classDCs, ...spellDCs) || null;
}

function bladeDamage(actor) {
  const blade = favoredBlade(actor);
  if (!blade) return null;
  const dice = Math.max(1, Number(blade.system.damage?.dice ?? 1));
  const die = blade.system.damage?.die ?? "d4";
  const type = blade.system.damage?.damageType ?? "slashing";
  return { formula: `${dice}${die}`, type, blade };
}

function toggle(actor, option, value) {
  const holder = actor.items.find((i) => (i.system.rules ?? []).some((r) => r.key === "RollOption" && r.option === option));
  if (!holder) return;
  return actor.toggleRollOption("all", option, holder.id, value);
}

async function postCard(actor, title, body, flags = {}) {
  return ChatMessage.implementation.create({
    speaker: ChatMessage.implementation.getSpeaker({ actor }),
    content: `<div class="${CARD}"><header><i class="fa-solid fa-feather-pointed"></i> ${esc(title)}</header>${body}</div>`,
    flags: { [MODULE_ID]: flags },
  });
}

// ============================================================================================================ favored blade
function nativelyThrown(weapon) {
  const traits = weapon._source.system.traits?.value ?? [];
  return weapon.isRanged || traits.some((t) => t === "thrown" || /^thrown-\d+$/.test(t));
}

// Moves the favored-blade tag to the clicked weapon (or clears it), tagging whether it can already be thrown.
async function setFavoredBlade(actor, weaponId) {
  const updates = [];
  let chosen = null;
  for (const weapon of actor.itemTypes.weapon) {
    const tags = (weapon._source.system.traits?.otherTags ?? []).filter((t) => t !== TAG && t !== NATIVE_TAG);
    const had = isFavored(weapon);
    const want = weapon.id === weaponId ? !had : false;
    if (want) {
      chosen = weapon;
      tags.push(TAG);
      if (nativelyThrown(weapon)) tags.push(NATIVE_TAG);
    }
    if (want !== had || want) updates.push({ _id: weapon.id, "system.traits.otherTags": tags });
  }
  if (updates.length) await actor.updateEmbeddedDocuments("Item", updates);
  // Focused Parry's +2 applies when the Favored Blade already had parry.
  if (hasFeat(actor, "focused-parry")) {
    const parry = !!chosen && (chosen._source.system.traits?.value ?? []).includes("parry");
    await toggle(actor, "focused-parry-native", parry);
  }
  if (stanceOf(actor)) await setFlying(actor, Math.min(flying(actor), maxBlades(actor)));
}

Hooks.on("renderCharacterSheetPF2e", (app, html) => {
  const actor = app.actor;
  if (!hasFeat(actor, DEDICATION)) return;
  const root = html instanceof HTMLElement ? html : html?.[0];
  if (!root) return;
  for (const row of root.querySelectorAll(".tab.inventory li[data-item-id]")) {
    const weapon = actor.items.get(row.dataset.itemId);
    if (!weapon?.isOfType("weapon")) continue;
    const active = isFavored(weapon);
    if (!app.isEditable && !active) continue;
    const el = document.createElement("a");
    el.classList.add(`${MODULE_ID}-favored-blade`);
    if (active) el.classList.add("active");
    el.dataset.tooltip = active ? "Favored Blade" : "Set as Favored Blade";
    el.innerHTML = '<i class="fa-solid fa-feather-pointed fa-fw"></i>';
    if (app.isEditable) {
      el.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        setFavoredBlade(actor, weapon.id);
      });
    } else el.classList.add("readonly");
    const controls = row.querySelector(".item-controls");
    const name = row.querySelector(".item-name h4");
    if (controls) controls.prepend(el);
    else if (name) name.append(el);
  }
});

// ============================================================================================================ abilities
async function damageSaveCard(actor, title, text, { mapSteps = false, recall = false } = {}) {
  const dmg = bladeDamage(actor);
  if (!dmg) return notify("Mark your Favored Blade in the inventory first.", "warn");
  const dc = soaringDC(actor);
  const damage = `@Damage[${dmg.formula}[${dmg.type}]|options:area-damage]`;
  let saves;
  if (!dc) saves = "@Check[reflex|basic]";
  else if (mapSteps) {
    const agile = dmg.blade.system.traits?.value?.includes("agile");
    const steps = agile ? [0, -4, -8] : [0, -5, -10];
    saves = steps.map((m, i) => `${["First attack", "Second attack", "Third or later"][i]}: @Check[reflex|dc:${dc + m}|basic|name:${title}]`).join("<br>");
  } else saves = `@Check[reflex|dc:${dc}|basic|name:${title}]`;
  await postCard(actor, title, `<p>${text}</p><p>${damage}</p><p>${saves}</p>`);
  if (recall) await recallAll(actor);
}

async function rendingRecall(actor) {
  const { stuck } = ledger(actor);
  const dc = soaringDC(actor);
  const rows = Object.entries(stuck).filter(([, n]) => n > 0).map(([uuid, n]) => {
    const name = fromUuidSync(uuid)?.name ?? "A creature";
    const check = dc ? `@Check[fortitude|dc:${dc}|basic|name:Rending Recall]` : "@Check[fortitude|basic]";
    return `<li><strong>${esc(name)}</strong> (${n} blade${n === 1 ? "" : "s"}): @Damage[(${n}d6+${n})[persistent,bleed]] ${check}</li>`;
  });
  const body = rows.length
    ? `<p>The blades tear free.</p><ul>${rows.join("")}</ul>`
    : "<p>No blades were stuck in an enemy.</p>";
  await postCard(actor, "Rending Recall", body);
  await recallAll(actor);
}

async function commandBlades(actor) {
  if (!stanceOf(actor)) return notify("You need to be in Bladework Stance.", "warn");
  const l = ledger(actor);
  const max = maxBlades(actor);
  const cur = flying(actor);
  const stuck = Object.entries(l.stuck).filter(([, n]) => n > 0)
    .map(([uuid, n]) => `${esc(fromUuidSync(uuid)?.name ?? "a creature")} (${n})`).join(", ");
  const content = `<div class="${MODULE_ID}-dialog">
    <p><strong>${cur}</strong> of ${max} blades are flying above you.</p>
    ${stuck ? `<p class="hint">Stuck in: ${stuck}</p>` : ""}
    ${l.placed ? `<p class="hint">Placed with Battlefield Control: ${l.placed}</p>` : ""}
    ${l.fallen ? `<p class="hint">Fallen at ${esc(l.fallen)}</p>` : ""}
    <label class="${MODULE_ID}-check">Send out <input type="number" name="send" value="1" min="1" max="${Math.max(cur, 1)}" style="width:4em"> blade(s) to a spot within your first range increment</label>
  </div>`;
  const choice = await foundry.applications.api.DialogV2.wait({
    window: { title: "Command Blades", icon: "fa-solid fa-feather-pointed" },
    content,
    buttons: [
      { action: "recall", label: "Recall all", icon: "fa-solid fa-rotate-left", default: true },
      { action: "send", label: "Send out", icon: "fa-solid fa-paper-plane",
        callback: (_e, button) => ({ send: Number(button.form.elements.send.value) || 1 }) },
      { action: "cancel", label: "Cancel" },
    ],
    rejectClose: false,
  });
  if (choice === "recall") {
    await recallAll(actor);
    await postCard(actor, "Command Blades", "<p>Every blade returns to fly above you.</p>");
  } else if (choice?.send) {
    const n = Math.min(choice.send, cur);
    await setFlying(actor, cur - n);
    await saveLedger(actor, { ...l, out: l.out + n });
    await postCard(actor, "Command Blades", `<p>${n} blade${n === 1 ? "" : "s"} fly off to a spot within range.</p>`);
  }
}

const USE = {
  "command-blades": commandBlades,
  "slashing-recall": (a) => damageSaveCard(a, "Slashing Recall",
    "Every blade streaks back. Creatures in the lines between you and where the blades were take this damage once.",
    { recall: true }),
  "blade-spin": (a) => damageSaveCard(a, "Blade Spin", "Creatures within your Favored Blade's reach take this damage.",
    { mapSteps: true }),
  "sharp-steps": (a) => damageSaveCard(a, "Sharp Steps",
    "You recover the blade and spin. Creatures within your Favored Blade's reach take this damage.", { mapSteps: true }),
  "rending-recall": rendingRecall,
  async "raining-assault"(a) {
    await a.setFlag(MODULE_ID, "pending", "raining-assault");
    await toggle(a, "soaring-blade-splash", true);
    notify("Splash is on for your next Strike with the Favored Blade.");
  },
  async "downpour-of-steel"(a) {
    await toggle(a, "soaring-blade-splash", true);
    await postCard(a, "Downpour of Steel",
      `<p>Make a thrown Strike against each foe within your blade's first range increment. Splash is on; each enemy takes it only once. Your multiple attack penalty doesn't grow until you've made every attack.</p>
       <button type="button" data-soaring="finish-downpour" data-actor="${a.id}"><i class="fa-solid fa-flag-checkered"></i> Finish (leave Bladework Stance)</button>`);
  },
  async "true-blades-strike"(a) {
    await a.setFlag(MODULE_ID, "pending", "true-blades-strike");
    await toggle(a, "true-blades-strike", true);
    notify("True Blade's Strike is on for your next Strike with the Favored Blade.");
  },
  async "battlefield-control"(a) {
    if (flying(a) < 1) return notify("No blades are flying above you to place.", "warn");
    const data = (await game.packs.get(PACK)?.getDocuments({ name: "Effect: Battlefield Blade" }))?.[0]?.toObject();
    await setFlying(a, flying(a) - 1);
    const l = ledger(a);
    await saveLedger(a, { ...l, placed: l.placed + 1 });
    if (data) {
      delete data._id;
      await a.createEmbeddedDocuments("Item", [data]);
    }
  },
};

// ============================================================================================================ hooks
Hooks.on("createChatMessage", async (message, _options, userId) => {
  if (!mine(userId)) return;
  const actor = message.actor;
  if (!actor || !hasFeat(actor, DEDICATION)) return;
  const context = message.flags?.pf2e?.context;

  // Using one of the archetype's actions.
  if (!context?.type) {
    const handler = USE[message.item?.slug];
    if (handler && ["feat", "action"].includes(message.item.type)) await handler(actor);
    return;
  }

  const options = context.options ?? [];
  const favored = options.includes(`item:tag:${TAG}`);
  if (!favored || !stanceOf(actor)) return;

  if (context.type === "attack-roll") {
    const pending = actor.getFlag(MODULE_ID, "pending");
    const targetUuid = context.target?.token ?? context.target?.actor ?? null;
    const targetName = targetUuid ? fromUuidSync(targetUuid)?.name : null;
    const hit = ["success", "criticalSuccess"].includes(context.outcome);

    // Raining Assault: after the Strike every flying blade falls in the target's space.
    if (pending === "raining-assault") {
      const l = ledger(actor);
      await saveLedger(actor, { ...l, fallen: targetName ?? "the target", out: l.out + flying(actor) });
      await setFlying(actor, 0);
      await toggle(actor, "soaring-blade-splash", false);
      await actor.unsetFlag(MODULE_ID, "pending");
      return;
    }

    // A thrown copy leaves the stance (unless a returning rune brings it straight back).
    const thrown = options.includes("item:thrown");
    const returning = message.item?.system?.runes?.property?.includes?.("returning");
    if (thrown && !returning && flying(actor) > 0) {
      await setFlying(actor, flying(actor) - 1);
      const l = ledger(actor);
      if (hit && targetUuid && hasFeat(actor, "impaling-strikes")) {
        l.stuck[targetUuid] = (l.stuck[targetUuid] ?? 0) + 1;
      } else l.out += 1;
      await saveLedger(actor, l);
    }
  }

  // True Blade's Strike ends the stance once its damage is rolled.
  if (context.type === "damage-roll" && options.includes("true-blades-strike")) {
    await actor.unsetFlag(MODULE_ID, "pending");
    const stance = stanceOf(actor);
    if (stance) await stance.delete();
  }
});

Hooks.on("renderChatMessageHTML", (message, html) => {
  const button = html.querySelector?.('[data-soaring="finish-downpour"]');
  if (!button) return;
  const actor = game.actors.get(button.dataset.actor);
  if (!actor?.isOwner || !stanceOf(actor)) {
    button.disabled = true;
    return;
  }
  button.addEventListener("click", async (event) => {
    event.preventDefault();
    button.disabled = true;
    await toggle(actor, "soaring-blade-splash", false);
    await stanceOf(actor)?.delete();
  });
});

Hooks.on("createItem", async (item, _options, userId) => {
  if (!mine(userId) || item.type !== "effect" || !item.actor) return;
  const actor = item.actor;
  if (item.slug === STANCE) {
    if (!favoredBlade(actor)) return notify("Mark your Favored Blade in the inventory (the feather on its row).", "warn");
    await saveLedger(actor, { stuck: {}, placed: 0, out: 0, fallen: null });
    const surfing = actor.itemTypes.effect.some((e) => e.slug === SURFING) ? 1 : 0;
    await setFlying(actor, maxBlades(actor) - surfing);
  } else if (item.slug === SURFING && stanceOf(actor)) {
    await setFlying(actor, flying(actor) - 1);
  }
});

Hooks.on("deleteItem", async (item, options, userId) => {
  if (!mine(userId) || item.type !== "effect" || !item.actor) return;
  const actor = item.actor;
  if (item.slug === STANCE) {
    await saveLedger(actor, { stuck: {}, placed: 0, out: 0, fallen: null });
    if (actor.getFlag(MODULE_ID, "pending")) await actor.unsetFlag(MODULE_ID, "pending");
  } else if (item.slug === SURFING && stanceOf(actor)) {
    await setFlying(actor, flying(actor) + 1);
  } else if (item.slug === PLACED && !options?.soaringRecall && stanceOf(actor)) {
    // The placed blade's minute is up: it flies back.
    const l = ledger(actor);
    await saveLedger(actor, { ...l, placed: Math.max(0, l.placed - 1) });
    await setFlying(actor, flying(actor) + 1);
  }
});
