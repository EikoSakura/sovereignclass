// The Assembly view: one card per slot (each its own eidolon actor) plus each eidolon's evolution feats.
// The same view renders in its own window (AssemblyApp) and in an "Assembly" tab on the summoner's sheet.
import {
  FEAT, MODULE_ID, createEidolonActor, ensureConvokerSpellcasting, getConvoker, getMembers, getPrimary, hasFeat,
  isConvoker, linkEidolon, localizeLabel as esc, notify, sceneTokenOf, slotCount, syncSharedGear,
  toolbeltShareEnabled, unlinkEidolon,
} from "./core.mjs";
import { manifest, unmanifest } from "./canvas.mjs";
import { assaultFlow, convokeFlow, fuseFlow, setPrimaryFlow } from "./flows.mjs";
import { exportAssembly, importAssemblyDialog } from "./bundle.mjs";
import {
  assignEvolution, assignedFor, assignedSource, evolutionOptions, evolutionSlots, fillEvolutionDefaults,
} from "./evolutions.mjs";

const { ApplicationV2 } = foundry.applications.api;
const FilePicker = () => foundry.applications.apps.FilePicker.implementation;
const OPEN = new Map();
export const SHEET_TAB = "sovereign-assembly";

// ================================================================================================================ render
function sizeName(actor) {
  return game.i18n.localize(CONFIG.PF2E.actorSizes?.[actor.system.traits?.size?.value] ?? "");
}

function card(m, editable) {
  if (m.locked) {
    return `<li class="slot locked" data-slot="${m.index}"><i class="fa-solid fa-lock"></i><span>Take Expanded Assemblage to open this slot</span></li>`;
  }
  const type = m.typeName ? `<span class="type">${esc(m.typeName)}</span>` : `<span class="type muted">Any eidolon</span>`;
  if (!m.actor) {
    const create = editable && m.typeUuid
      ? `<button type="button" data-assembly="create" data-slot="${m.index}"><i class="fa-solid fa-plus"></i> Create ${esc(m.typeName ?? "eidolon")}</button>`
      : "";
    const missing = m.missing ? `<span class="warn">The linked actor was deleted</span>` : "";
    return `<li class="slot empty" data-slot="${m.index}">
      <div class="drop"><i class="fa-solid fa-user-plus"></i><span>Drop an eidolon actor or ancestry here</span></div>
      ${type}${missing}${create}</li>`;
  }
  const a = m.actor;
  const owner = a.isOwner;
  const badges = [
    m.isPrimary ? `<span class="badge primary">Primary</span>` : "",
    sceneTokenOf(a) ? `<span class="badge manifested">Manifested</span>` : "",
    a.items.some((i) => i.flags?.[MODULE_ID]?.fusion) ? `<span class="badge fused">Fused</span>` : "",
  ].join("");
  const conditions = a.conditions?.active?.map((c) => esc(c.name)).join(", ");
  return `<li class="slot filled ${m.isPrimary ? "is-primary" : ""}" data-slot="${m.index}" data-actor-id="${a.id}">
    <div class="art">
      <img class="portrait" src="${esc(a.img)}" alt="" ${owner ? `data-assembly="editImage" data-tooltip="Change portrait"` : ""}>
      ${owner ? `<a class="token-art" data-assembly="editToken" data-tooltip="Change token art"><img src="${esc(a.prototypeToken.texture.src)}" alt=""></a>` : ""}
    </div>
    <div class="info">
      <a class="name" data-assembly="openSheet" data-tooltip="Open sheet">${esc(a.name)}</a>
      ${type}
      <span class="meta">Level ${a.level}, ${esc(sizeName(a))}</span>
      ${conditions ? `<span class="meta conditions">${conditions}</span>` : ""}
      <div class="badges">${badges}</div>
    </div>
    ${editable ? `<div class="controls">
      ${m.isPrimary ? "" : `<button type="button" data-assembly="setPrimary" data-tooltip="Make primary for free (daily preparations or Refocus)"><i class="fa-solid fa-star"></i> Set primary</button>`}
      <a data-assembly="unlink" data-tooltip="Unlink from the assembly"><i class="fa-solid fa-link-slash"></i></a>
    </div>` : ""}
  </li>`;
}

