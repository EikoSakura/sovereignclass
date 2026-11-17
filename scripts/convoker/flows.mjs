// Convoke, Assembled Assault, and Combination Convocation, from the Assembly window or from casting the spell.
import {
  BOOST_EIDOLON_SLUG, EFFECT, FEAT, MODULE_ID, SPELL, findSpell, getMembers, getPrimary, hasFeat, localizeLabel as esc,
  notify, sceneTokenOf, setPrimaryFlag, stripGrantFlags,
} from "./core.mjs";
import {
  applyEffectByName, createTokens, deleteTokens, isAreaFree, pickPoint, swapEidolons, teleportToken, tokenCenter,
  tokenDataFor,
} from "./canvas.mjs";

const { DialogV2 } = foundry.applications.api;
const CAST_OPTION = "origin:action:slug:cast-a-spell";
const castingFromWindow = new Set();

// ---------------------------------------------------------------------------------------------------------------- casting
// Casts the spell from the summoner's sheet so pf2e spends the Focus Point and posts the spell card.
async function castSpell(summoner, slug) {
  const spell = findSpell(summoner, slug);
  if (!spell) {
    notify(`The ${slug.replace(/-/g, " ")} spell isn't on ${summoner.name}'s sheet, so no Focus Point was spent.`, "warn");
    return { ok: true, rank: null };
  }
  const entry = spell.spellcasting;
  if (!entry) return { ok: true, rank: spell.rank };
  const before = summoner.system.resources.focus?.value ?? 0;
  const key = `${summoner.id}:${slug}`;
  castingFromWindow.add(key);
  try {
    await entry.cast(spell, {});
  } finally {
    setTimeout(() => castingFromWindow.delete(key), 3000);
  }
  const after = summoner.system.resources.focus?.value ?? 0;
  if (before > 0 && after >= before) return { ok: false };
  if (before <= 0) return { ok: false };
  return { ok: true, rank: spell.rank };
}

export function castMessageInfo(message) {
  const origin = message.flags?.pf2e?.origin;
  if (!origin?.rollOptions?.includes(CAST_OPTION)) return null;
  const item = message.item;
  if (!item?.isOfType?.("spell")) return null;
  const actor = message.actor;
  if (!actor) return null;
  if (castingFromWindow.has(`${actor.id}:${item.slug}`)) return null;
  const rank = Number(origin.castRank ?? message.flags?.pf2e?.casting?.castRank ?? item.rank) || item.rank;
  return { actor, slug: item.slug, rank };
}

async function postCard(summoner, title, body, flags = {}) {
  return ChatMessage.implementation.create({
    speaker: ChatMessage.implementation.getSpeaker({ actor: summoner }),
    content: `<div class="${MODULE_ID}-card"><header><i class="fa-solid fa-people-group"></i> ${title}</header>${body}</div>`,
    flags: { [MODULE_ID]: flags },
  });
}

function portrait(actor) {
  return `<img src="${esc(actor.img)}" alt="" width="36" height="36">`;
}

function memberChoices(members, name, checkedId) {
  return members.map((m) => `
    <label class="${MODULE_ID}-choice">
      <input type="radio" name="${name}" value="${m.actor.id}" ${m.actor.id === checkedId ? "checked" : ""}>
      ${portrait(m.actor)}
      <span><strong>${esc(m.actor.name)}</strong><small>${esc(m.typeName ?? "Eidolon")}, ${esc(sizeLabel(m.actor))}</small></span>
    </label>`).join("");
}

function sizeLabel(actor) {
  const size = actor.system.traits?.size?.value ?? "med";
  return game.i18n.localize(CONFIG.PF2E.actorSizes?.[size] ?? size);
}

async function formDialog({ title, icon, content, ok, width = 440 }) {
  const result = await DialogV2.wait({
    window: { title, icon },
    position: { width },
    content: `<div class="${MODULE_ID}-dialog">${content}</div>`,
    buttons: [
      {
        action: "ok",
        label: ok,
        icon: "fa-solid fa-check",
        default: true,
        callback: (_event, button) => new foundry.applications.ux.FormDataExtended(button.form).object,
      },
      { action: "cancel", label: "Cancel", icon: "fa-solid fa-xmark" },
    ],
    rejectClose: false,
  });
  return result && typeof result === "object" ? result : null;
}

