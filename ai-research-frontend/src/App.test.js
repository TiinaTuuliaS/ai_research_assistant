import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import App from "./App";
import { api } from "./api";

jest.mock("./api", () => ({ ...jest.requireActual("./api"), api: jest.fn() }));
jest.mock("./components/Dashboard", () => () => <p>Research dashboard</p>);
jest.mock("./components/History", () => () => <p>Research history</p>);

beforeEach(() => { jest.clearAllMocks(); localStorage.clear(); });

test("does not trust old localStorage identity", async () => {
  localStorage.setItem("user", JSON.stringify({ user_id: 123 }));
  localStorage.setItem("selectedResearch", "old report");
  api.mockRejectedValue(Object.assign(new Error("Unauthorized"), { status: 401 }));
  render(<App />);
  await screen.findByRole("button", { name: "Kirjaudu" });
  expect(screen.queryByText("Research dashboard")).not.toBeInTheDocument();
  expect(localStorage.getItem("user")).toBeNull();
  expect(localStorage.getItem("selectedResearch")).toBeNull();
});

test("restores server session and revokes it on logout", async () => {
  api.mockResolvedValueOnce({ user_id: 1 }).mockResolvedValueOnce(null);
  render(<App />);
  await screen.findByText("Research dashboard");
  fireEvent.click(screen.getByRole("button", { name: /Logout/ }));
  await screen.findByRole("button", { name: "Kirjaudu" });
  expect(api).toHaveBeenCalledWith("/logout", { method: "POST" });
  expect(screen.queryByText("Research dashboard")).not.toBeInTheDocument();
});
