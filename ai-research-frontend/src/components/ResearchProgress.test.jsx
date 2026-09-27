import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./Dashboard";
import AgentProgress from "./AgentProgress";
import ResearchReport, { reportText } from "./ResearchReport";
import { api } from "../api";

jest.mock("../api", () => ({ api: jest.fn() }));
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
const steps = [
  { key: "researcher", label: "Tutkija", description: "Kartoittaa", status: "completed", output: "Tutkijan havainto" },
  { key: "writer", label: "Kirjoittaja", description: "Yhdistää", status: "running", output: "" },
];
beforeEach(() => { jest.clearAllMocks(); sessionStorage.clear(); });

test("exhausted quota prevents submission but keeps reports accessible", () => {
  render(<MemoryRouter><Dashboard user={{ user_id: 1, quota: { limit: 3, used: 3, remaining: 0 } }}
    draft={{}} setDraft={() => {}} /></MemoryRouter>);
  expect(screen.getByText(/Tutkimuksia jäljellä: 0 \/ 3/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Tutkimukset käytetty" })).toBeDisabled();
  expect(screen.getByRole("link", { name: "Avaa omat raportit →" })).toHaveAttribute("href", "/history");
  fireEvent.submit(document.querySelector("form"));
  expect(api).not.toHaveBeenCalled();
});

test("last accepted attempt updates quota while its progress remains visible", async () => {
  const quota = { limit: 3, used: 3, remaining: 0 };
  api.mockResolvedValue({ id: "last", status: "completed", topic: "Aihe", result: "Valmis", steps, quota });
  render(<MemoryRouter><Dashboard user={{ user_id: 1, quota: { limit: 3, used: 2, remaining: 1 } }}
    draft={{ topic: "Aihe" }} setDraft={() => {}} /></MemoryRouter>);
  fireEvent.submit(document.querySelector("form"));
  await screen.findByRole("button", { name: "Tutkimukset käytetty" });
  expect(screen.getByText(/Tutkimuksia jäljellä: 0 \/ 3/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Tutkimukset käytetty" })).toBeDisabled();
});

test("progress reflects completed stages, never elapsed time", () => {
  const view = render(<AgentProgress job={{ status: "running", steps }} />);
  expect(screen.getByRole("progressbar")).toHaveAttribute("value", "50");
  expect(screen.getByRole("status")).toHaveTextContent("Kirjoittaja työskentelee");
  expect(screen.getByText("🤖")).toHaveClass("robot-working");
  view.rerender(<AgentProgress job={{ status: "failed", steps }} />);
  expect(screen.getByRole("status")).toHaveTextContent("Tutkimus keskeytyi");
  expect(screen.getByRole("progressbar")).not.toHaveAttribute("value", "100");
  expect(screen.getByText("🤖")).not.toHaveClass("robot-working");
});

test("separates actual perspectives, synthesis and sources; export retains all", () => {
  const result = "Yhteenveto\n\n## Lähteet\nLähdelinkit";
  render(<ResearchReport result={result} steps={steps} />);
  expect(screen.getByText("Tutkijan havainto").closest("details")).not.toHaveAttribute("open");
  expect(screen.getByRole("heading", { name: "Yhdistetty loppuraportti" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Lähteet" })).toBeInTheDocument();
  expect(reportText(result, steps)).toContain("Tutkijan havainto");
  expect(reportText(result, steps)).toContain("Yhteenveto");
});

test("resumes an existing job and retries only polling after a connection error", async () => {
  sessionStorage.setItem("research-job-1", "saved");
  api.mockRejectedValueOnce(new Error("Offline")).mockResolvedValueOnce({ id: "saved", status: "completed", steps, result: "Valmis vastaus", topic: "Aihe" });
  render(<MemoryRouter><Dashboard user={{ user_id: 1 }} draft={{ topic: "", goal: "", target_market: "", budget_eur: "" }} setDraft={() => {}} /></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: "Jatka edistymisen seurantaa" }));
  await screen.findByText("Valmis vastaus");
  expect(api.mock.calls.every(([path, options]) => path === "/research-jobs/saved" && !options.method)).toBe(true);
  expect(sessionStorage.getItem("research-job-1")).toBeNull();
});

test("aborts a pending status fetch on unmount and ignores its response", async () => {
  sessionStorage.setItem("research-job-1", "saved");
  let resolve;
  api.mockImplementation(() => new Promise(done => { resolve = done; }));
  const view = render(<MemoryRouter><Dashboard user={{ user_id: 1 }} draft={{ topic: "", goal: "", target_market: "", budget_eur: "" }} setDraft={() => {}} /></MemoryRouter>);
  await waitFor(() => expect(api).toHaveBeenCalledTimes(1));
  const signal = api.mock.calls[0][1].signal;
  view.unmount();
  expect(signal.aborted).toBe(true);
  await act(async () => resolve({ status: "completed", result: "Late result", steps }));
  expect(sessionStorage.getItem("research-job-1")).toBe("saved");
});
