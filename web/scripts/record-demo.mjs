import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFile, mkdir, mkdtemp, rm, stat } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const base = process.env.SMOKE_BASE_URL || "http://127.0.0.1:3000";
const data = fileURLToPath(new URL("../../data/", import.meta.url));
const docs = fileURLToPath(new URL("../../docs/", import.meta.url));
const ffmpeg = process.env.FFMPEG || "ffmpeg";
await mkdir(data, { recursive: true });
const directory = await mkdtemp(join(data, "demo-"));
const browser = await chromium.launch({ headless: true });
const viewport = { width: 1440, height: 900 };
const context = await browser.newContext({
  viewport,
  recordVideo: { dir: directory, size: viewport },
});
const started = performance.now();
const elapsed = () => (performance.now() - started) / 1000;
const waits = [];
const page = await context.newPage();
const video = page.video();
const dwell = (seconds) => page.waitForTimeout(seconds * 1000);
const heading = (name) => page.getByRole("heading", { name, exact: true });

async function scrollTo(locator, block = "center") {
  await locator.evaluate(async (element, block) => {
    element.scrollIntoView({ behavior: "smooth", block });
    await new Promise((resolve) => setTimeout(resolve, 750));
  }, block);
}

async function ask(label) {
  await page.getByRole("button", { name: label }).click();
  await dwell(3);
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/api/backend/ask") && r.request().method() === "POST",
    { timeout: 240000 },
  );
  await page.getByRole("button", { name: "Find evidence" }).click();
  const start = elapsed();
  const http = await response;
  const end = elapsed();
  if (end - start > 4) waits.push([start + 0.5, end - 0.5]);
  assert.equal(http.status(), 200);
  const body = await http.json();
  await page.getByTestId("answer-status").waitFor();
  return body;
}

let delivered = false;
try {
  try {
    await page.goto(base);
    await page.locator(".health-pill", { hasText: "Corpus ready" }).waitFor({
      timeout: 60000,
    });
    const head = Math.max(0, elapsed() - 0.5);
    await dwell(4);
    const trace = page.getByRole("button", { name: /Behind the answer/ });
    if ((await trace.getAttribute("aria-expanded")) === "true") {
      await trace.click();
    }
    const mechanism = await ask("Unreliable airspeed");
    assert.ok(["answered", "partial"].includes(mechanism.status));
    assert.ok(mechanism.citations.length > 0);
    await scrollTo(heading("What the accounts support"));
    await dwell(8);
    await trace.click();
    await scrollTo(page.getByTestId("trace-timeline"), "start");
    await dwell(9);
    console.log("Recorded mechanism answer and trace");

    const citation = page.getByRole("link", { name: /Open ASRS report/ }).first();
    await scrollTo(citation);
    await dwell(2);
    await citation.click();
    const synopsis = page.getByText("SYNOPSIS", { exact: true });
    const narrative = page.getByText("REPORTER NARRATIVE", { exact: true });
    await synopsis.waitFor();
    await narrative.waitFor();
    await scrollTo(synopsis);
    await dwell(5);
    await scrollTo(narrative, "start");
    await dwell(7);
    await page.getByRole("link", { name: /Back to Ask/ }).click();
    console.log("Recorded cited report");

    const count = await ask("Count reports");
    assert.equal(count.status, "answered");
    assert.equal(count.aggregate.count, 98);
    assert.equal(count.aggregate.denominator, 20000);
    assert.deepEqual(count.aggregate.filters, {
      year_start: 2020,
      year_end: 2020,
      anomaly_category: "Ground Incursion Runway",
    });
    const aggregate = page.getByTestId("aggregate");
    await scrollTo(aggregate);
    await dwell(5);
    await aggregate.getByText("View count provenance", { exact: true }).click();
    await scrollTo(aggregate);
    await dwell(7);
    console.log("Recorded count and SQL provenance");

    await page.getByRole("link", { name: /Evaluation lab/ }).click();
    await dwell(3);
    for (const title of [
      "Retrieval before the production default",
      "More stages did not solve answerability",
      "Answer what the evidence supports",
      "One run. The failure stays visible.",
      "Source trail",
    ]) {
      await scrollTo(heading(title), "start");
      await dwell(5);
    }
    const tail = elapsed();
    await context.close();
    const raw = await video.path();
    const available = spawnSync(ffmpeg, ["-version"], { windowsHide: true });
    if (available.error?.code === "ENOENT") {
      const output = join(docs, "demo.webm");
      await copyFile(raw, output);
      console.log(`ffmpeg unavailable. Raw demo: ${output} (${(await stat(output)).size} bytes)`);
    } else {
      assert.equal(available.status, 0, "ffmpeg version check failed");
      const segments = [];
      let cursor = head;
      for (const [start, end] of waits) {
        segments.push([cursor, start, 1], [start, end, (end - start) / 2]);
        cursor = end;
      }
      segments.push([cursor, tail, 1]);
      const filters = segments.map(
        ([start, end, speed], i) =>
          `[0:v]trim=start=${start}:end=${end},setpts=(PTS-STARTPTS)/${speed}[v${i}]`,
      );
      filters.push(
        segments.map((_, i) => `[v${i}]`).join("") +
          `concat=n=${segments.length}:v=1:a=0,fps=25[out]`,
      );
      const encoded = join(directory, "demo.mp4");
      const result = spawnSync(ffmpeg, [
        "-hide_banner", "-loglevel", "error", "-i", raw,
        "-filter_complex", filters.join(";"), "-map", "[out]",
        "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", encoded,
      ], { stdio: "inherit", windowsHide: true });
      assert.equal(result.status, 0, "ffmpeg encoding failed");
      const { size } = await stat(encoded);
      const duration = segments.reduce((sum, [start, end, speed]) =>
        sum + (end - start) / speed, 0);
      assert.ok(duration >= 60 && duration <= 150, `Duration: ${duration}s`);
      assert.ok(size <= 25_000_000, `Encoded size: ${size} bytes`);
      await copyFile(encoded, join(docs, "demo.mp4"));
      console.log(`docs/demo.mp4: ${duration.toFixed(1)} seconds, ${size} bytes`);
    }
    delivered = true;
  } finally {
    await context.close();
    await browser.close();
  }
} finally {
  if (delivered) {
    await rm(directory, { recursive: true, force: true, maxRetries: 5 });
  }
}
