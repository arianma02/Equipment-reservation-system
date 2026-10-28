import { test, expect, type Page } from "@playwright/test";

const equipment = {
  id: 1,
  name: "Camera",
  asset_tag: "CAM-1",
  category_id: 1,
  category_name: "Cameras",
  status: "active",
};
const user = {
  id: 1,
  email: "user@example.com",
  role: "user",
  status: "active",
};

async function mockApi(
  page: Page,
  options: { conflict?: boolean; expired?: boolean; forbidden?: boolean } = {},
) {
  let reservation: Record<string, unknown> | null = null;
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();
    const reply = (body: unknown, status = 200) =>
      route.fulfill({ status, json: body });
    if (path === "/login")
      return reply({
        access_token: "browser-test-token",
        token_type: "bearer",
      });
    if (path === "/me") return reply(user);
    if (path === "/categories") return reply([{ id: 1, name: "Cameras" }]);
    if (path === "/equipment") return reply([equipment]);
    if (path === "/equipment/1") return reply(equipment);
    if (path.endsWith("/availability")) return reply({ available: true });
    if (path === "/equipment/1/reservations") {
      if (options.expired) return reply({ detail: "Invalid token" }, 401);
      if (options.forbidden)
        return reply({ detail: "Admin access required" }, 403);
      if (options.conflict)
        return reply(
          { detail: "Equipment is already reserved for the selected dates" },
          409,
        );
      reservation = {
        id: 1,
        user_id: 1,
        equipment_id: 1,
        equipment_name: "Camera",
        status: "active",
        ...route.request().postDataJSON(),
      };
      return reply(reservation, 201);
    }
    if (path === "/reservations/me")
      return reply(reservation ? [reservation] : []);
    if (path === "/reservations/1/cancel") {
      reservation = { ...reservation, status: "cancelled" };
      return reply(reservation);
    }
    throw new Error(`Unexpected API call: ${method} ${path}`);
  });
}

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill("testpassword");
  await page.getByRole("button", { name: "Login", exact: true }).click();
  await expect(page.getByText(`Logged in as ${user.email}`)).toBeVisible();
}

async function openBooking(page: Page) {
  await page.goto("/equipment/1");
  await page.getByLabel("Start date").fill("2099-01-01");
  await page.getByLabel("End date").fill("2099-01-02");
}

test("login, book, view history, and cancel", async ({ page }) => {
  await mockApi(page);
  await login(page);
  await openBooking(page);
  await page.getByRole("button", { name: "Check availability" }).click();
  await expect(page.getByText("Available", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Reserve equipment" }).click();
  await expect(
    page.getByText("Reservation created", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "My Reservations" }).click();
  await expect(page.getByRole("heading", { name: "Camera" })).toBeVisible();
  await page.getByRole("button", { name: "Cancel reservation" }).click();
  await expect(page.getByText("cancelled", { exact: true })).toBeVisible();
});

test("booking conflict is visible without losing the session", async ({
  page,
}) => {
  await mockApi(page, { conflict: true });
  await login(page);
  await openBooking(page);
  await page.getByRole("button", { name: "Reserve equipment" }).click();
  await expect(
    page.getByText("Equipment is already reserved for the selected dates"),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Logout" })).toBeVisible();
});

test("expired session clears login and explains what happened", async ({
  page,
}) => {
  await mockApi(page, { expired: true });
  await login(page);
  await openBooking(page);
  await page.getByRole("button", { name: "Reserve equipment" }).click();
  await expect(page.getByRole("alert")).toHaveText(
    "Your session has ended. Please log in again.",
  );
  await expect(page.getByRole("button", { name: "Logout" })).toHaveCount(0);
  expect(
    await page.evaluate(() => localStorage.getItem("access_token")),
  ).toBeNull();
});

test("a permission denial does not expire a valid session", async ({
  page,
}) => {
  await mockApi(page, { forbidden: true });
  await login(page);
  await openBooking(page);
  await page.getByRole("button", { name: "Reserve equipment" }).click();
  await expect(page.getByText("Admin access required")).toBeVisible();
  await expect(page.getByRole("button", { name: "Logout" })).toBeVisible();
});

test("changing dates invalidates an in-flight availability response", async ({
  page,
}) => {
  await mockApi(page);
  await openBooking(page);
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  let started!: () => void;
  const requestStarted = new Promise<void>((resolve) => {
    started = resolve;
  });
  await page.route("**/availability?**", async (route) => {
    started();
    await held;
    await route.fulfill({ json: { available: true } }).catch(() => {});
  });
  await page.getByRole("button", { name: "Check availability" }).click();
  await requestStarted;
  await page.getByLabel("Start date").fill("2099-02-01");
  release();
  await expect(page.getByText("Available", { exact: true })).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Check availability" }),
  ).toBeEnabled();
  // A new check still succeeds after the aborted one.
  await page.getByLabel("End date").fill("2099-02-02");
  await page.getByRole("button", { name: "Check availability" }).click();
  await expect(page.getByText("Available", { exact: true })).toBeVisible();
});
