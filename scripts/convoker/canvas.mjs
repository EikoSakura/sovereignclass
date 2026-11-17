// Token placement, swapping, and carryover for the Convoker flows.
import { EFFECT, MODULE_ID, SU_PACK, asGM, notify, packDocData, sceneTokenOf } from "./core.mjs";

const EPS = 0.5;

function rectOf(scene, td) {
  const g = scene.grid.size;
  return { x: td.x, y: td.y, w: td.width * g, h: td.height * g };
}

function overlaps(a, b) {
  return a.x < b.x + b.w - EPS && a.x + a.w > b.x + EPS && a.y < b.y + b.h - EPS && a.y + a.h > b.y + EPS;
}

export function isAreaFree(scene, x, y, width, height, ignore = []) {
  const g = scene.grid.size;
  const rect = { x, y, w: width * g, h: height * g };
  const bounds = scene.dimensions.sceneRect;
  if (rect.x < bounds.x - EPS || rect.y < bounds.y - EPS) return false;
  if (rect.x + rect.w > bounds.x + bounds.width + EPS || rect.y + rect.h > bounds.y + bounds.height + EPS) return false;
  for (const td of scene.tokens) {
    if (ignore.includes(td.id)) continue;
    if (overlaps(rect, rectOf(scene, td))) return false;
  }
  return true;
}

// The first open spot adjacent to `anchor` that fits a width x height token, nearest first.
export function findAdjacentSpot(scene, anchor, width, height, ignore = []) {
  const g = scene.grid.size;
  const candidates = [];
  for (let dx = -width; dx <= anchor.width; dx++) {
    for (let dy = -height; dy <= anchor.height; dy++) {
      const inside = dx > -width && dx < anchor.width && dy > -height && dy < anchor.height;
      if (inside) continue;
      candidates.push({ x: anchor.x + dx * g, y: anchor.y + dy * g, d: Math.abs(dx) + Math.abs(dy) });
    }
  }
  candidates.sort((a, b) => a.d - b.d);
  return candidates.find((c) => isAreaFree(scene, c.x, c.y, width, height, ignore)) ?? null;
}

// Positions for a token of new size that still cover the old token's top-left square.
function swapSpots(scene, old, width, height) {
  const g = scene.grid.size;
  const out = [];
  const growX = Math.max(0, width - old.width);
  const growY = Math.max(0, height - old.height);
  for (let dx = 0; dx <= growX; dx++) for (let dy = 0; dy <= growY; dy++) out.push({ x: old.x - dx * g, y: old.y - dy * g });
  return out;
}

export function tokenCenter(td) {
  const g = td.parent.grid.size;
  return { x: td.x + (td.width * g) / 2, y: td.y + (td.height * g) / 2 };
}

