// Convoker assembly: data model, compendium lookups, GM relay, and eidolon actor management.
// The summoner stores `flags.pf2e-sovereign.assembly = { slots: [actorId|null, ...], primary: actorId|null }`.
// Each eidolon actor stores `flags.pf2e-sovereign.convoker = summonerId`.

export const MODULE_ID = "pf2e-sovereign";
export const SU_PACK = `${MODULE_ID}.summons-unleashed`;
export const EI_PACK = `${MODULE_ID}.su-eidolons`;
export const CC_EIDOLON_PACK = "pf2e-animal-companions.AC-Eidolons";

export const FEAT = {
  assembly: "convoker-assembly",
  dedication: "convoker-dedication",
  assemblyEvolution: "assembly-evolution",
  assembledAssault: "assembled-assault",
  expanded: "expanded-assemblage",
  warping: "warping-convoke",
  combination: "combination-convocation",
};
export const SPELL = { convoke: "convoke", assault: "assembled-assault", combination: "combination-convocation" };
export const EFFECT = {
  convoked: "Effect: Convoked",
  fusion: "Effect: Combination Convocation",
  fusionSize: "Effect: Combination Convocation (Greater Size)",
};
export const BOOST_EIDOLON_SLUG = "spell-effect-boost-eidolon";
const EVOLUTION_SURGE = "Compendium.pf2e.spells-srd.Item.lV8FkHZtzZu7Cy6j";

// Feats that hand the convoker a focus spell.
export const FEAT_SPELLS = {
  [FEAT.dedication]: { pack: SU_PACK, name: "Convoke" },
  [FEAT.assemblyEvolution]: { uuid: EVOLUTION_SURGE },
  [FEAT.assembledAssault]: { pack: SU_PACK, name: "Assembled Assault" },
  [FEAT.combination]: { pack: SU_PACK, name: "Combination Convocation" },
};

export const TRADITION_SKILLS = { arcane: "arcana", divine: "religion", occult: "occultism", primal: "nature" };

// ---------------------------------------------------------------------------------------------------------------- utils
export const localizeLabel = (s) => foundry.utils.escapeHTML(String(s ?? ""));
export const notify = (msg, type = "info") => ui.notifications[type](`Convoker | ${msg}`);
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function packUuid(packId, name, type = null) {
  const pack = game.packs.get(packId);
  if (!pack) return null;
  const index = await pack.getIndex({ fields: ["type"] });
  const hit = index.find((e) => e.name === name && (!type || e.type === type));
  return hit?.uuid ?? null;
}

export async function packDocData(packId, name, type = null) {
  const uuid = await packUuid(packId, name, type);
  if (!uuid) return null;
  const doc = await fromUuid(uuid);
  if (!doc) return null;
  const data = doc.toObject();
  delete data._id;
  data._stats = { ...(data._stats ?? {}), compendiumSource: uuid };
  return data;
}

export function stripGrantFlags(data) {
  delete data._id;
  if (data.flags?.pf2e) {
    delete data.flags.pf2e.grantedBy;
    delete data.flags.pf2e.itemGrants;
  }
  return data;
}

// ---------------------------------------------------------------------------------------------------------------- GM relay
// Players often can't create actors/tokens or delete tokens. These calls fall back to the active GM.
const pending = new Map();

const GM_HANDLERS = {
  async createActor({ data }) {
    const actor = await Actor.implementation.create(data);
    return actor?.id ?? null;
  },
  async createTokens({ sceneId, data }) {
    const scene = game.scenes.get(sceneId);
    const docs = await scene.createEmbeddedDocuments("Token", data);
    return docs.map((d) => d.id);
  },
  async deleteTokens({ sceneId, ids }) {
    const scene = game.scenes.get(sceneId);
    await scene.deleteEmbeddedDocuments("Token", ids.filter((id) => scene.tokens.has(id)));
    return true;
  },
  async moveToken({ sceneId, tokenId, x, y }) {
    const token = game.scenes.get(sceneId)?.tokens.get(tokenId);
    await token?.move({ x, y, action: "blink" }, { constrainOptions: { ignoreWalls: true, ignoreCost: true } });
    return true;
  },
  async swapCombatant({ combatId, combatantId, tokenId, actorId, sceneId }) {
    const combat = game.combats.get(combatId);
    const old = combat?.combatants.get(combatantId);
    if (!old) return false;
    const data = old.toObject();
    delete data._id;
    Object.assign(data, { tokenId, actorId, sceneId });
    const isTurn = combat.combatant?.id === combatantId;
    const [created] = await combat.createEmbeddedDocuments("Combatant", [data]);
    await combat.deleteEmbeddedDocuments("Combatant", [combatantId]);
    if (isTurn && created) {
      const turn = combat.turns.findIndex((c) => c.id === created.id);
      if (turn >= 0) await combat.update({ turn });
    }
    return true;
  },
};

