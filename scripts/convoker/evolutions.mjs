// Convoker evolution feats: every evolution feat the summoner takes is a "slot", and each eidolon in the
// assembly gets its own evolution feat for that slot (same level or lower), retrainable at daily preparations.
// The eidolon's copy is flagged `flags.pf2e-sovereign.evolutionSlot = <summoner feat id>`.
import { MODULE_ID, linkedEidolons, notify } from "./core.mjs";

const CC_SUFFIX = / \(CC\)$/;
let OPTIONS = null;

const baseName = (name) => String(name ?? "").replace(CC_SUFFIX, "").trim();

export function isEvolution(item) {
  return item?.type === "feat" && (item.system?.traits?.value ?? []).includes("evolution");
}

// Evolution feats on the summoner, lowest level first.
export function evolutionSlots(summoner) {
  return summoner.itemTypes.feat
    .filter((f) => isEvolution(f) && !f.flags?.[MODULE_ID]?.evolutionSlot)
    .sort((a, b) => (a.level - b.level) || ((a._stats?.createdTime ?? 0) - (b._stats?.createdTime ?? 0)));
}

// Every evolution feat in any compendium or the world, one per name. Companion Compendia's eidolon-side
// "(CC)" copies win, since those carry the rule elements that work on the eidolon actor.
export async function evolutionOptions() {
  if (OPTIONS) return OPTIONS;
  const byName = new Map();
  const consider = (entry, uuid, source) => {
    const traits = entry.system?.traits?.value ?? [];
    if (entry.type !== "feat" || !traits.includes("evolution")) return;
    const name = baseName(entry.name);
    const isCC = CC_SUFFIX.test(entry.name);
    const current = byName.get(name);
    if (current && (current.isCC || !isCC)) return;
    byName.set(name, { uuid, name, level: Number(entry.system?.level?.value ?? 1), source, isCC });
  };
  for (const pack of game.packs.filter((p) => p.metadata.type === "Item")) {
    const index = await pack.getIndex({ fields: ["system.traits.value", "system.level.value"] });
    for (const e of index) consider(e, e.uuid, pack.metadata.label);
  }
  for (const item of game.items) consider(item, item.uuid, "World");
  OPTIONS = [...byName.values()].sort((a, b) => (a.level - b.level) || a.name.localeCompare(b.name));
  return OPTIONS;
}

export function optionsSync() {
  return OPTIONS;
}

export function assignedFor(eidolon, slotId) {
  return eidolon.itemTypes.feat.find((f) => f.flags?.[MODULE_ID]?.evolutionSlot === slotId) ?? null;
}

export function assignedSource(item) {
  return item?.flags?.[MODULE_ID]?.evolutionSource ?? item?.sourceId ?? null;
}

function defaultFor(slot, options) {
  const name = baseName(slot.name);
  return options.find((o) => o.name === name) ?? null;
}

// Gives `eidolon` the evolution feat at `uuid` for this slot, replacing whatever it had there.
export async function assignEvolution(eidolon, slotId, uuid) {
  if (!eidolon?.isOwner) return notify(`You don't own ${eidolon?.name ?? "that eidolon"}.`, "warn");
  const old = assignedFor(eidolon, slotId);
  if (old) await eidolon.deleteEmbeddedDocuments("Item", [old.id]);
  if (!uuid) return null;
  const source = await fromUuid(uuid);
  if (!source) return notify("That evolution feat couldn't be found.", "error");
  const data = source.toObject();
  delete data._id;
  data._stats = { ...(data._stats ?? {}), compendiumSource: source.pack ? uuid : data._stats?.compendiumSource ?? null };
  data.system.location = null;
  foundry.utils.mergeObject(data, { flags: { [MODULE_ID]: { evolutionSlot: slotId, evolutionSource: uuid } } });
  const [created] = await eidolon.createEmbeddedDocuments("Item", [data]);
  return created;
}

// Fills any empty slot on every linked eidolon with the same feat the summoner took.
export async function fillEvolutionDefaults(summoner) {
  const slots = evolutionSlots(summoner);
  if (!slots.length) return 0;
  const options = await evolutionOptions();
  let count = 0;
  for (const eidolon of linkedEidolons(summoner)) {
    if (!eidolon.isOwner) continue;
    for (const slot of slots) {
      if (assignedFor(eidolon, slot.id)) continue;
      const def = defaultFor(slot, options);
      if (!def) continue;
      await assignEvolution(eidolon, slot.id, def.uuid);
      count++;
    }
  }
  return count;
}

// Removes every eidolon's pick for a slot when the summoner loses that evolution feat.
export async function removeEvolutionSlot(summoner, slotId) {
  for (const eidolon of linkedEidolons(summoner)) {
    const item = assignedFor(eidolon, slotId);
    if (item && eidolon.isOwner) await eidolon.deleteEmbeddedDocuments("Item", [item.id]);
  }
}

export function invalidateEvolutionOptions() {
  OPTIONS = null;
}
