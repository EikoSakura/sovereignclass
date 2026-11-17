// The Assembly window: one card per assembly slot, each linked to its own eidolon actor.
import {
  FEAT, MODULE_ID, createEidolonActor, ensureConvokerSpellcasting, getConvoker, getMembers, getPrimary, hasFeat,
  isConvoker, linkEidolon, localizeLabel as esc, notify, sceneTokenOf, slotCount, syncSharedGear,
  toolbeltShareEnabled, unlinkEidolon,
} from "./core.mjs";
import { manifest, unmanifest } from "./canvas.mjs";
import { assaultFlow, convokeFlow, fuseFlow, setPrimaryFlow } from "./flows.mjs";
import { exportAssembly, importAssemblyDialog } from "./bundle.mjs";

const { ApplicationV2 } = foundry.applications.api;
const FilePicker = () => foundry.applications.apps.FilePicker.implementation;
const OPEN = new Map();

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

// Re-renders open windows that involve this actor.
export function refreshAssemblies(actor) {
  if (!actor) return;
  for (const app of OPEN.values()) {
    if (!app.rendered) continue;
    const s = app.actor;
    if (s.id === actor.id || getConvoker(actor)?.id === s.id) app.debouncedRender();
  }
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
    position: { width: 760, height: "auto" },
    actions: {
      convoke: AssemblyApp.#onConvoke,
      assault: AssemblyApp.#onAssault,
      fuse: AssemblyApp.#onFuse,
      manifest: AssemblyApp.#onManifest,
      setPrimary: AssemblyApp.#onSetPrimary,
      create: AssemblyApp.#onCreate,
      unlink: AssemblyApp.#onUnlink,
      openSheet: AssemblyApp.#onOpenSheet,
      editImage: AssemblyApp.#onEditImage,
      editToken: AssemblyApp.#onEditToken,
      sync: AssemblyApp.#onSync,
      spellcasting: AssemblyApp.#onSpellcasting,
      exportBundle: AssemblyApp.#onExport,
      importBundle: AssemblyApp.#onImport,
      dismissNotice: AssemblyApp.#onDismissNotice,
    },
  };

  get title() {
    return `Assembly: ${this.actor.name}`;
  }

  async close(options) {
    OPEN.delete(this.actor.id);
    return super.close(options);
  }

  _context() {
    const actor = this.actor;
    const sel = actor.itemTypes.feat.find((f) => f.slug === FEAT.assembly)?.flags?.pf2e?.rulesSelections ?? {};
    const members = getMembers(actor);
    const primary = getPrimary(actor);
    return {
      actor,
      editable: actor.isOwner,
      tradition: sel.convokerTradition ?? null,
      key: sel.convokerKey ?? null,
      focus: actor.system.resources.focus ?? { value: 0, max: 0 },
      hp: actor.system.attributes.hp,
      members,
      primary,
      primaryManifested: primary ? !!sceneTokenOf(primary) : false,
      slots: slotCount(actor),
      feats: {
        convoke: hasFeat(actor, FEAT.dedication),
        assault: hasFeat(actor, FEAT.assembledAssault),
        fuse: hasFeat(actor, FEAT.combination),
      },
      shareOff: game.modules.get("pf2e-toolbelt")?.active ? !toolbeltShareEnabled() : null,
      noSpellcasting: !actor.itemTypes.spellcastingEntry.some((e) => e.system.prepared?.value === "prepared"),
    };
  }

  _card(m, ctx) {
    if (m.locked) {
      return `<li class="slot locked" data-slot="${m.index}"><i class="fa-solid fa-lock"></i><span>Take Expanded Assemblage to open this slot</span></li>`;
    }
    const type = m.typeName ? `<span class="type">${esc(m.typeName)}</span>` : `<span class="type muted">Any eidolon</span>`;
    if (!m.actor) {
      const create = ctx.editable && m.typeUuid
        ? `<button type="button" data-action="create" data-slot="${m.index}"><i class="fa-solid fa-plus"></i> Create ${esc(m.typeName ?? "eidolon")}</button>`
        : "";
      const missing = m.missing ? `<span class="warn">The linked actor was deleted</span>` : "";
      return `<li class="slot empty" data-slot="${m.index}">
        <div class="drop"><i class="fa-solid fa-user-plus"></i><span>Drop an eidolon actor or ancestry here</span></div>
        ${type}${missing}${create}</li>`;
    }
    const a = m.actor;
    const token = sceneTokenOf(a);
    const owner = a.isOwner;
    const badges = [
      m.isPrimary ? `<span class="badge primary">Primary</span>` : "",
      token ? `<span class="badge manifested">Manifested</span>` : "",
      a.items.some((i) => i.flags?.[MODULE_ID]?.fusion) ? `<span class="badge fused">Fused</span>` : "",
    ].join("");
    const conditions = a.conditions?.active?.map((c) => esc(c.name)).join(", ");
    return `<li class="slot filled ${m.isPrimary ? "is-primary" : ""}" data-slot="${m.index}" data-actor-id="${a.id}">
      <div class="art">
        <img class="portrait" src="${esc(a.img)}" alt="" ${owner ? `data-action="editImage" data-tooltip="Change portrait"` : ""}>
        ${owner ? `<a class="token-art" data-action="editToken" data-tooltip="Change token art"><img src="${esc(a.prototypeToken.texture.src)}" alt=""></a>` : ""}
      </div>
      <div class="info">
        <a class="name" data-action="openSheet" data-tooltip="Open sheet">${esc(a.name)}</a>
        ${type}
        <span class="meta">Level ${a.level}, ${esc(game.i18n.localize(CONFIG.PF2E.actorSizes?.[a.system.traits.size.value] ?? ""))}</span>
        ${conditions ? `<span class="meta conditions">${conditions}</span>` : ""}
        <div class="badges">${badges}</div>
      </div>
      ${ctx.editable ? `<div class="controls">
        ${m.isPrimary ? "" : `<button type="button" data-action="setPrimary" data-tooltip="Make primary for free (daily preparations or Refocus)"><i class="fa-solid fa-star"></i> Set primary</button>`}
        <a data-action="unlink" data-tooltip="Unlink from the assembly"><i class="fa-solid fa-link-slash"></i></a>
      </div>` : ""}
    </li>`;
  }

  async _renderHTML() {
    const ctx = this._context();
    const a = ctx.actor;
    const notices = [];
    if (this.notice) notices.push(`<p class="notice">${esc(this.notice)} <a data-action="dismissNotice"><i class="fa-solid fa-xmark"></i></a></p>`);
    if (ctx.shareOff) notices.push(`<p class="notice warn">Turn on pf2e-toolbelt's Shared Data setting so your eidolons share your Hit Points.</p>`);
    if (ctx.noSpellcasting && ctx.editable) notices.push(`<p class="notice">Your prepared convoker spellcasting isn't set up. <button type="button" data-action="spellcasting">Set it up</button></p>`);
    const p = ctx.primary;
    const manifestLabel = ctx.primaryManifested ? "Unmanifest" : "Manifest";
    return `
      <header class="summoner">
        <img src="${esc(a.img)}" alt="">
        <div>
          <h2>${esc(a.name)}</h2>
          <div class="chips">
            ${ctx.tradition ? `<span class="chip">${esc(ctx.tradition)} tradition</span>` : ""}
            ${ctx.key ? `<span class="chip">Key: ${esc(game.i18n.localize(CONFIG.PF2E.abilities?.[ctx.key] ?? ctx.key))}</span>` : ""}
            <span class="chip">Focus ${ctx.focus.value}/${ctx.focus.max}</span>
            <span class="chip">HP ${ctx.hp.value}/${ctx.hp.max}</span>
            <span class="chip">${ctx.members.filter((m) => m.actor).length}/${ctx.slots} eidolons</span>
          </div>
        </div>
      </header>
      ${notices.join("")}
      <ol class="slots">${ctx.members.map((m) => this._card(m, ctx)).join("")}</ol>
      ${ctx.editable ? `<footer class="bar">
        <div class="group">
          <button type="button" data-action="manifest" ${p ? "" : "disabled"}><i class="fa-solid fa-${ctx.primaryManifested ? "eye-slash" : "wand-sparkles"}"></i> ${manifestLabel}</button>
          ${ctx.feats.convoke ? `<button type="button" class="primary" data-action="convoke"><i class="fa-solid fa-arrows-rotate"></i> Convoke</button>` : ""}
          ${ctx.feats.assault ? `<button type="button" data-action="assault"><i class="fa-solid fa-hand-fist"></i> Assembled Assault</button>` : ""}
          ${ctx.feats.fuse ? `<button type="button" data-action="fuse"><i class="fa-solid fa-circle-nodes"></i> Fuse</button>` : ""}
        </div>
        <div class="group">
          <button type="button" data-action="sync" data-tooltip="Copy eidolon-trait and invested gear from the primary to the others"><i class="fa-solid fa-rotate"></i> Sync gear</button>
          <button type="button" data-action="exportBundle" data-tooltip="Save the summoner and every eidolon, with images, to one file"><i class="fa-solid fa-file-export"></i> Export</button>
          <button type="button" data-action="importBundle" data-tooltip="Load an exported assembly onto this summoner"><i class="fa-solid fa-file-import"></i> Import</button>
        </div>
      </footer>` : ""}`;
  }

  _replaceHTML(result, content) {
    content.innerHTML = result;
  }

  _onRender() {
    if (!this.actor.isOwner) return;
    for (const slot of this.element.querySelectorAll("li.slot:not(.locked)")) {
      slot.addEventListener("dragover", (event) => {
        event.preventDefault();
        slot.classList.add("drag-over");
      });
      slot.addEventListener("dragleave", () => slot.classList.remove("drag-over"));
      slot.addEventListener("drop", (event) => this.#onDrop(event, Number(slot.dataset.slot)));
    }
  }

  async #onDrop(event, index) {
    event.preventDefault();
    event.currentTarget.classList.remove("drag-over");
    const data = foundry.applications.ux.TextEditor.implementation.getDragEventData(event);
    if (data?.type === "Item") return this.#onDropAncestry(data, index);
    if (data?.type !== "Actor") return;
    const eidolon = await fromUuid(data.uuid);
    if (!eidolon?.isOfType?.("character")) return notify("Drop a character actor with an eidolon ancestry.", "warn");
    if (eidolon.id === this.actor.id) return;
    if (eidolon.pack) return notify("Import the actor into the world first.", "warn");
    if (!eidolon.isOwner) return notify("You need to own that actor.", "warn");
    const other = getConvoker(eidolon);
    if (other && other.id !== this.actor.id) return notify(`${eidolon.name} already belongs to ${other.name}'s assembly.`, "warn");
    await linkEidolon(this.actor, eidolon, index);
  }

  // An eidolon ancestry (any compendium, e.g. Summoners+) dropped on an empty slot creates that eidolon.
  async #onDropAncestry(data, index) {
    const item = await fromUuid(data.uuid);
    if (item?.type !== "ancestry" || !item.system.traits?.value?.includes("eidolon")) {
      return notify("Drop an eidolon ancestry (or an eidolon actor) on a slot.", "warn");
    }
    const member = getMembers(this.actor)[index];
    if (member?.actor) return notify(`Unlink ${member.actor.name} from that slot first.`, "warn");
    try {
      const eidolon = await createEidolonActor(this.actor, index, item.uuid);
      notify(`${eidolon.name} created and linked.`);
    } catch (err) {
      notify(err.message, "error");
    }
  }

  // ------------------------------------------------------------------------------------------------------------ actions
  static #member(target) {
    const id = target.closest("[data-actor-id]")?.dataset.actorId;
    return id ? game.actors.get(id) : null;
  }

  static async #onConvoke() {
    await convokeFlow(this.actor);
  }

  static async #onAssault() {
    await assaultFlow(this.actor);
  }

  static async #onFuse() {
    await fuseFlow(this.actor);
  }

  static async #onManifest() {
    const primary = getPrimary(this.actor);
    if (!primary) return;
    if (sceneTokenOf(primary)) await unmanifest(primary);
    else await manifest(this.actor, primary);
    this.render();
  }

  static async #onSetPrimary(_event, target) {
    const eidolon = AssemblyApp.#member(target);
    if (eidolon) await setPrimaryFlow(this.actor, eidolon.id);
  }

  static async #onCreate(_event, target) {
    const index = Number(target.dataset.slot);
    try {
      const eidolon = await createEidolonActor(this.actor, index);
      notify(`${eidolon.name} created and linked.`);
    } catch (err) {
      notify(err.message, "error");
    }
  }

  static async #onUnlink(_event, target) {
    const index = Number(target.closest("[data-slot]")?.dataset.slot);
    const eidolon = AssemblyApp.#member(target);
    const ok = await foundry.applications.api.DialogV2.confirm({
      window: { title: "Unlink eidolon" },
      content: `<p>Unlink <strong>${esc(eidolon?.name)}</strong> from the assembly? The actor isn't deleted.</p>`,
    });
    if (ok) await unlinkEidolon(this.actor, index);
  }

  static #onOpenSheet(_event, target) {
    AssemblyApp.#member(target)?.sheet.render(true);
  }

  static #onEditImage(_event, target) {
    const eidolon = AssemblyApp.#member(target);
    if (!eidolon) return;
    new (FilePicker())({
      type: "image",
      current: eidolon.img,
      callback: async (path) => {
        const update = { img: path };
        if (eidolon.prototypeToken.texture.src === eidolon.img || eidolon.prototypeToken.texture.src?.includes("mystery-man")) {
          update["prototypeToken.texture.src"] = path;
        }
        await eidolon.update(update);
      },
    }).render(true);
  }

  static #onEditToken(_event, target) {
    const eidolon = AssemblyApp.#member(target);
    if (!eidolon) return;
    new (FilePicker())({
      type: "imagevideo",
      current: eidolon.prototypeToken.texture.src,
      callback: async (path) => {
        await eidolon.update({ "prototypeToken.texture.src": path });
        for (const token of eidolon.getActiveTokens(true, true)) {
          if (token.isOwner) await token.update({ "texture.src": path });
        }
      },
    }).render(true);
  }

  static async #onSync() {
    await syncSharedGear(this.actor);
  }

  static async #onSpellcasting() {
    await ensureConvokerSpellcasting(this.actor);
    notify("Convoker spellcasting set to prepared.");
  }

  static async #onExport() {
    await exportAssembly(this.actor);
  }

  static async #onImport() {
    await importAssemblyDialog(this.actor);
  }

  static #onDismissNotice() {
    this.notice = null;
    this.render();
  }
}
