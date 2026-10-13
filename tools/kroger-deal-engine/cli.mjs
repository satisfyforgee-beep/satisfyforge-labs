#!/usr/bin/env node
import { createClientFromEnv } from "./kroger.mjs";

function parse(argv) {
  const [command, ...rest] = argv;
  const opts = { _: [] };
  for (let i = 0; i < rest.length; i++) {
    const arg = rest[i];
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const next = rest[i + 1];
      if (next && !next.startsWith("--")) {
        if (opts[key] === undefined) opts[key] = next;
        else opts[key] = Array.isArray(opts[key]) ? [...opts[key], next] : [opts[key], next];
        i++;
      } else opts[key] = true;
    } else opts._.push(arg);
  }
  return { command, opts };
}

function print(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

function itemsFrom(opts) {
  const raw = opts.item === undefined ? [] : Array.isArray(opts.item) ? opts.item : [opts.item];
  return raw.map(entry => {
    const m = String(entry).match(/^(.*?)(?:\*(\d+))?$/);
    return { term: m?.[1]?.trim(), quantity: Number(m?.[2] || 1) };
  }).filter(x => x.term);
}

const { command, opts } = parse(process.argv.slice(2));
if (!command || ["help", "--help", "-h"].includes(command)) {
  console.log(`SatisfyForge Kroger Deal Engine\n\nCommands:\n  locations --zip 45044 [--limit 10]\n  search --location LOCATION_ID --term "milk" [--limit 10]\n  basket --location LOCATION_ID --item "milk*2" --item "eggs"\n\nEnvironment:\n  KROGER_CLIENT_ID\n  KROGER_CLIENT_SECRET\n  KROGER_SCOPE (optional; default product.compact)\n\nThis tool compares public Kroger product/store pricing. It does NOT clip digital coupons.`);
  process.exit(0);
}

try {
  const client = createClientFromEnv();
  if (command === "locations") {
    print(await client.locationsNearZip(opts.zip, opts.limit));
  } else if (command === "search") {
    print(await client.searchProducts({ term: opts.term, locationId: opts.location, limit: opts.limit }));
  } else if (command === "basket") {
    print(await client.compareBasket({ locationId: opts.location, items: itemsFrom(opts) }));
  } else {
    throw new Error(`UNKNOWN_COMMAND_${command}`);
  }
} catch (error) {
  console.error(JSON.stringify({ ok: false, error: error.message }));
  process.exit(1);
}
