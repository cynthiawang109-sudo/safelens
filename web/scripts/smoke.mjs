import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
const base = process.env.SMOKE_BASE_URL || "http://127.0.0.1:3000";
const docs = new URL("../../docs/", import.meta.url);
await mkdir(docs, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1440, height: 1100 },
  deviceScaleFactor: 1,
});
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const results = { base, requests: [], checks: [], screenshots: [] };
async function shot(name) {
  await page.screenshot({
    path: new URL(name, docs).pathname.replace(/^\/([A-Za-z]:)/, "$1"),
    fullPage: true,
  });
  results.screenshots.push(`docs/${name}`);
}
try {
  for (const [label, kind] of [
    ["Unreliable airspeed", "mechanism"],
    ["Count reports", "count"],
  ]) {
    await page.goto(base);
    await page
      .locator(".health-pill")
      .filter({ hasText: "Corpus ready" })
      .waitFor();
    await page.getByRole("button", { name: label }).click();
    const response = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/backend/ask") && r.request().method() === "POST",
      { timeout: 240000 },
    );
    await page.getByRole("button", { name: "Find evidence" }).click();
    await page.getByRole("status").waitFor();
    if (kind === "mechanism") await shot("STEP8_LOADING.png");
    const http = await response;
    assert.equal(http.status(), 200);
    const body = await http.json();
    await page.getByTestId("answer-status").waitFor();
    assert.equal(
      (await page.getByTestId("answer-status").innerText())
        .trim()
        .toLowerCase(),
      body.status.replaceAll("_", " "),
    );
    await page.getByTestId("trace-timeline").waitFor();
    assert.equal(
      await page.locator(".timeline-item").count(),
      body.trace.length,
    );
    for (const e of body.trace)
      if (typeof e.detail.query === "string")
        assert.ok(
          (await page.getByTestId("trace-timeline").innerText()).includes(
            e.detail.query,
          ),
        );
    results.requests.push({
      kind,
      httpStatus: http.status(),
      renderedStatus: body.status,
      stages: body.trace.map((e) => e.stage),
      usage: body.usage,
      aggregate: body.aggregate
        ? {
            count: body.aggregate.count,
            denominator: body.aggregate.denominator,
            filters: body.aggregate.filters,
          }
        : null,
    });
    await shot(
      kind === "count" ? "STEP8_COUNT_TRACE.png" : "STEP8_ASK_TRACE.png",
    );
    if (kind === "count") {
      assert.equal(body.status, "answered");
      assert.equal(body.aggregate.denominator, 20000);
      assert.ok(
        (await page.getByTestId("aggregate").innerText()).includes(
          body.aggregate.count.toLocaleString("en-US"),
        ),
      );
    } else {
      assert.ok(["answered", "partial"].includes(body.status));
      assert.ok(body.citations.length > 0);
      await page.setViewportSize({ width: 390, height: 844 });
      await shot("STEP8_ASK_MOBILE.png");
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      );
      await page.setViewportSize({ width: 1440, height: 1100 });
      const acn = body.citations[0].acn;
      await page.locator(`a[href="/report/${acn}"]`).first().click();
      await page.getByText("REPORTER NARRATIVE", { exact: true }).waitFor();
      assert.ok(
        (await page.locator(".metadata-grid").innerText()).includes("SOURCE"),
      );
      await shot("STEP8_REPORT.png");
      results.checks.push(
        "Live citation navigates to indexed synopsis, narrative and metadata",
      );
    }
  }
  await page.goto(`${base}/results`);
  await page.getByText("One run. The failure stays visible.").waitFor();
  assert.ok(
    (await page.locator("main").innerText()).includes("No aggregate returned"),
  );
  await shot("STEP8_RESULTS.png");
  results.checks.push(
    "Results snapshot renders, including unchanged ft-cnt-1 failure",
  );
  await page.route("**/api/backend/health", (r) =>
    r.fulfill({ status: 503, json: { detail: "smoke unavailable" } }),
  );
  await page.goto(base);
  await page
    .locator(".health-pill")
    .filter({ hasText: "Service unavailable" })
    .waitFor();
  await page.route("**/api/backend/ask", (r) =>
    r.fulfill({ status: 503, json: { detail: "smoke unavailable" } }),
  );
  await page.getByRole("button", { name: "Hydraulic failure" }).click();
  await page.getByRole("button", { name: "Find evidence" }).click();
  await page.locator('.error-box[role="alert"]').waitFor();
  assert.ok((await page.locator("#question").inputValue()).length > 0);
  await page.route("**/api/backend/report/*", (r) =>
    r.fulfill({ status: 404, json: { detail: "not found" } }),
  );
  await page.goto(`${base}/report/123`);
  await page.getByRole("button", { name: "Retry report" }).waitFor();
  results.checks.push(
    "Health, Ask and report errors visible; question retained; manual report retry available",
  );
  assert.deepEqual(errors, []);
  results.checks.push(
    "No browser page errors; mobile Ask has no horizontal overflow",
  );
  results.passed = true;
} finally {
  await writeFile(
    new URL("STEP8_SMOKE.json", docs),
    JSON.stringify(results, null, 2) + "\n",
    "utf8",
  );
  await browser.close();
}
console.log(JSON.stringify(results, null, 2));
