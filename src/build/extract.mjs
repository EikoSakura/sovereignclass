import { extractPack } from "@foundryvtt/foundryvtt-cli";
const [src, dest] = process.argv.slice(2);
await extractPack(src, dest, { log: false });