// ---------------------------------------------------------------------------------------------------------------- convoke
export async function convokeFlow(summoner, { alreadyCast = false } = {}) {
  const primary = getPrimary(summoner);
  const others = getMembers(summoner).filter((m) => m.actor && !m.isPrimary && !m.locked);
  if (!others.length) return notify("Link at least two eidolons to your assembly first.", "warn");

  const warping = hasFeat(summoner, FEAT.warping);
  const range = summoner.level >= 16 ? 30 : 15;
  const manifested = primary ? !!sceneTokenOf(primary) : false;
  const content = `
    <p>Swap ${primary ? `<strong>${esc(primary.name)}</strong>` : "your eidolon"} for:</p>
    <div class="${MODULE_ID}-choices">${memberChoices(others, "target", others[0].actor.id)}</div>
    ${primary ? `<p class="hint">Conditions, effects and persistent damage move to the new eidolon. It can't use actions with a frequency until your next turn.${manifested ? "" : ` ${esc(primary.name)} isn't on this scene, so only the primary changes.`}</p>` : ""}
    ${warping ? `<label class="${MODULE_ID}-check"><input type="checkbox" name="warp" checked> Warping Convoke: teleport up to ${range} feet after the swap</label>` : ""}`;
  const res = await formDialog({ title: "Convoke", icon: "fa-solid fa-arrows-rotate", content, ok: alreadyCast ? "Swap" : "Cast convoke" });
  if (!res?.target) return;

  if (!alreadyCast) {
    const cast = await castSpell(summoner, SPELL.convoke);
    if (!cast.ok) return;
  }
  const to = game.actors.get(res.target);
  const result = primary ? await swapEidolons(primary, to, { carry: true, lockout: true }) : { ok: true, token: null, moved: [] };
  if (!result.ok) {
    return postCard(summoner, "Convoke fails", `<p>${esc(result.reason)}</p>`);
  }
  await setPrimaryFlag(summoner, to.id);

  let warped = "";
  if (warping && res.warp && result.token) {
    const spot = await pickPoint({
      prompt: `Click where ${to.name} teleports (up to ${range} feet)`,
      origin: tokenCenter(result.token),
      maxDistance: range,
      width: result.token.width,
      height: result.token.height,
    });
    if (spot && isAreaFree(canvas.scene, spot.x, spot.y, result.token.width, result.token.height, [result.token.id])) {
      await teleportToken(result.token, spot.x, spot.y);
      warped = `<p>Warping Convoke: teleported without triggering reactions.</p>`;
    } else if (spot) {
      notify("That space is occupied, so the eidolon stays put.", "warn");
    }
  }
  const moved = result.moved.length ? `<p class="hint">Moved over: ${result.moved.map(esc).join(", ")}</p>` : "";
  return postCard(summoner, "Convoke",
    `<p>${primary ? `${esc(primary.name)} returns to the assembly. ` : ""}<strong>${esc(to.name)}</strong> takes its place.</p>${moved}${warped}
     <p class="hint">${esc(EFFECT.convoked)}: no actions with a frequency until your next turn.</p>`);
}

// Free swap for daily preparations or Refocus. No Focus Point, no lockout.
export async function setPrimaryFlow(summoner, eidolonId) {
  const primary = getPrimary(summoner);
  const to = game.actors.get(eidolonId);
  if (!to || primary?.id === eidolonId) return;
  if (primary && sceneTokenOf(primary)) {
    const result = await swapEidolons(primary, to, { carry: true, lockout: false });
    if (!result.ok) return notify(result.reason, "warn");
  }
  await setPrimaryFlag(summoner, eidolonId);
  notify(`${to.name} is now your primary eidolon.`);
}

// ---------------------------------------------------------------------------------------------------------------- assembled assault
export async function assaultFlow(summoner, { alreadyCast = false } = {}) {
  const primary = getPrimary(summoner);
  const others = getMembers(summoner).filter((m) => m.actor && !m.isPrimary && !m.locked);
  if (!others.length) return notify("Link at least two eidolons to your assembly first.", "warn");
  const content = `
    <p>Choose the secondary eidolon to call forth:</p>
    <div class="${MODULE_ID}-choices">${memberChoices(others, "target", others[0].actor.id)}</div>
    <p class="hint">You'll place it within 60 feet. It provides flanking, both eidolons Strike, and it returns to the assembly when you click Return on the chat card or your turn ends.</p>`;
  const res = await formDialog({ title: "Assembled Assault", icon: "fa-solid fa-hand-fist", content, ok: alreadyCast ? "Call forth" : "Cast assembled assault" });
  if (!res?.target) return;
  if (!alreadyCast) {
    const cast = await castSpell(summoner, SPELL.assault);
    if (!cast.ok) return;
  }
  await endAssault(summoner);
  const secondary = game.actors.get(res.target);
  const scene = canvas.scene;
  if (!scene) return notify("Open a scene first.", "warn");
  const anchor = sceneTokenOf(summoner, scene);
  const probe = await secondary.getTokenDocument({ x: 0, y: 0 });
  const spot = await pickPoint({
    prompt: `Click where ${secondary.name} appears (within 60 feet)`,
    origin: anchor ? tokenCenter(anchor) : null,
    maxDistance: anchor ? 60 : null,
    width: probe.width,
    height: probe.height,
  });
  if (!spot) return;
  if (!isAreaFree(scene, spot.x, spot.y, probe.width, probe.height)) notify("That space is occupied; placing it anyway.", "warn");
  const data = await tokenDataFor(secondary, spot.x, spot.y, { disposition: anchor?.disposition ?? probe.disposition });
  const [token] = await createTokens(scene, [data]);

  let boosted = "";
  const boost = primary?.itemTypes.effect.find((e) => e.slug === BOOST_EIDOLON_SLUG);
  if (boost && secondary.isOwner) {
    const copy = boost.toObject();
    delete copy._id;
    foundry.utils.setProperty(copy, `flags.${MODULE_ID}.assaultTemp`, true);
    await secondary.createEmbeddedDocuments("Item", [copy]);
    boosted = `<p class="hint">Boost Eidolon applies to ${esc(secondary.name)} too.</p>`;
  }
  await summoner.setFlag(MODULE_ID, "assault", { sceneId: scene.id, tokenId: token?.id ?? null, actorId: secondary.id });
  return postCard(summoner, "Assembled Assault",
    `<p><strong>${esc(primary?.name ?? "Your eidolon")}</strong> and <strong>${esc(secondary.name)}</strong> each Strike a creature in reach.
     If both hit the same creature, combine their damage for resistances and weaknesses. The multiple attack penalty increases only after both attacks.</p>${boosted}
     <button type="button" data-${MODULE_ID}-action="end-assault" data-summoner="${summoner.id}"><i class="fa-solid fa-rotate-left"></i> Return to assembly</button>`);
}