export function registerSocket() {
  game.socket.on(`module.${MODULE_ID}`, async (msg) => {
    if (msg?.type === "response" && msg.userId === game.user.id) {
      const p = pending.get(msg.requestId);
      if (!p) return;
      pending.delete(msg.requestId);
      msg.error ? p.reject(new Error(msg.error)) : p.resolve(msg.result);
      return;
    }
    if (msg?.type !== "request" || game.users.activeGM?.id !== game.user.id) return;
    const handler = GM_HANDLERS[msg.action];
    let result = null;
    let error = null;
    try {
      result = handler ? await handler(msg.args) : null;
      if (!handler) error = `Unknown action ${msg.action}`;
    } catch (err) {
      console.error(err);
      error = err.message;
    }
    game.socket.emit(`module.${MODULE_ID}`, { type: "response", requestId: msg.requestId, userId: msg.userId, result, error });
  });
}

export async function asGM(action, args) {
  if (game.user.isGM) return GM_HANDLERS[action](args);
  if (!game.users.activeGM) throw new Error("A GM needs to be logged in for this.");
  const requestId = foundry.utils.randomID();
  return new Promise((resolve, reject) => {
    pending.set(requestId, { resolve, reject });
    game.socket.emit(`module.${MODULE_ID}`, { type: "request", action, args, requestId, userId: game.user.id });
    setTimeout(() => {
      if (pending.delete(requestId)) reject(new Error("The GM didn't respond."));
    }, 20000);
  });
}

export async function waitForActor(id, tries = 40) {
  for (let i = 0; i < tries; i++) {
    const a = game.actors.get(id);
    if (a) return a;
    await sleep(100);
  }
  return null;
}

// ---------------------------------------------------------------------------------------------------------------- assembly model
export function isConvoker(actor) {
  return !!actor?.isOfType?.("character") && actor.itemTypes.feat.some((f) => f.slug === FEAT.assembly);
}

export function hasFeat(actor, slug) {
  return !!actor?.itemTypes?.feat?.some((f) => f.slug === slug);
}

export function getConvoker(eidolon) {
  const id = eidolon?.getFlag?.(MODULE_ID, "convoker");
  return id ? game.actors.get(id) ?? null : null;
}

export function slotCount(actor) {
  return 3 + actor.itemTypes.feat.filter((f) => f.slug === FEAT.expanded).length;
}

export function getState(actor) {
  const raw = actor.getFlag(MODULE_ID, "assembly") ?? {};
  const count = slotCount(actor);
  const length = Math.max(count, raw.slots?.length ?? 0);
  const slots = Array.from({ length }, (_, i) => raw.slots?.[i] ?? null);
  const types = Array.from({ length }, (_, i) => raw.types?.[i] ?? null);
  return { slots, types, primary: raw.primary ?? null };
}

export async function saveState(actor, state) {
  await actor.update({
    [`flags.${MODULE_ID}.assembly`]: { slots: state.slots, types: state.types ?? [], primary: state.primary },
  });
}

// Chooses which eidolon a slot holds (an eidolon ancestry uuid), before or instead of creating its actor.
export async function setSlotType(actor, index, uuid) {
  const state = getState(actor);
  state.types[index] = uuid || null;
  await saveState(actor, state);
}

