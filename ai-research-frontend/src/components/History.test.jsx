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

test("shows research date in list and opened report without inventing legacy dates", async () => {
  const createdAt = "2026-10-15T09:30:00+00:00";
  api.mockResolvedValue([
    { id: 2, topic: "Dated report", result: "Content", created_at: createdAt },
    { id: 1, topic: "Legacy report", result: "Old", created_at: null },
  ]);
  render(<MemoryRouter><History user={{ user_id: 1 }} /></MemoryRouter>);
  await screen.findByText("Dated report");
  expect(document.querySelector("time")).toHaveAttribute("datetime", createdAt);
  expect(document.querySelector("time")).toHaveTextContent("15.10.2026");
  expect(screen.getByText("Tutkimuspäivämäärää ei ole tallennettu.")).toBeInTheDocument();
  fireEvent.click(screen.getByText("Dated report"));
  expect(document.querySelectorAll("time")).toHaveLength(2);
});

test("shows newest completed reports before older unfinished jobs and can refresh", async () => {
  api.mockResolvedValueOnce([
    { id: "job-old", topic: "Old failed research", status: "failed", steps: [] },
    { id: 19, topic: "Spinning demand", status: "completed", result: "Demand report" },
    { id: 20, topic: "Spinning competition", status: "completed", result: "Competition report" },
  ]).mockResolvedValueOnce([{ id: 21, topic: "Newest report", status: "completed", result: "New" }]);
  render(<MemoryRouter><History user={{ user_id: 2 }} /></MemoryRouter>);
  await screen.findByText("Spinning competition");
  expect(screen.getAllByRole("heading", { level: 3 }).map(node => node.textContent)).toEqual([
    "Spinning competition", "Spinning demand", "Old failed research",
  ]);
  fireEvent.click(screen.getByRole("button", { name: "Päivitä lista" }));
  await screen.findByText("Newest report");
  expect(api).toHaveBeenCalledTimes(2);
  expect(screen.queryByText("Old failed research")).not.toBeInTheDocument();
});

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

test("limited reports have their own group and open as a limited result", async () => {
  api.mockResolvedValue([{id: 42, topic: "Restaurants", status: "limited", result: "Saved limited findings", steps: []}]);
  render(<MemoryRouter><History user={{user_id: 1}} /></MemoryRouter>);
  await screen.findByText("Restaurants");
  expect(screen.queryByRole("region", {name: "Valmiit raportit · uusimmat ensin"})).not.toBeInTheDocument();
  expect(screen.getByRole("region", {name: "Rajatut tulokset · loppuraportti ei valmistunut"})).toBeInTheDocument();
  fireEvent.click(screen.getByText("Restaurants"));
  expect(screen.getByRole("status")).toHaveTextContent("Rajattu tulos");
  expect(screen.getByText("Saved limited findings")).toBeInTheDocument();
});
