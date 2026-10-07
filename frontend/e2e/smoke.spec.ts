import { expect, test } from "@playwright/test";

const nav = (page: import("@playwright/test").Page, name: string) =>
  page.getByRole("navigation", { name: "Main" }).getByRole("link", { name });

test("generate data, train, inspect metrics, predict, roll back", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Generate synthetic dataset" }).click();
  await expect(page.getByText("Generated 100 synthetic labelled documents")).toBeVisible();
  await expect(page.getByText("Invoice: 20")).toBeVisible();

  await nav(page, "2 · Train").click();
  await page.getByRole("button", { name: "Train", exact: true }).click();
  await expect(page.getByText(/Comparison — run #1/)).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText("best", { exact: true })).toBeVisible();

  await nav(page, "3 · Metrics").click();
  await expect(page.getByRole("table", { name: "Confusion matrix" })).toBeVisible();
  await expect(page.getByText("Macro F1")).toBeVisible();

  await nav(page, "4 · Predict").click();
  await page.getByRole("button", { name: "mystery.txt" }).click();
  await expect(page.getByRole("heading", { name: /Invoice/ })).toBeVisible();

  await nav(page, "Models").click();
  await page
    .getByRole("button", { name: /roll back/i })
    .first()
    .click();
  await expect(page.getByText("active", { exact: true })).toHaveCount(1);
});
