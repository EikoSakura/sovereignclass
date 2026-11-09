import { compilePack } from "@foundryvtt/foundryvtt-cli";
import fs from "node:fs";
import path from "node:path";
const mod = process.argv[2];
for (const pack of fs.readdirSync(path.join(mod, "src", "packs"))) {
  const dest = path.join(mod, "packs", pack);
  fs.rmSync(dest, { recursive: true, force: true });
  await compilePack(path.join(mod, "src", "packs", pack), dest, { log: false, recursive: false });
  console.log("compiled", pack);
}
