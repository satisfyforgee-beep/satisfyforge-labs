import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";
import { chromium } from "playwright";
import { tasks } from "./tasks.mjs";

const taskName = process.env.SF_TASK || "smoke";
const allowMutations = String(process.env.SF_ALLOW_MUTATIONS || "false").toLowerCase() === "true";
const stateGzipB64 = process.env.SF_BROWSER_STATE_GZIP_B64 || "";

if (!tasks[taskName]) {
  console.error(JSON.stringify({ ok: false, task: taskName, code: "UNKNOWN_TASK" }));
  process.exit(2);
}

let storageStatePath;
let authLoaded = false;
if (stateGzipB64) {
  try {
    const compressed = Buffer.from(stateGzipB64, "base64");
    const decoded = zlib.gunzipSync(compressed).toString("utf8");
    JSON.parse(decoded);
    storageStatePath = path.join(os.tmpdir(), "sf-browser-state.json");
    fs.writeFileSync(storageStatePath, decoded, { mode: 0o600 });
    authLoaded = true;
  } catch {
    console.error(JSON.stringify({ ok: false, task: taskName, code: "INVALID_AUTH_STATE" }));
    process.exit(3);
  }
}

const browser = await chromium.launch({
  headless: true,
  args: ["--disable-dev-shm-usage"]
});

try {
  const browserContext = await browser.newContext({
    storageState: storageStatePath || undefined,
    viewport: { width: 1440, height: 1100 }
  });
  const page = await browserContext.newPage();
  page.setDefaultTimeout(15000);

  const result = await tasks[taskName]({
    page,
    browserContext,
    allowMutations,
    context: { authLoaded }
  });

  const safeResult = {
    ...result,
    task: taskName,
    mutationMode: allowMutations,
    authLoaded
  };
  console.log(JSON.stringify(safeResult));
  process.exitCode = result?.ok === false ? 1 : 0;
} catch (error) {
  console.error(JSON.stringify({
    ok: false,
    task: taskName,
    code: error.code || "TASK_FAILED",
    message: error.code || error.message || "Task failed"
  }));
  process.exitCode = 1;
} finally {
  if (storageStatePath) {
    try { fs.rmSync(storageStatePath, { force: true }); } catch {}
  }
  await browser.close();
}