// Waits for the user to click a grid space. Resolves {x, y} (top-left, snapped) or null on right click / Escape.
export function pickPoint({ prompt, origin = null, maxDistance = null, width = 1, height = 1 } = {}) {
  return new Promise((resolve) => {
    const view = canvas.app.view;
    const g = canvas.grid.size;
    const preview = new PIXI.Graphics();
    canvas.controls.addChild(preview);
    if (origin && maxDistance) {
      const radius = (maxDistance / canvas.grid.distance) * g + g / 2;
      preview.lineStyle(3, 0x6aa5ff, 0.9).beginFill(0x6aa5ff, 0.08).drawCircle(origin.x, origin.y, radius).endFill();
    }
    const marker = new PIXI.Graphics();
    canvas.controls.addChild(marker);
    const note = ui.notifications.info(`Convoker | ${prompt} (right click or Escape to cancel)`, { permanent: true });

    const cleanup = (value) => {
      view.removeEventListener("pointerdown", onDown, true);
      view.removeEventListener("pointermove", onMove, true);
      window.removeEventListener("keydown", onKey, true);
      preview.destroy();
      marker.destroy();
      try {
        if (typeof note?.remove === "function") note.remove();
        else ui.notifications.remove(note?.id ?? note);
      } catch {
        /* notification already gone */
      }
      resolve(value);
    };
    const toTopLeft = (event) => {
      const p = canvas.canvasCoordinatesFromClient({ x: event.clientX, y: event.clientY });
      const tl = canvas.grid.getTopLeftPoint({ x: p.x - ((width - 1) * g) / 2, y: p.y - ((height - 1) * g) / 2 });
      return { x: tl.x, y: tl.y };
    };
    const inRange = (tl) => {
      if (!origin || !maxDistance) return true;
      const center = { x: tl.x + (width * g) / 2, y: tl.y + (height * g) / 2 };
      return canvas.grid.measurePath([origin, center]).distance <= maxDistance + 0.01;
    };
    const onMove = (event) => {
      const tl = toTopLeft(event);
      marker.clear().lineStyle(2, inRange(tl) ? 0x4caf50 : 0xe53935, 1).drawRect(tl.x, tl.y, width * g, height * g);
    };
    const onDown = (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (event.button === 2) return cleanup(null);
      if (event.button !== 0) return;
      const tl = toTopLeft(event);
      if (!inRange(tl)) return notify(`That's farther than ${maxDistance} feet.`, "warn");
      cleanup(tl);
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cleanup(null);
      }
    };
    view.addEventListener("pointerdown", onDown, true);
    view.addEventListener("pointermove", onMove, true);
    window.addEventListener("keydown", onKey, true);
  });
}

// ---------------------------------------------------------------------------------------------------------------- tokens
export async function createTokens(scene, data) {
  if (game.user.can("TOKEN_CREATE")) {
    const docs = await scene.createEmbeddedDocuments("Token", data);
    return docs;
  }
  const ids = await asGM("createTokens", { sceneId: scene.id, data });
  return ids.map((id) => scene.tokens.get(id)).filter(Boolean);
}

export async function deleteTokens(scene, ids) {
  if (!ids.length) return;
  const own = ids.every((id) => scene.tokens.get(id)?.isOwner);
  if (own && game.user.can("TOKEN_DELETE")) return scene.deleteEmbeddedDocuments("Token", ids);
  return asGM("deleteTokens", { sceneId: scene.id, ids });
}

export async function teleportToken(td, x, y) {
  if (td.isOwner) {
    return td.move({ x, y, action: "blink" }, { constrainOptions: { ignoreWalls: true, ignoreCost: true } });
  }
  return asGM("moveToken", { sceneId: td.parent.id, tokenId: td.id, x, y });
}

export async function tokenDataFor(actor, x, y, extra = {}) {
  const td = await actor.getTokenDocument({ x, y, ...extra });
  return td.toObject();
}

// ---------------------------------------------------------------------------------------------------------------- carryover
function carriesOver(item) {
  if (!["condition", "effect"].includes(item.type)) return false;
  const flags = item.flags ?? {};
  if (flags.pf2e?.aura) return false;
  if (flags[MODULE_ID]?.fusion || flags[MODULE_ID]?.fusedBy || flags[MODULE_ID]?.assaultTemp) return false;
  if (item.grantedBy && item.grantedBy.actor === item.actor) return false;
  if (item.isOfType?.("condition") && item.system.references?.parent) return false;
  return true;
}

// Moves conditions and effects (and HP, when it isn't shared by pf2e-toolbelt) from one eidolon to another.
export async function carryOver(from, to) {
  const items = from.items.filter(carriesOver);
  const moved = items.map((i) => i.name);
  if (items.length && to.isOwner) {
    await to.createEmbeddedDocuments("Item", items.map((i) => {
      const d = i.toObject();
      delete d._id;
      return d;
    }));
    if (from.isOwner) await from.deleteEmbeddedDocuments("Item", items.map((i) => i.id));
  }
  const shared = from.getFlag("pf2e-toolbelt", "shareData.data.health") && game.modules.get("pf2e-toolbelt")?.active;
  if (!shared && to.isOwner) {
    const hp = from.system.attributes.hp;
    await to.update({
      "system.attributes.hp.value": Math.min(hp.value, to.system.attributes.hp.max),
      "system.attributes.hp.temp": hp.temp ?? 0,
    });
  }
  return moved;
}