// Every eidolon ancestry in any compendium or the world, for the slot dropdowns. Grouped by source.
let ANCESTRY_OPTIONS = null;
export async function eidolonAncestryOptions() {
  if (ANCESTRY_OPTIONS) return ANCESTRY_OPTIONS;
  const out = [];
  for (const pack of game.packs.filter((p) => p.metadata.type === "Item")) {
    const index = await pack.getIndex({ fields: ["system.traits.value"] });
    for (const e of index) {
      if (e.type === "ancestry" && (e.system?.traits?.value ?? []).includes("eidolon")) {
        out.push({ uuid: e.uuid, name: e.name, source: pack.metadata.label });
      }
    }
  }
  for (const item of game.items) {
    if (item.type === "ancestry" && item.system.traits?.value?.includes("eidolon")) {
      out.push({ uuid: item.uuid, name: item.name, source: "World" });
    }
  }
  ANCESTRY_OPTIONS = out.sort((a, b) => a.source.localeCompare(b.source) || a.name.localeCompare(b.name));
  return ANCESTRY_OPTIONS;
}
export function invalidateAncestryOptions() {
  ANCESTRY_OPTIONS = null;
}

// Each slot's eidolon type: chosen in the Assembly view, or (for older characters) on the Convoker Assembly
// (3) and each Expanded Assemblage (1 each).
export function slotTypes(actor) {
  const chosen = getState(actor).types;
  const legacy = legacySlotTypes(actor);
  return Array.from({ length: Math.max(chosen.length, legacy.length) }, (_, i) => chosen[i] ?? legacy[i] ?? null);
}

function legacySlotTypes(actor) {
  const assembly = actor.itemTypes.feat.find((f) => f.slug === FEAT.assembly);
  const sel = assembly?.flags?.pf2e?.rulesSelections ?? {};
  const types = [sel.assemblyEidolon1, sel.assemblyEidolon2, sel.assemblyEidolon3];
  const expanded = actor.itemTypes.feat
    .filter((f) => f.slug === FEAT.expanded)
    .sort((a, b) => (a._stats?.createdTime ?? 0) - (b._stats?.createdTime ?? 0));
  for (const f of expanded) types.push(f.flags?.pf2e?.rulesSelections?.expandedEidolon ?? null);
  return types.map((t) => (typeof t === "string" && t.length ? t : null));
}

export function typeName(uuid) {
  if (!uuid) return null;
  return fromUuidSync(uuid)?.name ?? null;
}

export function getMembers(actor) {
  const state = getState(actor);
  const types = slotTypes(actor);
  const count = slotCount(actor);
  return state.slots.map((id, index) => {
    const eidolon = id ? game.actors.get(id) ?? null : null;
    return {
      index,
      id,
      actor: eidolon,
      missing: !!id && !eidolon,
      locked: index >= count,
      typeUuid: types[index] ?? null,
      typeName: typeName(types[index]),
      isPrimary: !!id && id === state.primary,
    };
  });
}

export function getPrimary(actor) {
  const { primary } = getState(actor);
  return primary ? game.actors.get(primary) ?? null : null;
}

export function linkedEidolons(actor) {
  return getMembers(actor).filter((m) => m.actor).map((m) => m.actor);
}

export function sceneTokenOf(actor, scene = canvas.scene) {
  if (!actor || !scene) return null;
  return scene.tokens.find((t) => t.actorId === actor.id && t.actorLink) ?? null;
}

// ---------------------------------------------------------------------------------------------------------------- linking
function toolbeltShareData(summoner) {
  if (!game.modules.get("pf2e-toolbelt")?.active) return null;
  return {
    master: summoner.id,
    health: true,
    timeEvents: true,
    weaponRunes: true,
    armorRunes: true,
    spellcasting: true,
    heroPoints: false,
    languages: false,
    skills: false,
  };
}

export function toolbeltShareEnabled() {
  if (!game.modules.get("pf2e-toolbelt")?.active) return false;
  try {
    return !!game.settings.get("pf2e-toolbelt", "shareData.enabled");
  } catch {
    return false;
  }
}

export function eidolonLinkFlags(summoner) {
  const flags = { [MODULE_ID]: { convoker: summoner.id } };
  const share = toolbeltShareData(summoner);
  if (share) flags["pf2e-toolbelt"] = { shareData: { data: share } };
  return flags;
}