function evolutionTable(actor, members, options, editable) {
  const slots = evolutionSlots(actor);
  const eidolons = members.filter((m) => m.actor).map((m) => m.actor);
  if (!slots.length) {
    return `<p class="hint">Evolution feats you take show up here. Each eidolon in your assembly gets its own pick at that level or lower.</p>`;
  }
  if (!eidolons.length) return `<p class="hint">Link eidolons to pick their evolution feats.</p>`;
  const head = eidolons.map((e) => `<th><img src="${esc(e.img)}" alt=""><span>${esc(e.name)}</span></th>`).join("");
  const rows = slots.map((slot) => {
    const cells = eidolons.map((e) => {
      const item = assignedFor(e, slot.id);
      const current = assignedSource(item);
      const choices = (options ?? []).filter((o) => o.level <= slot.level);
      const known = current && !choices.some((o) => o.uuid === current)
        ? `<option value="${esc(current)}" selected>${esc(item.name)}</option>` : "";
      const opts = choices.map((o) => `<option value="${esc(o.uuid)}" ${o.uuid === current ? "selected" : ""}>${esc(o.name)} (${o.level})</option>`).join("");
      const disabled = editable && e.isOwner ? "" : "disabled";
      return `<td><select data-assembly-evolution data-slot-id="${slot.id}" data-actor-id="${e.id}" ${disabled}>
        <option value="" ${item ? "" : "selected"}>None</option>${known}${opts}</select></td>`;
    }).join("");
    return `<tr><th class="slot-name"><span>${esc(slot.name)}</span><small>Level ${slot.level}</small></th>${cells}</tr>`;
  }).join("");
  const fill = editable ? `<button type="button" data-assembly="fillEvolutions"><i class="fa-solid fa-wand-magic-sparkles"></i> Fill empty picks</button>` : "";
  return `<table class="evolutions"><thead><tr><th>Your evolution feat</th>${head}</tr></thead><tbody>${rows}</tbody></table>
    <div class="evo-footer"><span class="hint">Retrain these at daily preparations. Check each eidolon meets the feat's prerequisites.</span>${fill}</div>`;
}

