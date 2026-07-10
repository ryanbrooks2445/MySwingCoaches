import { expect, test } from "@playwright/test";

const publicPages = [
  { path: "/", heading: /Stop guessing/i },
  { path: "/pricing", heading: /Pay per swing/i },
  { path: "/example", heading: /A real, anonymized report/i },
  { path: "/login", heading: /^Log in$/i },
  { path: "/signup", heading: /Create your free account/i },
  { path: "/support", heading: /Support/i },
  { path: "/contact", heading: /Contact ForeFixed/i },
  { path: "/terms", heading: /Terms/i },
  { path: "/privacy", heading: /Privacy/i },
  { path: "/refund-policy", heading: /Refund/i },
];

for (const pageDef of publicPages) {
  test(`${pageDef.path} shows visible heading`, async ({ page }) => {
    await page.goto(pageDef.path);
    const heading = page.getByRole("heading", { name: pageDef.heading }).first();
    await expect(heading).toBeVisible();
    await expect(heading).toHaveCSS("opacity", "1");
  });
}

test("/dashboard redirects unauthenticated users to login", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/);
});