export async function linkEidolon(summoner, eidolon, index) {
  const state = getState(summoner);
  const prevSlot = state.slots.indexOf(eidolon.id);
  if (prevSlot >= 0) state.slots[prevSlot] = null;
  const previous = state.slots[index];
  if (previous && previous !== eidolon.id) {
    const old = game.actors.get(previous);
    if (old?.isOwner) await old.unsetFlag(MODULE_ID, "convoker");
  }
  state.slots[index] = eidolon.id;
  if (!state.primary || !state.slots.includes(state.primary)) state.primary = eidolon.id;
  await saveState(summoner, state);
  await eidolon.update({
    flags: eidolonLinkFlags(summoner),
    "system.details.level.value": summoner.level,
  });
}

export async function unlinkEidolon(summoner, index) {
  const state = getState(summoner);
  const id = state.slots[index];
  state.slots[index] = null;
  if (state.primary === id) state.primary = state.slots.find((s) => s) ?? null;
  await saveState(summoner, state);
  const eidolon = id ? game.actors.get(id) : null;
  if (eidolon?.isOwner) await eidolon.unsetFlag(MODULE_ID, "convoker");
}

export async function setPrimaryFlag(summoner, eidolonId) {
  const state = getState(summoner);
  state.primary = eidolonId;
  await saveState(summoner, state);
}

// ---------------------------------------------------------------------------------------------------------------- eidolon actors
// Finds the eidolon-actor ancestry for a summoner-side eidolon choice (ours, or Companion Compendia's by name).
export async function ancestryFor(typeUuid) {
  if (!typeUuid) return null;
  const type = await fromUuid(typeUuid);
  if (!type) return null;
  // Assembly picks are eidolon ancestries (any compendium, e.g. Summoners+); use them as-is.
  if (type.type === "ancestry") return type.uuid;
  // Older picks were the summoner-side eidolon feature: find the ancestry of the same name.
  for (const packId of [EI_PACK, CC_EIDOLON_PACK]) {
    const uuid = await packUuid(packId, type.name, "ancestry");
    if (uuid) return uuid;
  }
  for (const pack of game.packs.filter((p) => p.metadata.type === "Item")) {
    const index = await pack.getIndex({ fields: ["type"] });
    const hit = index.find((e) => e.type === "ancestry" && e.name === type.name);
    if (hit) return hit.uuid;
  }
  return game.items.find((i) => i.type === "ancestry" && i.name === type.name)?.uuid ?? null;
}

export async function createEidolonActor(summoner, index, typeOverride = null) {
  const typeUuid = typeOverride ?? slotTypes(summoner)[index];
  const type = typeUuid ? await fromUuid(typeUuid) : null;
  const ancestryUuid = await ancestryFor(typeUuid);
  const ancestry = ancestryUuid ? await fromUuid(ancestryUuid) : null;
  const name = `${summoner.name}'s ${type?.name ?? "Eidolon"}`;
  const img = ancestry?.img ?? type?.img ?? "icons/svg/mystery-man.svg";
  const data = {
    name,
    type: "character",
    img,
    folder: summoner.folder?.id ?? null,
    ownership: foundry.utils.deepClone(summoner._source.ownership),
    prototypeToken: {
      name,
      actorLink: true,
      disposition: summoner.prototypeToken.disposition,
      texture: { src: img },
      sight: { enabled: true },
    },
    system: { details: { level: { value: summoner.level } } },
    flags: eidolonLinkFlags(summoner),
  };

  let eidolon;
  if (game.user.can("ACTOR_CREATE")) {
    eidolon = await Actor.implementation.create(data);
  } else {
    const id = await asGM("createActor", { data });
    eidolon = id ? await waitForActor(id) : null;
  }
  if (!eidolon) throw new Error("The eidolon actor couldn't be created.");

  if (ancestry) {
    const itemData = ancestry.toObject();
    delete itemData._id;
    itemData._stats = { ...(itemData._stats ?? {}), compendiumSource: ancestryUuid };
    await eidolon.createEmbeddedDocuments("Item", [itemData]);
  } else if (type) {
    notify(`No eidolon ancestry was found for ${type.name}. Add one to ${name} by hand.`, "warn");
  }
  await linkEidolon(summoner, eidolon, index);
  if (typeOverride) await setSlotType(summoner, index, typeOverride);
  return eidolon;
}

