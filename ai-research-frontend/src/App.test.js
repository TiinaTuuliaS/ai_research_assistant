import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import App from "./App";
import { api } from "./api";

jest.mock("./api", () => ({ ...jest.requireActual("./api"), api: jest.fn() }));
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
jest.mock("./components/History", () => () => <p>Private research history</p>);

const unauthorized = () => Promise.reject(Object.assign(new Error("Unauthorized"), { status: 401 }));
const fillBrief = () => {
  fireEvent.change(screen.getByLabelText("Mikä on ideasi?"), { target: { value: "Uusi palvelu" } });
  fireEvent.change(screen.getByLabelText("Mihin tarpeeseen tai toiveeseen idea vastaa?"), { target: { value: "Testaa kysyntää" } });
  fireEvent.change(screen.getByLabelText("Kenelle ja mille alueelle idea on tarkoitettu?"), { target: { value: "Suomi, pienyritykset" } });
  fireEvent.change(screen.getByLabelText(/Kokeilubudjetti/), { target: { value: "0" } });
};

beforeEach(() => {
  jest.clearAllMocks(); localStorage.clear(); sessionStorage.clear();
  window.history.replaceState({}, "", "/");
});

test("public landing is visible even before the session request finishes", () => {
  api.mockReturnValue(new Promise(() => {}));
  render(<App />);
  expect(screen.getByRole("heading", { name: /AI Markkinatutkimusassistentti/ })).toBeInTheDocument();
  expect(screen.getByText("Uuden liikeidean kysynnän testaus")).toBeInTheDocument();
});

test("anonymous users can see the example, but cannot start research", async () => {
  localStorage.setItem("user", JSON.stringify({ user_id: 123 }));
  localStorage.setItem("selectedResearch", "old report");
  api.mockImplementation(unauthorized);
  render(<App />);
  const button = await screen.findByRole("button", { name: /Kirjaudu ja jatka/ });
  expect(localStorage.getItem("user")).toBeNull();
  expect(localStorage.getItem("selectedResearch")).toBeNull();
  fillBrief(); fireEvent.click(button);
  await screen.findByRole("button", { name: "Kirjaudu" });
  expect(api.mock.calls.some(([path]) => path === "/research-jobs")).toBe(false);
});

test("brief survives signup, login and return; only an explicit click starts research", async () => {
  api.mockImplementation(path => {
    if (path === "/me") return unauthorized();
    if (path === "/signup") return Promise.resolve({ message: "Created" });
    if (path === "/login") return Promise.resolve({ user_id: 1 });
    if (path === "/research-jobs") return Promise.resolve({ id: "job1", status: "queued", steps: [] });
    if (path === "/research-jobs/job1") return Promise.resolve({ topic: "Uusi palvelu", status: "completed", steps: [], result: "Valmis suunnitelma" });
    return Promise.reject(new Error(`Unexpected request ${path}`));
  });
  render(<App />);
  await screen.findByRole("button", { name: /Kirjaudu ja jatka/ });
  fillBrief();
  fireEvent.click(screen.getByRole("button", { name: /Kirjaudu ja jatka/ }));
  fireEvent.click(await screen.findByRole("link", { name: "Luo tili" }));
  fireEvent.change(screen.getByLabelText("Sähköposti tai käyttäjätunnus"), { target: { value: "test@example.test" } });
  fireEvent.change(screen.getByLabelText(/Salasana/), { target: { value: "test-password-123" } });
  fireEvent.click(screen.getByRole("button", { name: "Luo tili" }));
  await screen.findByRole("button", { name: "Kirjaudu" });
  fireEvent.change(screen.getByLabelText("Sähköposti tai käyttäjätunnus"), { target: { value: "test@example.test" } });
  fireEvent.change(screen.getByLabelText("Salasana"), { target: { value: "test-password-123" } });
  fireEvent.click(screen.getByRole("button", { name: "Kirjaudu" }));
  const run = await screen.findByRole("button", { name: /Aloita tutkimus/ });
  expect(screen.getByLabelText("Mikä on ideasi?")).toHaveValue("Uusi palvelu");
  expect(screen.getByLabelText(/Kokeilubudjetti/)).toHaveValue(0);
  expect(api.mock.calls.some(([path]) => path === "/research-jobs")).toBe(false);
  fireEvent.click(run);
  await screen.findByText("Valmis suunnitelma");
  const request = api.mock.calls.find(([path]) => path === "/research-jobs")[1];
  expect(JSON.parse(request.body)).toEqual({ research_type: "demand", topic: "Uusi palvelu", goal: "", problem: "Testaa kysyntää", competitors: "", target_market: "Suomi, pienyritykset", budget_eur: 0, language: "suomi" });
});

test("history requires login and returns to history afterwards", async () => {
  window.history.replaceState({}, "", "/history");
  api.mockImplementation(path => path === "/me" ? unauthorized() : Promise.resolve({ user_id: 1 }));
  render(<App />);
  await screen.findByRole("button", { name: "Kirjaudu" });
  expect(screen.queryByText("Private research history")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Sähköposti tai käyttäjätunnus"), { target: { value: "test" } });
  fireEvent.change(screen.getByLabelText("Salasana"), { target: { value: "password" } });
  fireEvent.click(screen.getByRole("button", { name: "Kirjaudu" }));
  await screen.findByText("Private research history");
});

test("logout clears the brief and keeps the public landing visible", async () => {
  api.mockResolvedValueOnce({ user_id: 1 }).mockResolvedValueOnce(null);
  render(<App />);
  await screen.findByRole("button", { name: "Kirjaudu ulos" });
  fillBrief();
  fireEvent.click(screen.getByRole("button", { name: "Kirjaudu ulos" }));
  await screen.findByRole("button", { name: /Kirjaudu ja jatka/ });
  expect(screen.getByLabelText("Mikä on ideasi?")).toHaveValue("");
  expect(sessionStorage.getItem("research-draft")).toBeNull();
  expect(screen.getByRole("heading", { name: /AI Markkinatutkimusassistentti/ })).toBeInTheDocument();
});

test("restores an unfinished brief after refresh", async () => {
  sessionStorage.setItem("research-draft", JSON.stringify({ idea: "Tallessa", problem: "Tavoite", audience: "Suomi", budget_eur: "150" }));
  api.mockImplementation(unauthorized);
  render(<App />);
  await waitFor(() => expect(screen.getByLabelText("Mikä on ideasi?")).toHaveValue("Tallessa"));
});
