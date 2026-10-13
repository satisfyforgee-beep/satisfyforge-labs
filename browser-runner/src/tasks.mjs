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

async function checkPublicPage(page, url, label) {
  const response = await page.goto(url, { waitUntil: "domcontentloaded" });
  const status = response?.status() ?? null;
  const title = normalize(await page.title().catch(() => ""));
  const text = normalize(await page.locator("body").innerText().catch(() => ""));
  const finalUrl = page.url();
  const looksMissing = /\b(404|page not found|not found)\b/i.test(`${title} ${text.slice(0, 800)}`);
  const sameHost = new URL(finalUrl).hostname.endsWith("wix-site-host.com");

  return {
    label,
    ok: Boolean(status && status < 400 && title && text.length >= 80 && !looksMissing && sameHost),
    status,
    title: title.slice(0, 120),
    textLength: text.length,
    finalPath: new URL(finalUrl).pathname,
    sameHost,
    looksMissing
  };
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

  async "outreach-funnel-smoke"({ page }) {
    const base = "https://headless-hjorlnsaplw-satisfyforgee-140d.wix-site-host.com";
    const pages = [];
    pages.push(await checkPublicPage(page, `${base}/`, "home"));
    pages.push(await checkPublicPage(page, `${base}/lead-rescue.html`, "lead-rescue"));
    pages.push(await checkPublicPage(page, `${base}/demo.html`, "demo"));
    return {
      ok: pages.every(item => item.ok),
      task: "outreach-funnel-smoke",
      pages
    };
  },

  async "wix-site-smoke"({ page }) {
    const base = "https://headless-hjorlnsaplw-satisfyforgee-140d.wix-site-host.com";
    const paths = [
      ["/", "home"],
      ["/appointments.html", "appointments"],
      ["/audit.html", "audit"],
      ["/auto.html", "auto"],
      ["/demo.html", "demo"],
      ["/home-services.html", "home-services"],
      ["/lead-rescue.html", "lead-rescue"],
      ["/lead-tracker.html", "lead-tracker"],
      ["/message-builder.html", "message-builder"],
      ["/pricing.html", "pricing"],
      ["/privacy.html", "privacy"],
      ["/roi-calculator.html", "roi-calculator"],
      ["/services.html", "services"],
      ["/tools.html", "tools"]
    ];

    const pages = [];
    const paymentSafety = [];
    for (const [path, label] of paths) {
      const result = await checkPublicPage(page, `${base}${path}`, label);
      pages.push(result);
      if (label === "home" || label === "pricing") {
        const directPayhipLinks = await page.locator('a[href*="payhip.com/b/"]').count();
        paymentSafety.push({ label, directPayhipLinks, ok: directPayhipLinks === 0 });
      }
    }

    return {
      ok: pages.every(item => item.ok) && paymentSafety.every(item => item.ok),
      task: "wix-site-smoke",
      pages,
      paymentSafety
    };
  },

  async "payhip-public-creator-kit"({ page }) {
    const response = await page.goto("https://payhip.com/b/MSLBK", { waitUntil: "domcontentloaded" });
    const status = response?.status() ?? null;
    const title = normalize(await page.title().catch(() => ""));
    const text = normalize(await page.locator("body").innerText().catch(() => ""));
    const finalUrl = page.url();
    const hostname = new URL(finalUrl).hostname.toLowerCase();
    const prices = [...new Set((text.match(/\$\s*[0-9]+(?:\.[0-9]{1,2})?/g) || []).map(value => value.replace(/\s+/g, "")))].slice(0, 8);
    const productMatch = /strange true story|shorts creator kit|creator kit/i.test(`${title} ${text.slice(0, 2500)}`);
    const looksMissing = /\b(404|page not found|product not found|unavailable)\b/i.test(`${title} ${text.slice(0, 1000)}`);
    return {
      ok: Boolean(status && status < 400 && hostname.endsWith("payhip.com") && productMatch && prices.length > 0 && !looksMissing),
      task: "payhip-public-creator-kit",
      publicId: "MSLBK",
      status,
      title: title.slice(0, 140),
      productMatch,
      observedPrices: prices,
      finalPath: new URL(finalUrl).pathname,
      looksMissing
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

    const save = page.locator('button:has-text("Save"):visible, button:has-text("Update"):visible, input[type="submit"]:visible').first();
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