// Copies items with the eidolon trait (and invested gear) from the primary to the rest of the assembly.
export async function syncSharedGear(summoner) {
  const primary = getPrimary(summoner);
  if (!primary) return notify("Set a primary eidolon first.", "warn");
  const shared = primary.inventory.filter((i) => i.traits.has("eidolon") || i.isInvested);
  let count = 0;
  for (const target of linkedEidolons(summoner)) {
    if (target.id === primary.id || !target.isOwner) continue;
    const stale = target.inventory.filter((i) => i.flags?.[MODULE_ID]?.syncedFrom).map((i) => i.id);
    if (stale.length) await target.deleteEmbeddedDocuments("Item", stale);
    const copies = shared.map((i) => {
      const d = stripGrantFlags(i.toObject());
      foundry.utils.setProperty(d, `flags.${MODULE_ID}.syncedFrom`, i.uuid);
      return d;
    });
    if (copies.length) await target.createEmbeddedDocuments("Item", copies);
    count++;
  }
  notify(`Shared gear copied to ${count} eidolon${count === 1 ? "" : "s"}.`);
}

// ---------------------------------------------------------------------------------------------------------------- spellcasting
export function focusEntry(actor) {
  return actor.itemTypes.spellcastingEntry.find((e) => e.system.prepared?.value === "focus") ?? null;
}

function assemblySelections(actor) {
  const assembly = actor.itemTypes.feat.find((f) => f.slug === FEAT.assembly);
  return assembly?.flags?.pf2e?.rulesSelections ?? {};
}

export async function ensureFocusEntry(actor) {
  const existing = focusEntry(actor);
  if (existing) return existing;
  const sel = assemblySelections(actor);
  const [entry] = await actor.createEmbeddedDocuments("Item", [{
    name: "Convoker Focus Spells",
    type: "spellcastingEntry",
    system: {
      prepared: { value: "focus" },
      tradition: { value: sel.convokerTradition ?? "arcane" },
      ability: { value: sel.convokerKey ?? actor.keyAttribute ?? "cha" },
      proficiency: { value: 1 },
    },
  }]);
  return entry;
}

const isSummonerEntry = (e) => e.flags?.["pf2e-leveler"]?.classSpellcastingEntry === "summoner" || /summoner|convoker/i.test(e.name ?? "");