export async function endAssault(summoner) {
  const state = summoner.getFlag(MODULE_ID, "assault");
  if (!state) return;
  const scene = game.scenes.get(state.sceneId);
  if (scene?.tokens.has(state.tokenId)) await deleteTokens(scene, [state.tokenId]);
  const secondary = game.actors.get(state.actorId);
  if (secondary?.isOwner) {
    const temp = secondary.items.filter((i) => i.flags?.[MODULE_ID]?.assaultTemp).map((i) => i.id);
    if (temp.length) await secondary.deleteEmbeddedDocuments("Item", temp);
  }
  await summoner.unsetFlag(MODULE_ID, "assault");
}

// ---------------------------------------------------------------------------------------------------------------- combination convocation
function initialAbility(eidolon) {
  const ref = eidolon.flags?.pf2e?.["eidolon-features"]?.initial;
  if (!ref) return null;
  const id = String(ref).split(".").pop();
  return eidolon.itemTypes.feat.find((f) => (f.sourceId ?? "").endsWith(id)) ?? null;
}

function unarmedAttacks(eidolon) {
  const weapons = eidolon.itemTypes.weapon;
  const unarmed = weapons.filter((w) => w.category === "unarmed");
  return unarmed.length ? unarmed : weapons;
}

function fuseOptions(primary, eidolon) {
  const have = new Set(primary.itemTypes.feat.map((f) => f.slug));
  const evolutions = eidolon.itemTypes.feat.filter((f) => f.traits.has("evolution") && !have.has(f.slug));
  const initial = initialAbility(eidolon);
  return {
    evolutions,
    initial: initial && !have.has(initial.slug) ? initial : null,
    unarmed: unarmedAttacks(eidolon),
  };
}

