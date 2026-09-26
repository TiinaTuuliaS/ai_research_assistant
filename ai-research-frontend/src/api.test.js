import { api, clearLegacyStorage } from "./api";

beforeEach(() => { global.fetch = jest.fn(); localStorage.clear(); });
afterEach(() => { jest.restoreAllMocks(); });

test("sends cookie credentials and CSRF header", async () => {
  fetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({ user_id: 1 }) });
  await api("/login", { method: "POST", body: "{}" });
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/login"), expect.objectContaining({
    credentials: "include", headers: expect.objectContaining({ "X-Requested-With": "ResearchApp" })
  }));
});

test("expired sessions clear legacy data and notify the app", async () => {
  localStorage.setItem("user", "old");
  localStorage.setItem("selectedResearch", "private");
  const listener = jest.fn();
  window.addEventListener("session-expired", listener);
  fetch.mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: "Expired" }) });
  await expect(api("/researches")).rejects.toThrow("Expired");
  expect(listener).toHaveBeenCalledTimes(1);
  expect(localStorage.getItem("selectedResearch")).toBeNull();
  expect(localStorage.getItem("user")).toBeNull();
  window.removeEventListener("session-expired", listener);
});

test("handles logout with an empty response", async () => {
  fetch.mockResolvedValue({ ok: true, status: 204 });
  await expect(api("/logout", { method: "POST" })).resolves.toBeNull();
  clearLegacyStorage();
});

test("explains an outdated backend instead of blaming field lengths", async () => {
  fetch.mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ type: "extra_forbidden", loc: ["body", "research_type"] }] }) });
  await expect(api("/research-jobs")).rejects.toThrow("Käynnistä backend uudelleen");
});

test("identifies the field and actual length limit", async () => {
  fetch.mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ type: "string_too_long", loc: ["body", "goal"], ctx: { max_length: 1000 } }] }) });
  await expect(api("/research-jobs")).rejects.toThrow("Tutkimuskysymys: enintään 1000 merkkiä.");
});
