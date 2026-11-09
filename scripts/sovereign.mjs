// Registers the Sovereign trait so class feats filter correctly in the pf2e feat browser.
Hooks.once("init", () => {
  const PF2E = CONFIG.PF2E;
  if (!PF2E) return;
  for (const key of ["classTraits", "featTraits", "actionTraits"]) {
    if (PF2E[key]) PF2E[key].sovereign = "Sovereign";
  }
  if (PF2E.traitsDescriptions) {
    PF2E.traitsDescriptions.sovereign = "Abilities with this trait come from the sovereign class.";
  }
});