function select(name, items) {
  return `<select name="${name}">${items.map((i) => `<option value="${i.id}">${esc(i.name)}</option>`).join("")}</select>`;
}

function fuseContent(primary, candidates, maxSources, maxBenefits, rank) {
  const blocks = candidates.map((m) => {
    const o = fuseOptions(primary, m.actor);
    const id = m.actor.id;
    const rows = [];
    if (o.evolutions.length) rows.push(`<label class="${MODULE_ID}-check"><input type="checkbox" name="evo-${id}"> Evolution feat ${select(`evo-${id}-item`, o.evolutions)}</label>`);
    if (o.initial) rows.push(`<label class="${MODULE_ID}-check"><input type="checkbox" name="init-${id}"> Initial ability: ${esc(o.initial.name)}</label>`);
    if (o.unarmed.length) rows.push(`<label class="${MODULE_ID}-check"><input type="checkbox" name="atk-${id}"> Unarmed attack ${select(`atk-${id}-item`, o.unarmed)}</label>`);
    if (!rows.length) rows.push(`<p class="hint">Nothing to take from this eidolon.</p>`);
    return `<fieldset><legend>${portrait(m.actor)} ${esc(m.actor.name)}</legend>${rows.join("")}</fieldset>`;
  });
  return `
    <p>Fuse into <strong>${esc(primary.name)}</strong> (rank ${rank}). Choose up to <strong>${maxBenefits}</strong> benefits from up to <strong>${maxSources}</strong> eidolon${maxSources > 1 ? "s" : ""}.</p>
    ${blocks.join("")}
    <fieldset><legend>Fusion</legend>
      <label class="${MODULE_ID}-check"><input type="checkbox" name="size"> Greater size: one size larger, +5 feet reach</label>
      <label class="${MODULE_ID}-check"><input type="checkbox" name="blast"> Fusion blast: Fortitude save in a 30-foot emanation or pushed away</label>
    </fieldset>
    <p class="hint">Lasts 1 minute. Casting convoke or unmanifesting the eidolon ends it.</p>`;
}

