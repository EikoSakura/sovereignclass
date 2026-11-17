// Convoker automation entry point: wires hooks to the Assembly window and the convoke / assault / fuse flows.
import {
  FEAT, FEAT_SPELLS, MODULE_ID, SPELL, ensureConvokerSpellcasting, getConvoker, getPrimary, grantFeatSpell,
  isConvoker, linkedEidolons, registerSocket, revokeFeatSpell, sceneTokenOf,
} from "./core.mjs";
import { manifest, unmanifest } from "./canvas.mjs";
import { assaultFlow, castMessageInfo, cleanupFusion, convokeFlow, endAssault, fuseFlow, setPrimaryFlow } from "./flows.mjs";
import { injectSheetTab, openAssembly, refreshAssemblies } from "./app.mjs";
import { fillEvolutionDefaults, invalidateEvolutionOptions, isEvolution, removeEvolutionSlot } from "./evolutions.mjs";
import { registerKamiWard } from "./kami.mjs";
import { exportAssembly, patchExportImport, restoreBundle } from "./bundle.mjs";

const mine = (userId) => userId === game.user.id;

Hooks.once("setup", () => {
  patchExportImport();
});

Hooks.once("ready", () => {
  registerSocket();
  registerKamiWard();
  game.modules.get(MODULE_ID).api = {
    openAssembly,
    convoke: (actor) => convokeFlow(actor),
    assembledAssault: (actor) => assaultFlow(actor),
    fuse: (actor) => fuseFlow(actor),
    setPrimary: setPrimaryFlow,
    exportAssembly,
    restoreBundle,
  };
});

// ---------------------------------------------------------------------------------------------------------------- sheet tab and button
Hooks.on("renderCharacterSheetPF2e", (sheet, html) => injectSheetTab(sheet, html));

Hooks.on("getActorSheetHeaderButtons", (sheet, buttons) => {
  const actor = sheet.actor;
  if (!actor || !(isConvoker(actor) || getConvoker(actor))) return;
  buttons.unshift({
    label: "Assembly",
    class: `${MODULE_ID}-assembly`,
    icon: "fa-solid fa-people-group",
    onclick: () => openAssembly(actor),
  });
});

// ---------------------------------------------------------------------------------------------------------------- casting
Hooks.on("createChatMessage", (message, _options, userId) => {
  if (!mine(userId)) return;
  const cast = castMessageInfo(message);
  if (cast && isConvoker(cast.actor)) {
    if (cast.slug === SPELL.convoke) return void convokeFlow(cast.actor, { alreadyCast: true });
    if (cast.slug === SPELL.assault) return void assaultFlow(cast.actor, { alreadyCast: true });
    if (cast.slug === SPELL.combination) return void fuseFlow(cast.actor, { alreadyCast: true, rank: cast.rank });
    return;
  }

  // Using Manifest Eidolon or Refocus from a convoker's sheet.
  const item = message.item;
  const actor = message.actor;
  if (!item || !isConvoker(actor)) return;
  if (item.slug === "manifest-eidolon") {
    const primary = getPrimary(actor);
    if (!primary) return void openAssembly(actor, { notice: "Choose a primary eidolon first." });
    return void (sceneTokenOf(primary) ? unmanifest(primary) : manifest(actor, primary));
  }
  if (item.slug === "refocus" && linkedEidolons(actor).length > 1) {
    openAssembly(actor, { notice: "Refocus: you can change your primary eidolon for free." });
  }
});

Hooks.on("renderChatMessageHTML", (message, html) => {
  const button = html.querySelector?.(`[data-${MODULE_ID}-action="end-assault"]`);
  if (!button) return;
  const summoner = game.actors.get(button.dataset.summoner);
  if (!summoner?.isOwner || !summoner.getFlag(MODULE_ID, "assault")) {
    button.disabled = true;
    return;
  }
  button.addEventListener("click", async (event) => {
    event.preventDefault();
    button.disabled = true;
    await endAssault(summoner);
  });
});

Hooks.on("pf2e.endTurn", (combatant, _encounter, userId) => {
  const actor = combatant?.actor;
  if (mine(userId) && isConvoker(actor) && actor.getFlag(MODULE_ID, "assault")) endAssault(actor);
});

Hooks.on("pf2e.restForTheNight", (actor) => {
  if (isConvoker(actor) && actor.isOwner && linkedEidolons(actor).length > 1) {
    openAssembly(actor, { notice: "Daily preparations: choose today's primary eidolon, and retrain any evolution feats." });
  }
});

// ---------------------------------------------------------------------------------------------------------------- items
Hooks.on("createItem", async (item, _options, userId) => {
  const actor = item.actor;
  if (!actor) {
    if (isEvolution(item)) invalidateEvolutionOptions();
    return;
  }
  refreshAssemblies(actor);
  if (!mine(userId) || item.type !== "feat") return;
  if (FEAT_SPELLS[item.slug] && isConvoker(actor)) await grantFeatSpell(actor, item);
  if (isEvolution(item) && isConvoker(actor) && !item.flags?.[MODULE_ID]?.evolutionSlot) {
    await fillEvolutionDefaults(actor);
    if (linkedEidolons(actor).length > 1) {
      openAssembly(actor, { notice: `${item.name}: each eidolon got it by default. Pick a different evolution feat for any of them below.` });
    }
  }
  if (item.slug === FEAT.assembly) {
    await ensureConvokerSpellcasting(actor);
    for (const feat of actor.itemTypes.feat) if (FEAT_SPELLS[feat.slug]) await grantFeatSpell(actor, feat);
    openAssembly(actor, { notice: "Create or drop an eidolon actor into each slot of your assembly." });
  }
});

Hooks.on("deleteItem", async (item, _options, userId) => {
  const actor = item.actor;
  if (!actor) return;
  refreshAssemblies(actor);
  if (!mine(userId)) return;
  if (item.flags?.[MODULE_ID]?.fusion) await cleanupFusion(item);
  if (item.type === "feat" && FEAT_SPELLS[item.slug]) await revokeFeatSpell(actor, item);
  if (isEvolution(item) && isConvoker(actor) && !item.flags?.[MODULE_ID]?.evolutionSlot) await removeEvolutionSlot(actor, item.id);
});

Hooks.on("updateItem", (item) => refreshAssemblies(item.actor));

// ---------------------------------------------------------------------------------------------------------------- actors and tokens
Hooks.on("updateActor", async (actor, changes, _options, userId) => {
  refreshAssemblies(actor);
  if (!mine(userId) || !isConvoker(actor)) return;
  const level = foundry.utils.getProperty(changes, "system.details.level.value");
  if (level === undefined) return;
  for (const eidolon of linkedEidolons(actor)) {
    if (eidolon.isOwner && eidolon.level !== level) await eidolon.update({ "system.details.level.value": level });
  }
});

Hooks.on("deleteActor", (actor) => refreshAssemblies(getConvoker(actor) ?? actor));
Hooks.on("createToken", (token) => refreshAssemblies(token.actor));
Hooks.on("deleteToken", (token) => refreshAssemblies(token.actor));
