import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

test("analyst can investigate a scored transaction and persist evidence", async ({
  page,
  request,
}) => {
  const snapshot = await (
    await request.get("http://127.0.0.1:8000/api/v1/overview")
  ).json();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/#overview");
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await expect(page.getByText("LIVE WORKSPACE SNAPSHOT")).toBeVisible();
  await expect(
    page.getByText(
      `${snapshot.scored.toLocaleString()} scored / ${snapshot.total.toLocaleString()} stored`,
    ),
  ).toBeVisible();
  await page.getByRole("link", { name: "Transactions", exact: true }).click();
  await page.getByLabel("Assessment filter").selectOption("true");
  const first = page.getByRole("button", { name: /TX-\d+/ }).first();
  await expect(first).toBeVisible();
  const txName = await first.innerText();
  await first.click();
  const dialog = page.getByRole("dialog", { name: "Transaction details" });
  await expect(dialog.getByText("Flagged", { exact: true })).toBeVisible();
  await dialog
    .getByRole("button", { name: "Compute SHAP explanation" })
    .click();
  await expect(
    dialog.getByText("Top contributions", { exact: false }),
  ).toBeVisible();
  const createdResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/cases") &&
      response.request().method() === "POST",
  );
  await dialog
    .getByRole("button", { name: "Create linked investigation" })
    .click();
  const caseId = (await (await createdResponse).json()).id;
  await expect(
    page.getByRole("heading", { name: "Investigations", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: `#${caseId} · Review ${txName}`, exact: true })
    .click();
  await page.getByLabel("Case status").selectOption("In Review");
  await page
    .getByLabel("Investigation note")
    .fill(
      "Synthetic evidence reviewed; anonymized features require analyst caution.",
    );
  await page.getByRole("button", { name: "Add note", exact: true }).click();
  await expect(
    page.getByText(
      "Synthetic evidence reviewed; anonymized features require analyst caution.",
      { exact: true },
    ),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Analyst decision", exact: true })
    .click();
  await page
    .getByLabel("Analyst decision")
    .fill("Continue review; model alert is not proof of fraud.");
  await page.getByRole("button", { name: "Save decision" }).click();
  await expect(page.getByRole("status")).toContainText("Investigation saved");
  await page.reload();
  await page
    .getByRole("button", { name: `#${caseId} · Review ${txName}`, exact: true })
    .click();
  await expect(page.getByLabel("Case status")).toHaveValue("In Review");
  await page
    .getByRole("button", { name: "Analyst decision", exact: true })
    .click();
  await expect(page.getByLabel("Analyst decision")).toHaveValue(
    "Continue review; model alert is not proof of fraud.",
  );
  const exported = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export report", exact: true })
    .click();
  const report = JSON.parse(
    await readFile((await (await exported).path())!, "utf8"),
  );
  expect(report.transactions[0].provenance).toBe("synthetic");
  expect(report.transactions[0].model_version).toBeTruthy();
  expect(errors).toEqual([]);
});

test("CSV import updates statistics and reports validation errors", async ({
  page,
  request,
}) => {
  const before = await (
    await request.get("http://127.0.0.1:8000/api/v1/overview")
  ).json();
  await page.goto("/#overview");
  await page.getByRole("button", { name: "Import dataset" }).click();
  const sample = (
    await readFile(
      resolve("../data/samples/synthetic-transactions.csv"),
      "utf8",
    )
  )
    .trim()
    .split("\n");
  const unique = [
    sample[0],
    ...sample.slice(1).map((line) => {
      const cells = line.split(",");
      cells[29] = String(Number(cells[29]) + before.total);
      return cells.join(",");
    }),
  ].join("\n");
  await page.getByLabel("CSV file").setInputFiles({
    name: "synthetic-e2e.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(unique),
  });
  await page
    .getByRole("button", { name: "Import transactions", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Imported 40 transactions",
  );
  const after = await (
    await request.get("http://127.0.0.1:8000/api/v1/overview")
  ).json();
  expect(after.total).toBe(before.total + 40);
  expect(after.scored).toBe(before.scored + 40);
  await page.getByRole("button", { name: "Import dataset" }).click();
  await page.getByLabel("CSV file").setInputFiles({
    name: "invalid.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("Amount,Class\n1,0"),
  });
  await page
    .getByRole("button", { name: "Import transactions", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "Missing columns",
  );
  await page.getByRole("button", { name: "Close import" }).click();
});

test("research, synthetic graph, and settings pages are usable", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/#laboratory");
  await expect(
    page.getByRole("heading", { name: "Model comparison", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Random Forest", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Random Forest · Precision-recall" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Fraud Detection", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Imported datasets", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Relationship demo", exact: true })
    .click();
  await expect(page.locator(".graph-canvas canvas").first()).toBeVisible();
  await page.getByLabel("Graph entity type").selectOption("Device");
  await page.getByRole("button", { name: "Fit", exact: true }).click();
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Environment", exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("overview is responsive and captures the actual workspace", async ({
  page,
}) => {
  await page.goto("/#overview");
  await expect(page.getByText("LIVE WORKSPACE SNAPSHOT")).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/overview.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../docs/screenshots/overview-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
});

test("workspace command navigation and display density persist", async ({
  page,
}) => {
  await page.goto("/#overview");
  await page.keyboard.press("ControlOrMeta+k");
  const search = page.getByRole("dialog", { name: "Workspace search" });
  await expect(search.getByLabel("Search workspace")).toBeFocused();
  await search.getByLabel("Search workspace").fill("performance");
  await search
    .getByRole("link", { name: "Model performance", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Model performance", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Display density").selectOption("comfortable");
  await page.reload();
  await expect(page.getByLabel("Display density")).toHaveValue("comfortable");
  await page.getByLabel("Display density").selectOption("compact");
});

test("advanced transaction queries persist and global search opens stored records", async ({
  page,
  request,
}) => {
  await page.goto("/#transactions");
  await page
    .getByText("Advanced filters & saved views", { exact: false })
    .click();
  await page.getByLabel("Minimum amount").fill("20");
  await page.getByLabel("Maximum amount").fill("150");
  const viewName = `Analyst range ${Date.now()}`;
  await page.getByLabel("Saved view name").fill(viewName);
  await page.getByRole("button", { name: "Save query configuration" }).click();
  await expect(page.getByLabel("Saved transaction views")).not.toHaveValue("");
  await page.reload();
  await page
    .getByText("Advanced filters & saved views", { exact: false })
    .click();
  await page
    .getByLabel("Saved transaction views")
    .selectOption({ label: viewName });
  await expect(page.getByLabel("Minimum amount")).toHaveValue("20");
  await expect(page.getByLabel("Maximum amount")).toHaveValue("150");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export filtered CSV" }).click();
  const csv = (await readFile((await (await download).path())!, "utf8"))
    .trim()
    .split("\n");
  const amountIndex = csv[0].split(",").indexOf("amount");
  expect(csv.length).toBeGreaterThan(1);
  expect(
    csv
      .slice(1)
      .every(
        (row) =>
          Number(row.split(",")[amountIndex]) >= 20 &&
          Number(row.split(",")[amountIndex]) <= 150,
      ),
  ).toBeTruthy();
  const tx = (
    await (
      await request.get("http://127.0.0.1:8000/api/v1/transactions?page_size=1")
    ).json()
  ).items[0];
  await page.keyboard.press("ControlOrMeta+k");
  const search = page.getByRole("dialog", { name: "Workspace search" });
  const label = `TX-${String(tx.id).padStart(6, "0")}`;
  await search.getByLabel("Search workspace").fill(label);
  await search
    .getByRole("button", { name: `Open Transaction ${label}`, exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Transaction details" }),
  ).toContainText(label);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Delete saved view" }).click();
  await expect(
    page.getByRole("option", { name: viewName, exact: true }),
  ).toHaveCount(0);
});

test("case workbench supports linked evidence, persisted resizing and audit timeline", async ({
  page,
  request,
}) => {
  const tx = (
    await (
      await request.get("http://127.0.0.1:8000/api/v1/transactions?page_size=1")
    ).json()
  ).items[0];
  const record = await (
    await request.post("http://127.0.0.1:8000/api/v1/cases", {
      data: {
        title: `Workbench evidence ${Date.now()}`,
        transaction_ids: [tx.id],
        entity_ids: ["device-1"],
      },
    })
  ).json();
  await page.goto(`/#investigations/${record.id}`);
  await expect(
    page.getByRole("heading", { name: "Linked evidence", exact: true }),
  ).toBeVisible();
  const splitter = page.getByRole("separator", {
    name: "Resize investigation queue",
  });
  const before = Number(await splitter.getAttribute("aria-valuenow"));
  await splitter.focus();
  await page.keyboard.press("ArrowRight");
  await expect(splitter).toHaveAttribute("aria-valuenow", String(before + 2));
  await page.getByLabel("Case status").selectOption("Escalated");
  await expect(page.locator(".timeline")).toContainText("Open → Escalated");
  await page.getByRole("button", { name: "device-1", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "Explore neighborhood" }),
  ).toHaveAttribute("href", "#graph/device-1");
  await page.reload();
  await expect(
    page.getByRole("separator", { name: "Resize investigation queue" }),
  ).toHaveAttribute("aria-valuenow", String(before + 2));
  await expect(page.getByLabel("Case status")).toHaveValue("Escalated");
  await page.screenshot({
    path: "../docs/screenshots/investigation-upgrade.png",
    fullPage: true,
    animations: "disabled",
  });
});

test("graph neighborhoods and synthetic entity investigations stay linked", async ({
  page,
}) => {
  await page.goto("/#graph/device-1");
  await expect(
    page.getByText("4 / 31 entities", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Expand neighborhood", exact: true })
    .click();
  await expect(
    page.getByText("7 / 31 entities", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Graph relationship type").selectOption("uses");
  await expect(
    page.getByText("4 / 31 entities", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Graph relationship type").selectOption("");
  await page.getByLabel("Shared-device cue").check();
  await expect(
    page.getByText("4 / 31 entities", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Inspect graph entity").selectOption("device-1");
  await page.screenshot({
    path: "../docs/screenshots/graph-upgrade.png",
    fullPage: true,
    animations: "disabled",
  });
  const created = page.waitForResponse(
    (r) => r.url().endsWith("/api/v1/cases") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Create entity investigation" })
    .click();
  const record = await (await created).json();
  expect(record.entity_ids).toEqual(["device-1"]);
  await expect(
    page.getByRole("heading", { name: "Linked evidence", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Explore neighborhood" }).click();
  await expect(
    page.getByRole("link", { name: `Case #${record.id}`, exact: true }),
  ).toBeVisible();
});

test("Overview risk exploration links to validated transaction filters", async ({
  page,
}) => {
  await page.goto("/#overview");
  await page.getByLabel("Risk band to explore").selectOption("8");
  await page
    .getByRole("button", { name: "Explore range", exact: true })
    .click();
  await expect(page.getByLabel("Minimum risk score")).toHaveValue("0.8");
  await expect(page.getByLabel("Maximum risk score")).toHaveValue("0.9");
  await page.keyboard.press("ControlOrMeta+k");
  const dialog = page.getByRole("dialog", { name: "Workspace search" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("link", { name: "Settings", exact: true }).focus();
  await page.keyboard.press("Tab");
  await expect(dialog.getByLabel("Search workspace")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
});

test("invalid ranges hide stale results and recover after correction", async ({
  page,
}) => {
  await page.goto("/#transactions");
  await page
    .getByText("Advanced filters & saved views", { exact: false })
    .click();
  await page.getByLabel("Minimum amount").fill("500");
  await page.getByLabel("Maximum amount").fill("1");
  await expect(page.getByRole("alert")).toContainText(
    "Invalid transaction query",
  );
  await expect(page.getByRole("button", { name: /TX-\d+/ })).toHaveCount(0);
  await page.getByLabel("Maximum amount").fill("1000");
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: /TX-\d+/ }).first(),
  ).toBeVisible();
});

test("direct prediction uses actual features, threshold overrides, and on-demand SHAP", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/#detection");
  await page.getByRole("button", { name: "Load stored example" }).click();
  await expect(page.getByLabel("Feature Amount")).not.toHaveValue("");
  await page.getByText("Decision settings", { exact: true }).click();
  await page.getByLabel("Decision threshold override").fill("0");
  const response = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/predict") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Predict transaction", exact: true })
    .click();
  const prediction = await (await response).json();
  expect(prediction.predicted_class).toBe(1);
  expect(prediction.decision_threshold).toBe(0);
  await expect(
    page.getByText("FRAUD CLASS PROBABILITY ESTIMATE", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Uncalibrated model estimate · not certainty of fraud"),
  ).toBeVisible();
  await page.getByText("Prediction metadata", { exact: true }).click();
  await expect(
    page
      .locator(".prediction-workspace")
      .getByText(prediction.model_version, { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Explain prediction with SHAP" })
    .click();
  await page
    .getByText("Explanation details and all features", { exact: true })
    .click();
  await expect(page.getByText(/SHAP output:/)).toBeVisible();
  await expect(
    page.getByText(
      /Contributions describe model behavior, not causal evidence/,
    ),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  expect(errors).toEqual([]);
});

test("laboratory explores validation costs while test metrics remain fixed", async ({
  page,
}) => {
  await page.goto("/#laboratory");
  const matrix = await page.locator(".confusion").innerText();
  await page
    .getByRole("button", { name: "Calibration & thresholds", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: /ROC curve$/ })).toBeVisible();
  const threshold = page.getByLabel("Validation threshold");
  await expect(threshold).toBeVisible();
  await threshold.selectOption({ index: 0 });
  await expect(
    page.getByText(
      /These illustrative costs are not measured financial losses/,
    ),
  ).toBeVisible();
  await expect(
    page.getByText("Test Brier score (lower is better)"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Test results", exact: true }).click();
  expect(await page.locator(".confusion").innerText()).toBe(matrix);
});

test("mobile navigation is labeled, dismissible, and closes after route changes", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#overview");
  const menu = page.getByRole("button", { name: "Open navigation" });
  await expect(menu).toHaveAttribute("aria-expanded", "false");
  await menu.click();
  const navigation = page.getByRole("dialog", { name: "Workspace navigation" });
  await expect(navigation).toBeVisible();
  await navigation
    .getByRole("link", { name: "Transactions", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Transactions", exact: true }),
  ).toBeVisible();
  await expect(menu).toHaveAttribute("aria-expanded", "false");
  await menu.click();
  await page.keyboard.press("Escape");
  await expect(navigation).not.toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("a stored transaction flows into prediction without reentering its feature vector", async ({
  page,
  request,
}) => {
  await page.goto("/#transactions");
  const row = page.getByRole("button", { name: /TX-\d+/ }).first();
  await row.click();
  const drawer = page.getByRole("dialog", { name: "Transaction details" });
  await drawer.getByRole("link", { name: "Use for prediction" }).click();
  await expect(drawer).not.toBeVisible();
  const txid = new URLSearchParams(new URL(page.url()).hash.split("?")[1]).get(
    "transaction",
  );
  const tx = await (await request.get(`/api/v1/transactions/${txid}`)).json();
  await expect(page.getByLabel("Feature Amount")).toHaveValue(
    String(tx.features.Amount),
  );
  await expect(
    page.getByLabel("Feature V1", { exact: true }),
  ).not.toBeVisible();
  const pending = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/predict") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Predict transaction", exact: true })
    .click();
  const response = await pending;
  expect(response.ok()).toBeTruthy();
  expect(response.request().postDataJSON().features).toEqual(tx.features);
  expect(response.request().postDataJSON().provenance).toBe(tx.provenance);
});

test("mobile model comparison remains keyboard-scrollable", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#laboratory");
  const table = page.getByRole("region", { name: "Model comparison results" });
  await table.focus();
  await page.keyboard.press("ArrowRight");
  await expect
    .poll(() => table.evaluate((element) => element.scrollLeft))
    .toBeGreaterThan(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("multi-dataset laboratory shows published evidence and honest access blockers", async ({
  page,
  request,
}) => {
  const before = await (
    await request.get("http://127.0.0.1:8000/api/v1/models")
  ).json();
  const catalog = await (
    await request.get("http://127.0.0.1:8000/api/v1/benchmarks")
  ).json();
  expect(catalog.report_errors).toEqual([]);
  expect(
    catalog.experiments.filter(
      (e: { dataset_id: string }) => e.dataset_id === "ulb",
    ),
  ).toHaveLength(2);
  await page.goto("/#laboratory");
  await page
    .getByRole("combobox", { name: "Dataset", exact: true })
    .selectOption("paysim");
  await expect(
    page.getByText("Simulation benchmark; not real transaction evidence.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Model comparison results" }),
  ).toBeVisible();
  await expect(page.getByText(/95% Wilson intervals/)).toBeVisible();
  await page.getByText("Verified dataset comparison", { exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Verified dataset comparison" }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Dataset", exact: true })
    .selectOption("ieee_cis");
  await expect(page.getByText(/No metrics are claimed/)).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Model comparison results" }),
  ).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole("combobox", { name: "Dataset", exact: true })
    .selectOption("ulb");
  await expect(
    page.getByRole("region", { name: "Model comparison results" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  const after = await (
    await request.get("http://127.0.0.1:8000/api/v1/models")
  ).json();
  expect(after).toEqual(before);
});