export async function fuseFlow(summoner, { alreadyCast = false, rank = null } = {}) {
  const primary = getPrimary(summoner);
  if (!primary) return notify("Set a primary eidolon first.", "warn");
  const candidates = getMembers(summoner).filter((m) => m.actor && !m.isPrimary && !m.locked);
  if (!candidates.length) return notify("Link at least two eidolons to your assembly first.", "warn");
  const spell = findSpell(summoner, SPELL.combination);
  rank ??= spell?.rank ?? 6;
  const maxSources = rank >= 7 ? 2 : 1;
  const maxBenefits = rank >= 7 ? 3 : 2;

  let picks = null;
  while (!picks) {
    const res = await formDialog({
      title: "Combination Convocation",
      icon: "fa-solid fa-circle-nodes",
      content: fuseContent(primary, candidates, maxSources, maxBenefits, rank),
      ok: alreadyCast ? "Fuse" : "Cast and fuse",
      width: 520,
    });
    if (!res) return;
    const chosen = [];
    for (const m of candidates) {
      const a = m.actor;
      if (res[`evo-${a.id}`]) chosen.push({ source: a, item: a.items.get(res[`evo-${a.id}-item`]), kind: "evolution feat" });
      if (res[`init-${a.id}`]) chosen.push({ source: a, item: initialAbility(a), kind: "initial ability" });
      if (res[`atk-${a.id}`]) chosen.push({ source: a, item: a.items.get(res[`atk-${a.id}-item`]), kind: "unarmed attack" });
    }
    const total = chosen.length + (res.size ? 1 : 0) + (res.blast ? 1 : 0);
    const sources = new Set(chosen.map((c) => c.source.id));
    if (!total) notify("Choose at least one benefit.", "warn");
    else if (total > maxBenefits) notify(`You can choose up to ${maxBenefits} benefits.`, "warn");
    else if (sources.size > maxSources) notify(`At rank ${rank} you can draw from ${maxSources} eidolon${maxSources > 1 ? "s" : ""}.`, "warn");
    else picks = { chosen, size: !!res.size, blast: !!res.blast };
  }

  if (!alreadyCast) {
    const cast = await castSpell(summoner, SPELL.combination);
    if (!cast.ok) return;
    rank = cast.rank ?? rank;
  }

  // Replace any fusion already running.
  const old = primary.items.filter((i) => i.flags?.[MODULE_ID]?.fusion).map((i) => i.id);
  if (old.length) await primary.deleteEmbeddedDocuments("Item", old);

  const sourceNames = [...new Set(picks.chosen.map((c) => c.source.name))];
  const fusion = await applyEffectByName(primary, EFFECT.fusion, { fusion: true, sources: picks.chosen.map((c) => c.source.id) });
  if (!fusion) return notify("The Combination Convocation effect is missing from the compendium.", "error");
  if (sourceNames.length) await fusion.update({ name: `${EFFECT.fusion} (${sourceNames.join(", ")})`, "system.level.value": rank });

  const copies = picks.chosen.filter((c) => c.item).map((c) => {
    const d = stripGrantFlags(c.item.toObject());
    d.name = `${c.item.name} (fused: ${c.source.name})`;
    if (d.flags?.[MODULE_ID]) {
      delete d.flags[MODULE_ID].evolutionSlot;
      delete d.flags[MODULE_ID].evolutionSource;
    }
    foundry.utils.setProperty(d, `flags.${MODULE_ID}.fusedBy`, fusion.id);
    return d;
  });
  if (copies.length) await primary.createEmbeddedDocuments("Item", copies);
  if (picks.size) await applyEffectByName(primary, EFFECT.fusionSize, { fusedBy: fusion.id });

  const lines = picks.chosen.map((c) => `<li>${esc(c.source.name)}'s ${c.kind}: ${esc(c.item?.name ?? "missing")}</li>`);
  if (picks.size) lines.push("<li>Greater size: one size larger, +5 feet reach</li>");
  await postCard(summoner, "Combination Convocation", `<p><strong>${esc(primary.name)}</strong> fuses with ${sourceNames.map(esc).join(" and ") || "the assembly"} for 1 minute.</p><ul>${lines.join("")}</ul>`);

  if (picks.blast) {
    const dc = spell?.spellcasting?.statistic?.dc?.value ?? summoner.attributes?.classDC?.value ?? summoner.classDC?.dc?.value;
    const check = dc ? `@Check[fortitude|dc:${dc}|traits:summoner,polymorph]` : "@Check[fortitude]";
    await postCard(summoner, "Fusion blast",
      `<p>@Template[type:emanation|distance:30] around ${esc(primary.name)}. Each creature in the area attempts ${check}.</p>
       <p><strong>Failure</strong> Pushed 10 feet away. <strong>Critical Failure</strong> Pushed 20 feet away.</p>`);
  }
}

// Removes fused copies when the Combination Convocation effect ends.
export async function cleanupFusion(effect) {
  const actor = effect.actor;
  if (!actor?.isOwner) return;
  const ids = actor.items.filter((i) => i.flags?.[MODULE_ID]?.fusedBy === effect.id).map((i) => i.id);
  if (ids.length) await actor.deleteEmbeddedDocuments("Item", ids);
}
