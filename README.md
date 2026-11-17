# Sovereign Class (PF2e Homebrew)

A Pathfinder Second Edition homebrew class for Foundry VTT: a ruler who bears regalia, draws power from their court, and leads a loyal follower.

## Installation

In Foundry, go to **Add-on Modules → Install Module** and paste this manifest URL:

```
https://github.com/EikoSakura/sovereignclass/releases/latest/download/module.json
```

## Requirements

- Foundry VTT v13 or v14
- Pathfinder Second Edition system (built against 8.6.1)
- [PF2e Companion Compendia](https://foundryvtt.com/packages/pf2e-animal-companions) for followers

## Contents

| Compendium | What's in it |
| --- | --- |
| Sovereign Classes | The Sovereign class (Charisma, 8 HP) |
| Sovereign Class Features | Core features, six regalia, the Court of Hero's Heart, court milestones |
| Sovereign Feats | 42 class feats, levels 1 to 20 |
| Sovereign Actions | Sovereign's Grace, Scepter's Command, Final Stand, Accept the Gambit, Hero's Heart Guard |
| Sovereign Effects | Effects to drag onto tokens from feat descriptions |
| Sovereign Extras | Automated rules the pf2e system doesn't ship yet: Stellar Dancer Dedication, Stellar Dance Stance, and its stance and zenith effects |

| Summons Unleashed: Convoker & Eidolons | The Convoker class archetype (Convoker Assembly, 7 archetype feats, the *convoke*, *assembled assault* and *combination convocation* focus spells), the summoner's side of 8 new eidolons, and their effects |
| Summons Unleashed: Eidolon Ancestries | The eidolon actor's side of the 8 new eidolons (Coatl, Kami, Mycological, Program, Rakshasa, Saboteur, Sphinx, Time): an ancestry, Strength and Dexterity key-attribute builds, and initial, symbiosis and transcendence abilities |

| Martial Memoires: Soaring Blade | The Soaring Blade archetype: dedication, Bladework Stance (with its effect), 15 archetype feats, and the Rending Recall and Punitive Strike actions |

The module also adds **Chain Blade** to the Base Weapon list on weapon sheets.

## Soaring Blade

Take **Soaring Blade Dedication**, then mark your Favored Blade with the feather toggle on its inventory row. Entering **Bladework Stance** counts the blades flying above you (its badge, set from the Favored Blade's damage dice) and gives the Favored Blade thrown 15 ft. (or +10 feet of range increment if it could already be thrown).

The count looks after itself: thrown copies leave (or stick in the target with Impaling Strikes), Blade Surfing and Battlefield Control take one, Raining Assault drops them all on the target, and **Command Blades** recalls or sends them out. Slashing Recall, Blade Spin, Sharp Steps and Rending Recall post their damage (rolled from your Favored Blade, or the bleed per stuck blade) with the save against your soaring blade DC. Raining Assault, Downpour of Steel and True Blade's Strike switch their splash or extra dice on for you, and the last two end the stance.

## Summons Unleashed eidolons

The new eidolons work like the system's own: a summoner picks one (for example **Coatl Eidolon**) from the Eidolon class feature's list. The eidolon actor takes the matching ancestry from **Summons Unleashed: Eidolon Ancestries**, which grants the Companion Compendia **Eidolon** class and the eidolon's abilities at 1st, 7th and 17th level.

A **Convoker** picks **Convoker Assembly** as their eidolon. It sets the tradition, its skill, the key attribute (Charisma or Intelligence), and records the three assembly eidolons. Spellcasting switches to prepared, and focus spells are added as you take the feats that grant them.

Each eidolon is its own actor. The **Assembly** window (button in the sheet header) shows one card per slot:

- **Create** an eidolon from a slot (right ancestry, your level, linked back to you), or drop an existing eidolon actor onto it. Click a portrait or the token picture to change art.
- **Manifest** places the primary next to you; **Set primary** swaps for free at daily preparations or Refocus.
- **Convoke** swaps tokens on the scene, moves conditions and effects over, applies the 1-round frequency lockout, and lets you click a square for Warping Convoke.
- **Assembled Assault** places the secondary within 60 feet (copying Boost Eidolon) until you click Return or your turn ends.
- **Fuse** (Combination Convocation) copies the chosen evolution feat, initial ability or unarmed attack onto the primary, and can grow it a size or post the fusion blast. Everything is removed when the effect ends.
- Casting those spells from the sheet, or using Manifest Eidolon, runs the same steps.
- **Export / Import** (or the sidebar's Export Data / Import Data on the summoner) saves and restores the summoner with every eidolon, their links, and any custom images in one JSON file.

Turn on pf2e-toolbelt's **Shared Data** setting so the eidolons share the summoner's Hit Points. Players without permission to create tokens or actors are covered by a logged-in GM.

## Followers

A follower is a character actor with the **Follower** ancestry and a follower type (Adept, Berserker, Medic, Scout, Sharpshooter, Shieldbearer) from Companion Compendia. Add the Experienced, Veteran, and Exceptional Advancement items at 4th, 8th, and 14th level. With the Court of Hero's Heart, give the follower **Hero's Heart Guard** at 4th level: a 5-foot aura that grants adjacent allies lesser cover.

## Building

Compendium sources live in `src/packs` as JSON and are generated by the Python scripts in `src/build`.

```bash
cd src/build
python build.py
node compile.mjs ../..
```

`build.py` validates every compendium link and icon path, then rewrites `src/packs`. `compile.mjs` needs `@foundryvtt/foundryvtt-cli` (`npm install`) and writes the LevelDB packs into `packs/`, which are committed so the repo is a complete module. Close the world (return to Setup) before compiling, since Foundry locks open packs.

## Still to come

The Courts of Infernal Power, Shimmering Wealth, Whispering Fey, and Magical Mastery.
