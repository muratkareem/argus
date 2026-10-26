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
  await expect(
    page.getByRole("heading", { name: "Intelligence overview" }),
  ).toBeVisible();
  await expect(page.getByText("LIVE WORKSPACE SNAPSHOT")).toBeVisible();
  await expect(
    page.getByText(`${snapshot.scored} scored / ${snapshot.total} stored`),
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
    .getByLabel("Analyst decision")
    .fill("Continue review; model alert is not proof of fraud.");
  await page.getByRole("button", { name: "Save decision" }).click();
  await expect(page.getByRole("status")).toContainText("Investigation saved");
  await page.reload();
  await page
    .getByRole("button", { name: `#${caseId} · Review ${txName}`, exact: true })
    .click();
  await expect(page.getByLabel("Case status")).toHaveValue("In Review");
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

test("research, graph, local copilot, and settings pages are usable", async ({
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
    .getByRole("link", { name: "Intelligence Graph", exact: true })
    .click();
  await expect(page.locator(".graph-canvas canvas").first()).toBeVisible();
  await page.getByLabel("Highlight entity type").selectOption("Device");
  await page.getByRole("button", { name: "Fit", exact: true }).click();
  await page.getByRole("link", { name: /AI Copilot/ }).click();
  await expect(
    page.getByText("Optional integration is disabled"),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analyze selected evidence" }),
  ).toBeDisabled();
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
  await expect(
    page.getByRole("heading", { name: "Intelligence overview" }),
  ).toBeVisible();
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