// Prepared spellcasting from the assembly, using the chosen tradition and key attribute. Keeps exactly one
// class entry: character builders (PF2e Leveler) create a spontaneous "Summoner" entry, at creation and again on
// level-ups, so any such entry is folded into the Convoker one. Evolution surge is removed until Assembly Evolution.
export async function ensureConvokerSpellcasting(actor) {
  if (!actor?.isOwner) return;
  const sel = assemblySelections(actor);
  const tradition = sel.convokerTradition ?? "arcane";
  const ability = sel.convokerKey ?? "cha";
  const entries = actor.itemTypes.spellcastingEntry.filter((e) => !["focus", "innate", "items", "ritual"].includes(e.system.prepared?.value));
  let main = entries.find((e) => e.flags?.[MODULE_ID]?.convokerEntry)
    ?? entries.find((e) => e.flags?.["pf2e-leveler"]?.classSpellcastingEntry === "summoner")
    ?? entries.find(isSummonerEntry)
    ?? null;
  const mainUpdate = {
    name: "Convoker Spells",
    "system.prepared.value": "prepared",
    "system.tradition.value": tradition,
    "system.ability.value": ability,
    [`flags.${MODULE_ID}.convokerEntry`]: true,
    "flags.pf2e-leveler.classSpellcastingEntry": "summoner",
  };
  if (main) {
    const s = main.system;
    const stale = main.name !== "Convoker Spells" || s.prepared?.value !== "prepared" || s.tradition?.value !== tradition
      || s.ability?.value !== ability || !main.flags?.[MODULE_ID]?.convokerEntry;
    if (stale) await main.update(mainUpdate);
  } else {
    [main] = await actor.createEmbeddedDocuments("Item", [{
      name: "Convoker Spells",
      type: "spellcastingEntry",
      system: { prepared: { value: "prepared" }, tradition: { value: tradition }, ability: { value: ability }, proficiency: { value: 1 } },
      flags: { [MODULE_ID]: { convokerEntry: true }, "pf2e-leveler": { classSpellcastingEntry: "summoner" } },
    }]);
  }

  // Fold stray summoner entries into the Convoker one.
  const strays = actor.itemTypes.spellcastingEntry.filter((e) => e.id !== main.id
    && !["focus", "innate", "items", "ritual"].includes(e.system.prepared?.value) && isSummonerEntry(e));
  if (strays.length) {
    const ids = new Set(strays.map((e) => e.id));
    const known = new Set(actor.itemTypes.spell.filter((s) => s.system.location?.value === main.id).map((s) => s.sourceId ?? s.slug));
    const move = [];
    const drop = [];
    for (const spell of actor.itemTypes.spell.filter((s) => ids.has(s.system.location?.value))) {
      const key = spell.sourceId ?? spell.slug;
      if (known.has(key)) drop.push(spell.id);
      else {
        known.add(key);
        move.push({ _id: spell.id, "system.location.value": main.id });
      }
    }
    // Builders set the new level's slot counts on the entry they create; keep the higher of each.
    const slotUpdate = {};
    for (const stray of strays) {
      for (const [key, slot] of Object.entries(stray.system.slots ?? {})) {
        const have = Number(main.system.slots?.[key]?.max ?? 0);
        const want = Math.max(have, Number(slot?.max ?? 0), Number(slotUpdate[`system.slots.${key}.max`] ?? 0));
        if (want > have) slotUpdate[`system.slots.${key}.max`] = want;
      }
    }
    if (Object.keys(slotUpdate).length) await main.update(slotUpdate);
    if (move.length) await actor.updateEmbeddedDocuments("Item", move);
    await actor.deleteEmbeddedDocuments("Item", [...drop, ...ids]);
  }

  // Convokers don't get evolution surge at 1st level; Assembly Evolution grants it back.
  if (!hasFeat(actor, FEAT.assemblyEvolution)) {
    const surge = actor.itemTypes.spell.filter((s) => s.sourceId === EVOLUTION_SURGE).map((s) => s.id);
    if (surge.length) await actor.deleteEmbeddedDocuments("Item", surge);
  }

  const focus = focusEntry(actor);
  if (focus && (focus.system.tradition?.value !== tradition || focus.system.ability?.value !== ability)) {
    await focus.update({ "system.tradition.value": tradition, "system.ability.value": ability });
  }
}

// Debounced tidy-up after spellcasting items land on a convoker (lets a builder finish its batch first).
const tidyTimers = new Map();
export function scheduleConvokerSpellTidy(actor) {
  if (!isConvoker(actor) || !actor.isOwner) return;
  clearTimeout(tidyTimers.get(actor.id));
  tidyTimers.set(actor.id, setTimeout(() => {
    tidyTimers.delete(actor.id);
    ensureConvokerSpellcasting(actor).catch((err) => console.error(`${MODULE_ID} | spell tidy failed`, err));
  }, 1500));
}

export async function grantFeatSpell(actor, feat) {
  const ref = FEAT_SPELLS[feat.slug];
  if (!ref || feat.type !== "feat") return;
  const uuid = ref.uuid ?? (await packUuid(ref.pack, ref.name, "spell"));
  if (!uuid) return;
  if (actor.itemTypes.spell.some((s) => s.sourceId === uuid)) return;
  const spell = await fromUuid(uuid);
  if (!spell) return;
  const entry = await ensureFocusEntry(actor);
  const data = spell.toObject();
  delete data._id;
  data._stats = { ...(data._stats ?? {}), compendiumSource: uuid };
  data.system.location = { value: entry.id };
  foundry.utils.setProperty(data, `flags.${MODULE_ID}.grantedByFeat`, feat.id);
  await actor.createEmbeddedDocuments("Item", [data]);
}

export async function revokeFeatSpell(actor, feat) {
  const ids = actor.itemTypes.spell.filter((s) => s.flags?.[MODULE_ID]?.grantedByFeat === feat.id).map((s) => s.id);
  if (ids.length) await actor.deleteEmbeddedDocuments("Item", ids);
}

export function findSpell(actor, slug) {
  return actor.itemTypes.spell.find((s) => s.slug === slug) ?? null;
}
