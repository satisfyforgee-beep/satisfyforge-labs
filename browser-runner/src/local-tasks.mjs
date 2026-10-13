import fs from "node:fs/promises";

export const localTasks = {
  async "forge-frenzy-smoke"({ page }) {
    const html = await fs.readFile("archive/forge-frenzy-v2.1/games/forge-frenzy-v2.html", "utf8");
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(String(error?.message || error)));

    await page.setContent(html, { waitUntil: "load" });
    await page.waitForSelector("#startBtn");

    const initial = await page.evaluate(() => ({
      title: document.title,
      timer: document.querySelector("#timer")?.textContent,
      tutorialHidden: document.querySelector("#tutorial")?.classList.contains("hide") || false,
      startText: document.querySelector("#startBtn")?.textContent
    }));

    await page.locator("#startBtn").click();
    await page.waitForTimeout(1600);

    const afterStart = await page.evaluate(() => ({
      timer: Number(document.querySelector("#timer")?.textContent || 60),
      tutorialHidden: document.querySelector("#tutorial")?.classList.contains("hide") || false,
      summaryHidden: document.querySelector("#summary")?.classList.contains("hide") || false,
      coins: Number(document.querySelector("#coins")?.textContent || 0),
      canvasWidth: document.querySelector("#c")?.width || 0,
      canvasHeight: document.querySelector("#c")?.height || 0
    }));

    const ok = initial.title === "SatisfyForge — Forge Frenzy v2.1"
      && initial.timer === "60"
      && initial.startText?.includes("START 60-SECOND RUN")
      && !initial.tutorialHidden
      && afterStart.timer < 60
      && afterStart.timer > 0
      && afterStart.tutorialHidden
      && afterStart.summaryHidden
      && afterStart.canvasWidth > 0
      && afterStart.canvasHeight > 0
      && pageErrors.length === 0;

    return {
      ok,
      task: "forge-frenzy-smoke",
      initial,
      afterStart,
      pageErrors
    };
  }
};
