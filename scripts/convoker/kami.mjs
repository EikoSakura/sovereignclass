// Kami Ward: while a kami eidolon has the ward, its summoner gets the same bonus whenever their tokens are adjacent.
// Works for any summoner: the convoker link, or pf2e-toolbelt's Shared Data master.
import { MODULE_ID, getConvoker } from "./core.mjs";

const WARD = "effect-kami-ward";

function summonerOf(eidolon) {
  const convoker = getConvoker(eidolon);
  if (convoker) return convoker;
  const master = eidolon?.getFlag?.("pf2e-toolbelt", "shareData.data.master");
  return master ? game.actors.get(master) ?? null : null;
}

function wardOn(eidolon) {
  return eidolon?.itemTypes?.effect?.find((e) => e.slug === WARD && !e.flags?.[MODULE_ID]?.kamiWardFrom) ?? null;
}

function sharedWard(summoner, eidolonId) {
  return summoner.itemTypes.effect.find((e) => e.flags?.[MODULE_ID]?.kamiWardFrom === eidolonId) ?? null;
}

// Adjacent = the two tokens' squares touch (diagonals count), using document positions rather than animation state.
function adjacent(a, b) {
  if (!a || !b || a.parent !== b.parent) return false;
  const g = a.parent.grid.size;
  const r = (t) => ({ x1: t.x / g, y1: t.y / g, x2: t.x / g + t.width, y2: t.y / g + t.height });
  const p = r(a);
  const q = r(b);
  const gapX = Math.max(0, q.x1 - p.x2, p.x1 - q.x2);
  const gapY = Math.max(0, q.y1 - p.y2, p.y1 - q.y2);
  return Math.max(gapX, gapY) < 0.01;
}

// Adds or removes the summoner's copy of the ward for one eidolon.
export async function updateKamiWard(eidolon) {
  const summoner = summonerOf(eidolon);
  if (!summoner || game.user !== summoner.primaryUpdater) return;
  const ward = wardOn(eidolon);
  const existing = sharedWard(summoner, eidolon.id);
  const scene = canvas.scene;
  const eToken = scene?.tokens.find((t) => t.actorId === eidolon.id);
  const sToken = scene?.tokens.find((t) => t.actorId === summoner.id);
  const want = !!ward && adjacent(eToken, sToken);

  if (want && !existing) {
    const data = ward.toObject();
    delete data._id;
    data.name = `${ward.name} (${eidolon.name})`;
    foundry.utils.setProperty(data, `flags.${MODULE_ID}.kamiWardFrom`, eidolon.id);
    await summoner.createEmbeddedDocuments("Item", [data]);
  } else if (!want && existing) {
    await summoner.deleteEmbeddedDocuments("Item", [existing.id]);
  }
}

function eidolonsNear(actor) {
  if (!actor) return [];
  if (wardOn(actor) || summonerOf(actor)) return [actor];
  // The summoner moved: check every eidolon that names them as summoner and has (or shared) a ward.
  return game.actors.filter((a) => summonerOf(a)?.id === actor.id && (wardOn(a) || sharedWard(actor, a.id)));
}

export function registerKamiWard() {
  Hooks.on("createItem", (item) => {
    if (item.slug === WARD && item.actor && !item.flags?.[MODULE_ID]?.kamiWardFrom) updateKamiWard(item.actor);
  });
  Hooks.on("deleteItem", (item) => {
    if (item.slug === WARD && item.actor && !item.flags?.[MODULE_ID]?.kamiWardFrom) updateKamiWard(item.actor);
  });
  Hooks.on("updateToken", (token, changes) => {
    if (!("x" in changes) && !("y" in changes)) return;
    for (const eidolon of new Set(eidolonsNear(token.actor))) updateKamiWard(eidolon);
  });
  Hooks.on("deleteToken", (token) => {
    for (const eidolon of new Set(eidolonsNear(token.actor))) updateKamiWard(eidolon);
  });
}