export async function renderAssembly(actor, { notice = null, inSheet = false } = {}) {
  const editable = actor.isOwner;
  const sel = actor.itemTypes.feat.find((f) => f.slug === FEAT.assembly)?.flags?.pf2e?.rulesSelections ?? {};
  const members = getMembers(actor);
  const primary = getPrimary(actor);
  const manifested = primary ? !!sceneTokenOf(primary) : false;
  const focus = actor.system.resources.focus ?? { value: 0, max: 0 };
  const hp = actor.system.attributes.hp;
  const options = evolutionSlots(actor).length ? await evolutionOptions() : [];

  const notices = [];
  if (notice) notices.push(`<p class="notice">${esc(notice)} <a data-assembly="dismissNotice"><i class="fa-solid fa-xmark"></i></a></p>`);
  if (game.modules.get("pf2e-toolbelt")?.active && !toolbeltShareEnabled()) {
    notices.push(`<p class="notice warn">Turn on pf2e-toolbelt's Shared Data setting so your eidolons share your Hit Points.</p>`);
  }
  if (editable && !actor.itemTypes.spellcastingEntry.some((e) => e.system.prepared?.value === "prepared")) {
    notices.push(`<p class="notice">Your prepared convoker spellcasting isn't set up. <button type="button" data-assembly="spellcasting">Set it up</button></p>`);
  }
  const header = inSheet ? "" : `
    <header class="summoner">
      <img src="${esc(actor.img)}" alt="">
      <div><h2>${esc(actor.name)}</h2><div class="chips">
        ${sel.convokerTradition ? `<span class="chip">${esc(sel.convokerTradition)} tradition</span>` : ""}
        ${sel.convokerKey ? `<span class="chip">Key: ${esc(game.i18n.localize(CONFIG.PF2E.abilities?.[sel.convokerKey] ?? sel.convokerKey))}</span>` : ""}
        <span class="chip">Focus ${focus.value}/${focus.max}</span>
        <span class="chip">HP ${hp.value}/${hp.max}</span>
        <span class="chip">${members.filter((m) => m.actor).length}/${slotCount(actor)} eidolons</span>
      </div></div>
    </header>`;
  const bar = editable ? `<footer class="bar">
      <div class="group">
        <button type="button" data-assembly="manifest" ${primary ? "" : "disabled"}><i class="fa-solid fa-${manifested ? "eye-slash" : "wand-sparkles"}"></i> ${manifested ? "Unmanifest" : "Manifest"}</button>
        ${hasFeat(actor, FEAT.dedication) ? `<button type="button" class="primary" data-assembly="convoke"><i class="fa-solid fa-arrows-rotate"></i> Convoke</button>` : ""}
        ${hasFeat(actor, FEAT.assembledAssault) ? `<button type="button" data-assembly="assault"><i class="fa-solid fa-hand-fist"></i> Assembled Assault</button>` : ""}
        ${hasFeat(actor, FEAT.combination) ? `<button type="button" data-assembly="fuse"><i class="fa-solid fa-circle-nodes"></i> Fuse</button>` : ""}
      </div>
      <div class="group">
        ${inSheet ? `<button type="button" data-assembly="popout" data-tooltip="Open in its own window"><i class="fa-solid fa-up-right-from-square"></i></button>` : ""}
        <button type="button" data-assembly="sync" data-tooltip="Copy eidolon-trait and invested gear from the primary to the others"><i class="fa-solid fa-rotate"></i> Sync gear</button>
        <button type="button" data-assembly="exportBundle" data-tooltip="Save the summoner and every eidolon, with images, to one file"><i class="fa-solid fa-file-export"></i> Export</button>
        <button type="button" data-assembly="importBundle" data-tooltip="Load an exported assembly onto this summoner"><i class="fa-solid fa-file-import"></i> Import</button>
      </div>
    </footer>` : "";
  return `<div class="${MODULE_ID}-assembly-view" data-summoner-id="${actor.id}">
    ${header}${notices.join("")}
    <ol class="slots">${members.map((m) => card(m, editable)).join("")}</ol>
    ${bar}
    <section class="evolution-section"><h3><i class="fa-solid fa-dna"></i> Evolution feats</h3>${evolutionTable(actor, members, options, editable)}</section>
  </div>`;
}

// ================================================================================================================ actions
function memberOf(target) {
  const id = target.closest("[data-actor-id]")?.dataset.actorId;
  return id ? game.actors.get(id) : null;
}

function pickImage(current, type, callback) {
  new (FilePicker())({ type, current, callback }).render(true);
}

const ACTIONS = {
  convoke: (actor) => convokeFlow(actor),
  assault: (actor) => assaultFlow(actor),
  fuse: (actor) => fuseFlow(actor),
  async manifest(actor) {
    const primary = getPrimary(actor);
    if (!primary) return;
    if (sceneTokenOf(primary)) await unmanifest(primary);
    else await manifest(actor, primary);
    refreshAssemblies(actor);
  },
  async setPrimary(actor, target) {
    const eidolon = memberOf(target);
    if (eidolon) await setPrimaryFlow(actor, eidolon.id);
  },
  async create(actor, target) {
    try {
      const eidolon = await createEidolonActor(actor, Number(target.dataset.slot));
      await fillEvolutionDefaults(actor);
      notify(`${eidolon.name} created and linked.`);
    } catch (err) {
      notify(err.message, "error");
    }
  },
  async unlink(actor, target) {
    const index = Number(target.closest("[data-slot]")?.dataset.slot);
    const eidolon = memberOf(target);
    const ok = await foundry.applications.api.DialogV2.confirm({
      window: { title: "Unlink eidolon" },
      content: `<p>Unlink <strong>${esc(eidolon?.name)}</strong> from the assembly? The actor isn't deleted.</p>`,
    });
    if (ok) await unlinkEidolon(actor, index);
  },
  openSheet: (_actor, target) => memberOf(target)?.sheet.render(true),
  editImage(_actor, target) {
    const e = memberOf(target);
    if (!e) return;
    pickImage(e.img, "image", async (path) => {
      const update = { img: path };
      const tex = e.prototypeToken.texture.src;
      if (tex === e.img || tex?.includes("mystery-man")) update["prototypeToken.texture.src"] = path;
      await e.update(update);
    });
  },
  editToken(_actor, target) {
    const e = memberOf(target);
    if (!e) return;
    pickImage(e.prototypeToken.texture.src, "imagevideo", async (path) => {
      await e.update({ "prototypeToken.texture.src": path });
      for (const token of e.getActiveTokens(true, true)) if (token.isOwner) await token.update({ "texture.src": path });
    });
  },
  sync: (actor) => syncSharedGear(actor),
  async spellcasting(actor) {
    await ensureConvokerSpellcasting(actor);
    notify("Convoker spellcasting set to prepared.");
  },
  async fillEvolutions(actor) {
    const n = await fillEvolutionDefaults(actor);
    notify(n ? `Filled ${n} evolution pick${n === 1 ? "" : "s"}.` : "Every eidolon already has a pick for each evolution feat.");
  },
  exportBundle: (actor) => exportAssembly(actor),
  importBundle: (actor) => importAssemblyDialog(actor),
  popout: (actor) => openAssembly(actor),
};

