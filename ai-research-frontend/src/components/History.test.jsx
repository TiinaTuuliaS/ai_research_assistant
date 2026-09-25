import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import History from "./History";
import { api } from "../api";

jest.mock("../api", () => ({ api: jest.fn() }));
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
jest.mock("framer-motion", () => ({
  motion: { div: ({ whileHover, ...props }) => <div {...props} /> }
}));

const reports = [{ id: 1, topic: "Market report", result: "Report content" }];

beforeEach(() => { jest.clearAllMocks(); localStorage.clear(); });

test("fetches once across renders and report selection", async () => {
  api.mockResolvedValue(reports);
  const view = render(<MemoryRouter><History user={{ user_id: 1 }} /></MemoryRouter>);
  await screen.findByText("Market report");
  fireEvent.click(screen.getByText("Market report"));
  expect(screen.getByText("Report content")).toBeInTheDocument();
  view.rerender(<MemoryRouter><History user={{ user_id: 1 }} /></MemoryRouter>);
  expect(api).toHaveBeenCalledTimes(1);
  expect(api).toHaveBeenCalledWith("/researches", expect.objectContaining({ signal: expect.anything() }));
});

test("ignores legacy cached report and unowned navigation IDs", async () => {
  localStorage.setItem("selectedResearch", JSON.stringify({ id: 99, result: "Other user's report" }));
  api.mockResolvedValue(reports);
  render(<MemoryRouter initialEntries={[{ pathname: "/history", state: { researchId: 99 } }]}>
    <History user={{ user_id: 1 }} />
  </MemoryRouter>);
  await screen.findByText("Market report");
  expect(screen.queryByText("Other user's report")).not.toBeInTheDocument();
  expect(screen.queryByText("Report content")).not.toBeInTheDocument();
});

test("shows errors and retries explicitly", async () => {
  api.mockRejectedValueOnce(new Error("Offline")).mockResolvedValueOnce([]);
  render(<MemoryRouter><History user={{ user_id: 1 }} /></MemoryRouter>);
  await screen.findByRole("alert");
  fireEvent.click(screen.getByText("Yritä uudelleen"));
  await screen.findByText("Ei vielä tutkimuksia.");
  expect(api).toHaveBeenCalledTimes(2);
});

test("aborts obsolete requests and discards their results after user changes", async () => {
  let resolveOld;
  api.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }))
    .mockResolvedValueOnce([]);
  const view = render(<MemoryRouter><History user={{ user_id: 1 }} /></MemoryRouter>);
  const signal = api.mock.calls[0][1].signal;
  view.rerender(<MemoryRouter><History user={{ user_id: 2 }} /></MemoryRouter>);
  expect(signal.aborted).toBe(true);
  resolveOld(reports);
  await waitFor(() => expect(screen.getByText("Ei vielä tutkimuksia.")).toBeInTheDocument());
  expect(screen.queryByText("Market report")).not.toBeInTheDocument();
});
