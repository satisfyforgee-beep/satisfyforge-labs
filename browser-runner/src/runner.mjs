import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";
import { chromium } from "playwright";
import { mutationTasks, tasks } from "./tasks.mjs";
import { localTasks } from "./local-tasks.mjs";

const allTasks = { ...tasks, ...localTasks };
const taskName = process.env.SF_TASK || "smoke";
const allowMutations = String(process.env.SF_ALLOW_MUTATIONS || "false").toLowerCase() === "true";
const mutationsArmed = String(process.env.SF_MUTATIONS_ARMED || "false").toLowerCase() === "true";
const taskIsMutation = mutationTasks.has(taskName);
const stateGzipB64 = process.env.SF_BROWSER_STATE_GZIP_B64 || "";
const resultPath = process.env.SF_RESULT_PATH || "result.json";

function emit(result, stream = "log") {
  const safe = JSON.stringify(result);
  fs.writeFileSync(resultPath, `${safe}\n`, { mode: 0o600 });
  console[stream](safe);
}

if (!allTasks[taskName]) {
  emit({ ok: false, task: taskName, code: "UNKNOWN_TASK" }, "error");
  process.exit(2);
}

if (taskIsMutation && !allowMutations) {
  emit({ ok: false, task: taskName, code: "MUTATION_NOT_ALLOWED", mutationMode: false, mutationsArmed }, "error");
  process.exit(4);
}

if (taskIsMutation && !mutationsArmed) {
  emit({ ok: false, task: taskName, code: "MUTATIONS_NOT_ARMED", mutationMode: true, mutationsArmed: false }, "error");
  process.exit(5);
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
    emit({ ok: false, task: taskName, code: "INVALID_AUTH_STATE" }, "error");
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

  const result = await allTasks[taskName]({
    page,
    browserContext,
    allowMutations,
    context: { authLoaded }
  });

  const safeResult = {
    ...result,
    task: taskName,
    mutationMode: allowMutations,
    mutationsArmed,
    authLoaded
  };
  emit(safeResult);
  process.exitCode = result?.ok === false ? 1 : 0;
} catch (error) {
  emit({
    ok: false,
    task: taskName,
    code: error.code || "TASK_FAILED",
    message: error.code || error.message || "Task failed",
    mutationMode: allowMutations,
    mutationsArmed,
    authLoaded
  }, "error");
  process.exitCode = 1;
} finally {
  if (storageStatePath) {
    try { fs.rmSync(storageStatePath, { force: true }); } catch {}
  }
  await browser.close();
}