export async function endFusion(eidolon) {
  if (!eidolon?.isOwner) return;
  const ids = eidolon.items.filter((i) => i.flags?.[MODULE_ID]?.fusion).map((i) => i.id);
  if (ids.length) await eidolon.deleteEmbeddedDocuments("Item", ids);
}

export async function applyEffectByName(actor, name, flags = {}) {
  const data = await packDocData(SU_PACK, name, "effect");
  if (!data) return null;
  foundry.utils.mergeObject(data, { flags: { [MODULE_ID]: flags } });
  const [doc] = await actor.createEmbeddedDocuments("Item", [data]);
  return doc;
}

// ---------------------------------------------------------------------------------------------------------------- swap
// Replaces `from`'s token with `to`'s on the current scene. Returns {ok, token, moved, reason}.
export async function swapEidolons(from, to, { carry = true, lockout = true } = {}) {
  const scene = canvas.scene;
  const oldToken = sceneTokenOf(from, scene);
  await endFusion(from);
  const moved = carry ? await carryOver(from, to) : [];
  if (lockout) await applyEffectByName(to, EFFECT.convoked);
  if (!scene || !oldToken) return { ok: true, token: null, moved };

  const probe = await to.getTokenDocument({ x: oldToken.x, y: oldToken.y });
  const width = probe.width;
  const height = probe.height;
  const spot = swapSpots(scene, oldToken, width, height).find((s) => isAreaFree(scene, s.x, s.y, width, height, [oldToken.id]));
  if (!spot) return { ok: false, token: null, moved, reason: `${to.name} doesn't have room to appear.` };

  const data = await tokenDataFor(to, spot.x, spot.y, {
    elevation: oldToken.elevation,
    hidden: oldToken.hidden,
    disposition: oldToken.disposition,
  });
  const [token] = await createTokens(scene, [data]);

  const combatant = game.combat?.combatants.find((c) => c.tokenId === oldToken.id && c.sceneId === scene.id);
  if (combatant && token) {
    await asGM("swapCombatant", {
      combatId: game.combat.id,
      combatantId: combatant.id,
      tokenId: token.id,
      actorId: to.id,
      sceneId: scene.id,
    }).catch((err) => notify(`Couldn't move the combatant: ${err.message}`, "warn"));
  }
  await deleteTokens(scene, [oldToken.id]);
  return { ok: true, token, moved };
}

export async function manifest(summoner, eidolon, { pick = false } = {}) {
  const scene = canvas.scene;
  if (!scene) return notify("Open a scene first.", "warn");
  if (sceneTokenOf(eidolon, scene)) return notify(`${eidolon.name} is already manifested.`, "warn");
  const probe = await eidolon.getTokenDocument({ x: 0, y: 0 });
  const anchor = sceneTokenOf(summoner, scene);
  let spot = !pick && anchor ? findAdjacentSpot(scene, anchor, probe.width, probe.height) : null;
  if (!spot) {
    spot = await pickPoint({
      prompt: `Click where ${eidolon.name} appears`,
      origin: anchor ? tokenCenter(anchor) : null,
      maxDistance: anchor ? 5 * Math.max(probe.width, 1) : null,
      width: probe.width,
      height: probe.height,
    });
    if (!spot) return null;
  }
  const data = await tokenDataFor(eidolon, spot.x, spot.y, { disposition: anchor?.disposition ?? probe.disposition });
  const [token] = await createTokens(scene, [data]);
  return token;
}

export async function unmanifest(eidolon) {
  const scene = canvas.scene;
  await endFusion(eidolon);
  const token = sceneTokenOf(eidolon, scene);
  if (token) await deleteTokens(scene, [token.id]);
}
