/* Real browser regression checks against a disposable database and real WSGI API. */
const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");

const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "shellarena-e2e-"));
const python = fs.existsSync(".venv/bin/python")
  ? ".venv/bin/python"
  : "python";
const root = "http://127.0.0.1:8765";
const server = spawn(
  python,
  [
    "-m",
    "gunicorn",
    "--bind",
    "127.0.0.1:8765",
    "--workers",
    "2",
    "--threads",
    "2",
    "--no-control-socket",
    "backend.wsgi:app",
  ],
  {
    env: {
      ...process.env,
      APP_ENV: "development",
      SECRET_KEY: crypto.randomBytes(32).toString("hex"),
      DATABASE_PATH: path.join(temporary, "arena.db"),
      TRUSTED_HOSTS: "127.0.0.1,localhost",
    },
    stdio: ["ignore", "ignore", "pipe"],
  },
);
let serverLogs = "";
server.stderr.on("data", (text) => {
  serverLogs = (serverLogs + text).slice(-6000);
});
const failures = [],
  checks = [];
let browser;
async function check(name, fn) {
  await fn();
  checks.push(name);
  console.log(`PASS ${name}`);
}
async function runCommand(page, command) {
  await page.locator("#command-input").fill(command);
  await page.locator("#command-input").press("Enter");
  await page.waitForFunction(
    () => !document.querySelector("#command-input").disabled,
  );
}
(async () => {
  try {
    for (let i = 0; i < 80; i++) {
      try {
        if ((await fetch(root + "/health/ready")).ok) break;
      } catch {}
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    browser = await chromium.launch({
      headless: true,
      ...(process.env.CHROMIUM_EXECUTABLE
        ? {
            executablePath: process.env.CHROMIUM_EXECUTABLE,
            args: [
              "--no-sandbox",
              "--no-zygote",
              "--single-process",
              "--use-gl=angle",
              "--use-angle=swiftshader",
              "--enable-unsafe-swiftshader",
              "--in-process-gpu",
            ],
          }
        : {}),
    });
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1080 },
    });
    page.on("pageerror", (error) => failures.push(error.message));
    page.on("console", (message) => {
      if (
        message.type() === "error" &&
        /Content Security Policy|Refused to/.test(message.text())
      )
        failures.push(message.text());
    });
    fs.mkdirSync("test-results", { recursive: true });
    await check("Dashboard renders and does not overflow", async () => {
      await page.goto(root);
      await page
        .getByRole("heading", { name: "Ready when you are." })
        .waitFor();
      assert.equal(await page.locator(".stat").count(), 4);
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      await page.screenshot({
        path: "test-results/desktop-overview.png",
        fullPage: true,
      });
    });
    await check(
      "Search, category, difficulty, and bookmarks work",
      async () => {
        await page.goto(root + "/#/missions");
        await page.locator("#mission-search").waitFor();
        await page.locator("#mission-search").fill("container");
        assert.equal(await page.locator(".mission-card").count(), 3);
        await page
          .getByRole("button", {
            name: "Save Container reconnaissance",
            exact: true,
          })
          .click();
        await page.waitForSelector(
          '[data-action="bookmark"][aria-pressed="true"]',
        );
        await page.locator("#mission-search").fill("");
        await page.getByRole("button", { name: "Saved", exact: true }).click();
        assert.equal(await page.locator(".mission-card").count(), 1);
        await page.getByRole("button", { name: "Saved", exact: true }).click();
        await page
          .getByRole("button", { name: "Kubernetes", exact: true })
          .click();
        await page.locator("#difficulty").selectOption("Intermediate");
        assert.equal(await page.locator(".mission-card").count(), 1);
        assert.match(
          await page.locator(".mission-card h3").textContent(),
          /Map the cluster/,
        );
      },
    );
    await check("Terminal completes objectives and awards XP", async () => {
      await page.goto(root + "/#/arena/first-contact");
      await page.locator("#command-input").waitFor();
      for (const command of ["pwd", "whoami", "ls"])
        await runCommand(page, command);
      await page
        .getByRole("heading", { name: "Mission accomplished." })
        .waitFor();
      assert.equal(await page.locator(".objectives .done").count(), 3);
      await page.screenshot({
        path: "test-results/desktop-arena.png",
        fullPage: true,
      });
    });
    await check(
      "History survives a refresh and output is escaped",
      async () => {
        await page.reload();
        await page.locator("#command-input").waitFor();
        assert.equal(await page.locator(".terminal-entry").count(), 3);
        await runCommand(page, 'echo "<img src=x onerror=alert(1)>"');
        assert.equal(await page.locator("#terminal-output img").count(), 0);
        assert.match(
          await page.locator(".terminal-response").last().textContent(),
          /<img/,
        );
        await page.locator("#command-input").press("ArrowUp");
        assert.match(await page.locator("#command-input").inputValue(), /<img/);
      },
    );
    const username = "test_" + crypto.randomBytes(4).toString("hex");
    const password = crypto.randomBytes(18).toString("base64url");
    await check("Guest upgrades to an account without losing XP", async () => {
      await page
        .getByRole("button", { name: "Save progress", exact: true })
        .click();
      await page.locator("#auth-username").fill(username);
      await page.locator("#auth-password").fill(password);
      await page.locator("#auth-form button[type=submit]").click();
      await page.waitForFunction(() => !document.querySelector("#modal").open);
      await page.goto(root + "/#/profile");
      await page
        .getByRole("heading", { name: username, exact: true })
        .waitFor();
      assert.match(await page.locator(".stat").first().textContent(), /100/);
      assert.equal(await page.locator(".badge-card:not(.locked)").count(), 1);
    });
    await check(
      "Leaderboard is opt in and profile preferences persist",
      async () => {
        await page.goto(root + "/#/settings");
        await page.locator("#setting-public").check();
        await page.locator("#setting-compact").check();
        await page.getByRole("button", { name: "Save preferences" }).click();
        await page.waitForSelector(".layout.compact");
        await page.goto(root + "/#/leaderboard");
        await page.locator("tbody tr").waitFor();
        assert.match(
          await page.locator("tbody").textContent(),
          new RegExp(username),
        );
      },
    );
    await check(
      "Sign out and sign back in restores account progress",
      async () => {
        await page.goto(root + "/#/settings");
        await page
          .getByRole("button", { name: "Sign out", exact: true })
          .click();
        await page
          .getByRole("button", { name: "Sign in", exact: true })
          .waitFor();
        await page
          .getByRole("button", { name: "Sign in", exact: true })
          .click();
        await page.locator("#auth-username").fill(username);
        await page.locator("#auth-password").fill(password);
        await page.locator("#auth-form button[type=submit]").click();
        await page.waitForFunction(
          () => !document.querySelector("#modal").open,
        );
        await page.goto(root + "/#/profile");
        await page
          .getByRole("heading", { name: username, exact: true })
          .waitFor();
        assert.match(await page.locator(".stat").first().textContent(), /100/);
      },
    );
    await check("Hints and workspace reset work", async () => {
      await page.goto(root + "/#/arena/release-note");
      await page.locator("#command-input").waitFor();
      await page.locator("[data-action=hint]").click();
      await page.locator(".hint-box").waitFor();
      await runCommand(page, "echo release-ready > release.txt");
      await page
        .getByRole("button", { name: "Restart lab", exact: true })
        .click();
      await page.locator("[data-action=confirm-reset]").click();
      await page.waitForFunction(() => !document.querySelector("#modal").open);
      await page.locator("#command-input").waitFor();
      assert.equal(await page.locator(".terminal-entry").count(), 0);
    });
    await check("Mobile navigation and layout work at 390px", async () => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(root + "/#/dashboard");
      await page.locator(".hero").waitFor();
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      await page.waitForFunction(() => !document.querySelector(".toast"));
      await page.screenshot({
        path: "test-results/mobile-overview.png",
        fullPage: true,
      });
      await page.getByRole("button", { name: "Toggle navigation" }).click();
      await page.locator('.sidebar.open a[href="#/missions"]').click();
      await page.locator("#mission-search").waitFor();
      assert.equal(await page.locator(".sidebar.open").count(), 0);
      await page.goto(root + "/#/arena/first-contact");
      await page.locator("#command-input").waitFor();
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      await page.screenshot({
        path: "test-results/mobile-arena.png",
        fullPage: true,
      });
    });
    await check("No uncaught browser errors or CSP violations", async () => {
      assert.deepEqual(failures, []);
    });
    fs.writeFileSync(
      "test-results/browser-summary.json",
      JSON.stringify({ status: "passed", checks, failures }, null, 2),
    );
    console.log(`${checks.length} browser workflow checks passed.`);
  } catch (error) {
    console.error(error);
    console.error(serverLogs);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    server.kill("SIGTERM");
    await new Promise((resolve) => server.once("close", resolve));
    fs.rmSync(temporary, { recursive: true, force: true });
  }
})();
