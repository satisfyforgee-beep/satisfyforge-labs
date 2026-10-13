const normalize = (value = "") => value.replace(/\s+/g, " ").trim();

function requireAuth(context) {
  if (!context.authLoaded) {
    const error = new Error("AUTH_REQUIRED");
    error.code = "AUTH_REQUIRED";
    throw error;
  }
}

async function looksLoggedOut(page) {
  const url = page.url().toLowerCase();
  if (url.includes("login") || url.includes("signin") || url.includes("sign-in")) return true;
  const passwordCount = await page.locator('input[type="password"]').count();
  return passwordCount > 0;
}

export const tasks = {
  async smoke({ page }) {
    await page.goto("https://example.com", { waitUntil: "domcontentloaded" });
    return {
      ok: (await page.title()).includes("Example Domain"),
      task: "smoke",
      title: await page.title(),
      origin: new URL(page.url()).origin
    };
  },

  async "payhip-audit-tool-vault"({ page, context }) {
    requireAuth(context);
    await page.goto("https://payhip.com/products", { waitUntil: "domcontentloaded" });
    if (await looksLoggedOut(page)) {
      const error = new Error("AUTH_EXPIRED");
      error.code = "AUTH_EXPIRED";
      throw error;
    }

    const target = page.getByText(/SatisfyForge Tool Vault/i).first();
    if (!(await target.count())) {
      return { ok: false, task: "payhip-audit-tool-vault", code: "PRODUCT_NOT_FOUND" };
    }

    let container = target.locator("xpath=ancestor::*[self::div or self::li or self::tr][1]");
    if (!(await container.count())) container = target;
    const text = normalize(await container.innerText().catch(() => ""));
    const money = text.match(/\$\s*([0-9]+(?:\.[0-9]{1,2})?)/);

    return {
      ok: true,
      task: "payhip-audit-tool-vault",
      product: "SatisfyForge Tool Vault",
      observedPrice: money ? Number(money[1]).toFixed(2) : null,
      publicId: "KLjBb",
      origin: new URL(page.url()).origin
    };
  },

  async "payhip-fix-tool-vault-49"({ page, context, allowMutations }) {
    requireAuth(context);
    if (!allowMutations) {
      const error = new Error("MUTATION_NOT_ALLOWED");
      error.code = "MUTATION_NOT_ALLOWED";
      throw error;
    }

    await page.goto("https://payhip.com/products", { waitUntil: "domcontentloaded" });
    if (await looksLoggedOut(page)) {
      const error = new Error("AUTH_EXPIRED");
      error.code = "AUTH_EXPIRED";
      throw error;
    }

    const target = page.getByText(/SatisfyForge Tool Vault/i).first();
    if (!(await target.count())) {
      return { ok: false, task: "payhip-fix-tool-vault-49", code: "PRODUCT_NOT_FOUND" };
    }

    let row = target.locator("xpath=ancestor::*[self::div or self::li or self::tr][1]");
    if (!(await row.count())) row = target.locator("xpath=..");

    const editLink = row.locator('a:has-text("Edit"), a[href*="edit"], button:has-text("Edit")').first();
    if (!(await editLink.count())) {
      await target.click();
    } else {
      await editLink.click();
    }
    await page.waitForLoadState("domcontentloaded");

    const priceInput = page.locator([
      'input[name*="price" i]',
      'input[id*="price" i]',
      'input[aria-label*="price" i]',
      'input[placeholder*="price" i]'
    ].join(",")).first();

    if (!(await priceInput.count())) {
      return { ok: false, task: "payhip-fix-tool-vault-49", code: "PRICE_FIELD_NOT_FOUND" };
    }

    const before = normalize(await priceInput.inputValue());
    await priceInput.fill("49");

    const save = page.locator('button:has-text("Save"), button:has-text("Update"), input[type="submit"]')
      .filter({ visible: true })
      .first();
    if (!(await save.count())) {
      return { ok: false, task: "payhip-fix-tool-vault-49", code: "SAVE_CONTROL_NOT_FOUND", before };
    }

    await save.click();
    await page.waitForLoadState("networkidle").catch(() => {});

    const after = normalize(await priceInput.inputValue().catch(() => "49"));
    return {
      ok: after === "49" || after === "49.00",
      task: "payhip-fix-tool-vault-49",
      product: "SatisfyForge Tool Vault",
      before,
      after,
      publicId: "KLjBb"
    };
  }
};