async function onDrop(actor, event, index) {
  event.preventDefault();
  event.currentTarget.classList.remove("drag-over");
  const data = foundry.applications.ux.TextEditor.implementation.getDragEventData(event);
  const member = getMembers(actor)[index];
  if (data?.type === "Item") {
    const item = await fromUuid(data.uuid);
    if (item?.type !== "ancestry" || !item.system.traits?.value?.includes("eidolon")) {
      return notify("Drop an eidolon ancestry (or an eidolon actor) on a slot.", "warn");
    }
    if (member?.actor) return notify(`Unlink ${member.actor.name} from that slot first.`, "warn");
    try {
      const eidolon = await createEidolonActor(actor, index, item.uuid);
      await fillEvolutionDefaults(actor);
      notify(`${eidolon.name} created and linked.`);
    } catch (err) {
      notify(err.message, "error");
    }
    return;
  }
  if (data?.type !== "Actor") return;
  const eidolon = await fromUuid(data.uuid);
  if (!eidolon?.isOfType?.("character")) return notify("Drop a character actor with an eidolon ancestry.", "warn");
  if (eidolon.id === actor.id) return;
  if (eidolon.pack) return notify("Import the actor into the world first.", "warn");
  if (!eidolon.isOwner) return notify("You need to own that actor.", "warn");
  const other = getConvoker(eidolon);
  if (other && other.id !== actor.id) return notify(`${eidolon.name} already belongs to ${other.name}'s assembly.`, "warn");
  await linkEidolon(actor, eidolon, index);
  await fillEvolutionDefaults(actor);
}

export function bindAssembly(root, actor, { onDismissNotice = null } = {}) {
  root.addEventListener("click", async (event) => {
    const target = event.target.closest("[data-assembly]");
    if (!target || !root.contains(target)) return;
    event.preventDefault();
    event.stopPropagation();
    const action = target.dataset.assembly;
    if (action === "dismissNotice") return onDismissNotice?.();
    const handler = ACTIONS[action];
    if (!handler) return;
    try {
      await handler(actor, target, event);
    } catch (err) {
      console.error(err);
      notify(err.message, "error");
    }
  });
  root.addEventListener("change", async (event) => {
    const select = event.target.closest("select[data-assembly-evolution]");
    if (!select) return;
    event.stopPropagation();
    const eidolon = game.actors.get(select.dataset.actorId);
    select.disabled = true;
    await assignEvolution(eidolon, select.dataset.slotId, select.value || null);
    refreshAssemblies(actor);
  });
  if (!actor.isOwner) return;
  for (const slot of root.querySelectorAll("li.slot:not(.locked)")) {
    slot.addEventListener("dragover", (event) => {
      event.preventDefault();
      slot.classList.add("drag-over");
    });
    slot.addEventListener("dragleave", () => slot.classList.remove("drag-over"));
    slot.addEventListener("drop", (event) => onDrop(actor, event, Number(slot.dataset.slot)));
  }
}

