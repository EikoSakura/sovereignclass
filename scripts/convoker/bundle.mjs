// One-file export and import of a convoker with their whole assembly, including portrait and token images.
// The bundle rides in the summoner's own JSON (flags.pf2e-sovereign.bundle), so Foundry's regular
// "Export Data" / "Import Data" on the actor carry the assembly too.
import { MODULE_ID, eidolonLinkFlags, getState, isConvoker, linkedEidolons, notify, saveState, asGM, waitForActor } from "./core.mjs";

const BUNDLE_VERSION = 1;
const SHARED_PREFIXES = ["icons/", "systems/", "modules/", "ui/", "cards/", "sounds/"];

function shouldEmbed(path) {
  if (!path || typeof path !== "string") return false;
  if (/^(data:|https?:|blob:)/i.test(path)) return false;
  return !SHARED_PREFIXES.some((p) => path.startsWith(p));
}

function imagePaths(data) {
  const out = [data.img, data.prototypeToken?.texture?.src, data.prototypeToken?.ring?.subject?.texture];
  return out.filter(shouldEmbed);
}

async function toDataURL(path) {
  try {
    const res = await fetch(foundry.utils.getRoute(path));
    if (!res.ok) return null;
    const blob = await res.blob();
    return await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

function exportData(doc) {
  const data = doc.toCompendium(null, { clearSource: false });
  data._stats ??= {};
  data._stats.exportSource = {
    worldId: game.world.id,
    uuid: doc.uuid,
    coreVersion: game.version,
    systemId: game.system.id,
    systemVersion: game.system.version,
  };
  return data;
}

// Summoner JSON with the assembly embedded.
export async function buildBundle(summoner) {
  const data = exportData(summoner);
  const state = getState(summoner);
  const eidolons = [];
  const slots = state.slots.map((id) => {
    const actor = id ? game.actors.get(id) : null;
    if (!actor) return null;
    eidolons.push({ originalId: actor.id, data: exportData(actor) });
    return eidolons.length - 1;
  });
  const primary = state.primary ? eidolons.findIndex((e) => e.originalId === state.primary) : -1;

  const images = {};
  for (const path of new Set([...imagePaths(data), ...eidolons.flatMap((e) => imagePaths(e.data))])) {
    const url = await toDataURL(path);
    if (url) images[path] = url;
  }
  const types = state.types ?? [];
  foundry.utils.setProperty(data, `flags.${MODULE_ID}.bundle`, { version: BUNDLE_VERSION, slots, types, primary, eidolons, images });
  return data;
}

export async function exportAssembly(summoner) {
  notify("Packing your assembly...");
  const data = await buildBundle(summoner);
  const filename = ["fvtt", "Actor", summoner.name?.slugify(), "assembly"].filterJoin("-");
  foundry.utils.saveDataToFile(JSON.stringify(data, null, 2), "application/json", `${filename}.json`);
  const n = data.flags[MODULE_ID].bundle.eidolons.length;
  notify(`Exported ${summoner.name} with ${n} eidolon${n === 1 ? "" : "s"}.`);
}

// ---------------------------------------------------------------------------------------------------------------- import
async function pathExists(path) {
  try {
    const res = await fetch(foundry.utils.getRoute(path), { method: "HEAD" });
    return res.ok;
  } catch {
    return false;
  }
}

async function ensureDir(path) {
  const FP = foundry.applications.apps.FilePicker.implementation;
  let built = "";
  for (const part of path.split("/")) {
    built = built ? `${built}/${part}` : part;
    try {
      await FP.createDirectory("data", built);
    } catch {
      /* exists */
    }
  }
}

// Writes embedded images that this world doesn't have yet. Returns {oldPath: newPath}.
async function restoreImages(images, folderName) {
  const map = {};
  const entries = Object.entries(images ?? {});
  if (!entries.length) return map;
  const canUpload = game.user.can("FILES_UPLOAD");
  const dir = `${MODULE_ID}-assemblies/${folderName}`;
  let dirReady = false;
  for (const [path, url] of entries) {
    if (await pathExists(path)) continue;
    if (!canUpload) {
      notify(`${path} is missing and you can't upload files. Ask your GM to import the assembly.`, "warn");
      continue;
    }
    if (!dirReady) {
      await ensureDir(dir);
      dirReady = true;
    }
    const blob = await (await fetch(url)).blob();
    const name = path.split("/").pop() || `${foundry.utils.randomID()}.webp`;
    const file = new File([blob], name, { type: blob.type });
    const res = await foundry.applications.apps.FilePicker.implementation.upload("data", dir, file, {}, { notify: false });
    if (res?.path) map[path] = res.path;
  }
  return map;
}

function remapImages(data, map) {
  const swap = (p) => map[p] ?? p;
  if (data.img) data.img = swap(data.img);
  if (data.prototypeToken?.texture?.src) data.prototypeToken.texture.src = swap(data.prototypeToken.texture.src);
  if (data.prototypeToken?.ring?.subject?.texture) data.prototypeToken.ring.subject.texture = swap(data.prototypeToken.ring.subject.texture);
  return data;
}

async function prepareActorData(raw) {
  const doc = await Actor.implementation.fromImport(foundry.utils.deepClone(raw));
  const data = game.actors.fromCompendium(doc, { keepId: false });
  delete data._id;
  return data;
}

// Recreates (or updates) the eidolon actors from a bundle and links them to this summoner.
export async function restoreBundle(summoner, bundle) {
  if (!bundle?.eidolons) return;
  const map = await restoreImages(bundle.images, summoner.name.slugify() || summoner.id);

  const summonerUpdate = remapImages({ img: summoner.img, prototypeToken: { texture: { src: summoner.prototypeToken.texture.src } } }, map);
  if (summonerUpdate.img !== summoner.img || summonerUpdate.prototypeToken.texture.src !== summoner.prototypeToken.texture.src) {
    await summoner.update({ img: summonerUpdate.img, "prototypeToken.texture.src": summonerUpdate.prototypeToken.texture.src });
  }

  const created = [];
  for (const entry of bundle.eidolons) {
    const data = remapImages(await prepareActorData(entry.data), map);
    data.folder = summoner.folder?.id ?? null;
    data.ownership = foundry.utils.deepClone(summoner._source.ownership);
    data.flags = foundry.utils.mergeObject(data.flags ?? {}, eidolonLinkFlags(summoner));

    // Re-importing into the same world updates the eidolon in place instead of duplicating it.
    const existing = game.actors.get(entry.originalId);
    let actor;
    if (existing && existing.getFlag(MODULE_ID, "convoker") === summoner.id && existing.isOwner) {
      await existing.update(data, { diff: false, recursive: false, noHook: true });
      actor = existing;
    } else if (game.user.can("ACTOR_CREATE")) {
      actor = await Actor.implementation.create(data);
    } else {
      const id = await asGM("createActor", { data });
      actor = id ? await waitForActor(id) : null;
    }
    created.push(actor ?? null);
  }

  const slots = bundle.slots.map((i) => (i === null || i === undefined ? null : created[i]?.id ?? null));
  const primary = bundle.primary >= 0 ? created[bundle.primary]?.id ?? null : slots.find(Boolean) ?? null;
  await saveState(summoner, { slots, types: bundle.types ?? [], primary });
  await summoner.unsetFlag(MODULE_ID, "bundle");
  const n = created.filter(Boolean).length;
  notify(`Restored ${n} eidolon${n === 1 ? "" : "s"} for ${summoner.name}.`);
}

export async function importAssemblyDialog(summoner) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json,application/json";
  input.addEventListener("change", async () => {
    const file = input.files?.[0];
    if (!file) return;
    const text = await foundry.utils.readTextFromFile(file);
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch {
      return notify("That file isn't valid JSON.", "error");
    }
    if (!parsed.flags?.[MODULE_ID]?.bundle) {
      return notify("That file has no assembly in it. Export it with the Assembly window's Export button.", "warn");
    }
    const ok = await foundry.applications.api.DialogV2.confirm({
      window: { title: "Import assembly" },
      content: `<p>Replace <strong>${foundry.utils.escapeHTML(summoner.name)}</strong> with <strong>${foundry.utils.escapeHTML(parsed.name)}</strong> from the file, and restore its eidolons?</p>`,
    });
    if (ok) await summoner.importFromJSON(text);
  });
  input.click();
}

// Patches Actor export/import so the regular sidebar options carry the assembly.
export function patchExportImport() {
  const cls = CONFIG.PF2E?.Actor?.documentClasses?.character ?? CONFIG.Actor.documentClass;
  const proto = cls.prototype;
  const originalExport = proto.exportToJSON;
  const originalImport = proto.importFromJSON;

  proto.exportToJSON = function (options = {}) {
    if (isConvoker(this) && linkedEidolons(this).length) return exportAssembly(this);
    return originalExport.call(this, options);
  };

  proto.importFromJSON = async function (json) {
    let bundle = null;
    try {
      bundle = JSON.parse(json)?.flags?.[MODULE_ID]?.bundle ?? null;
    } catch {
      /* let core report it */
    }
    const result = await originalImport.call(this, json);
    if (bundle) await restoreBundle(this, bundle);
    return result;
  };
}