// ================================================================================================================ window
export function openAssembly(actor, { notice = null } = {}) {
  const summoner = isConvoker(actor) ? actor : getConvoker(actor);
  if (!summoner) return notify("This actor isn't a Convoker or linked to one.", "warn");
  let app = OPEN.get(summoner.id);
  if (!app) {
    app = new AssemblyApp(summoner);
    OPEN.set(summoner.id, app);
  }
  app.notice = notice;
  app.render({ force: true });
  return app;
}

// Re-renders every Assembly view (window and sheet tab) that involves this actor.
export function refreshAssemblies(actor) {
  if (!actor) return;
  const summoner = isConvoker(actor) ? actor : getConvoker(actor);
  if (!summoner) return;
  const app = OPEN.get(summoner.id);
  if (app?.rendered) app.debouncedRender();
  refreshSheetTab(summoner);
}

class AssemblyApp extends ApplicationV2 {
  constructor(actor, options = {}) {
    super({ id: `${MODULE_ID}-assembly-${actor.id}`, ...options });
    this.actor = actor;
    this.notice = null;
    this.debouncedRender = foundry.utils.debounce(() => this.render(), 100);
  }

  static DEFAULT_OPTIONS = {
    classes: [MODULE_ID, "assembly-app"],
    window: { icon: "fa-solid fa-people-group", resizable: true },
    position: { width: 780, height: "auto" },
  };

  get title() {
    return `Assembly: ${this.actor.name}`;
  }

  async close(options) {
    OPEN.delete(this.actor.id);
    return super.close(options);
  }

  async _renderHTML() {
    return renderAssembly(this.actor, { notice: this.notice });
  }

  _replaceHTML(result, content) {
    content.innerHTML = result;
  }

  _onRender() {
    const view = this.element.querySelector(`.${MODULE_ID}-assembly-view`);
    if (view) bindAssembly(view, this.actor, { onDismissNotice: () => { this.notice = null; this.render(); } });
  }
}

// ================================================================================================================ sheet tab
const sheetRefreshers = new Map();

function refreshSheetTab(summoner) {
  const sheet = summoner.sheet;
  if (!sheet?.rendered) return;
  let fn = sheetRefreshers.get(summoner.id);
  if (!fn) {
    fn = foundry.utils.debounce(() => fillSheetTab(sheet, summoner), 120);
    sheetRefreshers.set(summoner.id, fn);
  }
  fn();
}

async function fillSheetTab(sheet, actor) {
  const root = sheet.element?.[0] ?? sheet.element;
  const tab = root?.querySelector?.(`.tab[data-tab="${SHEET_TAB}"]`);
  if (!tab) return;
  const scroll = tab.scrollTop;
  tab.innerHTML = await renderAssembly(actor, { inSheet: true });
  const view = tab.querySelector(`.${MODULE_ID}-assembly-view`);
  if (view) bindAssembly(view, actor);
  tab.scrollTop = scroll;
}

// Adds an "Assembly" tab to a convoker's pf2e character sheet.
export function injectSheetTab(sheet, html) {
  const actor = sheet.actor;
  if (!isConvoker(actor)) return;
  const root = html instanceof HTMLElement ? html : html?.[0];
  const nav = root?.querySelector("nav.sheet-navigation[data-group='primary']");
  const content = root?.querySelector("section.sheet-content");
  if (!nav || !content || nav.querySelector(`[data-tab="${SHEET_TAB}"]`)) return;

  const link = document.createElement("a");
  link.className = "item";
  link.dataset.tab = SHEET_TAB;
  link.dataset.tooltip = "Assembly";
  link.setAttribute("role", "tab");
  link.setAttribute("aria-label", "Assembly");
  link.innerHTML = `<i class="fa-solid fa-people-group"></i>`;
  const manage = nav.querySelector(".manage-tabs");
  nav.insertBefore(link, manage ?? null);

  const tab = document.createElement("section");
  tab.className = `tab ${SHEET_TAB} major`;
  tab.dataset.group = "primary";
  tab.dataset.tab = SHEET_TAB;
  content.append(tab);

  const tabs = sheet._tabs?.find((t) => t.group === "primary" || t._navSelector?.includes("sheet-navigation")) ?? sheet._tabs?.[0];
  if (tabs?.active === SHEET_TAB) tabs.activate(SHEET_TAB);
  fillSheetTab(sheet, actor);
}
