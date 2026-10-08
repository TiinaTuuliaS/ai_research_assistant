import { fireEvent, render, screen } from "@testing-library/react";
import PartialResults from "./PartialResults";
import { api } from "../api";

jest.mock("../api", () => ({ api: jest.fn() }));
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
const job = {
  id: "saved", topic: "Idea", status: "failed", can_retry_report: true,
  partial_result: "# Tutkimuksen osatulokset\nEi hyväksytty loppuanalyysi. Tallennettu havainto.",
  draft: "Tarkistamaton teksti", validation_error: "Lähdeviitteet puuttuvat.",
  steps: [...["researcher", "trend", "analyst", "strategist"].map(key => ({ key, status: "completed" })),
    { key: "writer", status: "failed" }],
};
beforeEach(() => api.mockReset());

test("failed job exposes partial results without opening agent disclosures", () => {
  render(<PartialResults initialJob={job} />);
  expect(screen.getByText(/Tallennettu havainto/)).toBeVisible();
  expect(screen.getByRole("status")).toHaveTextContent("4/5");
  expect(screen.getByText("Lähdeviitteet puuttuvat.")).toBeVisible();
  expect(screen.getByRole("button", { name: "Lue valmistuneet tulokset" })).toBeEnabled();
  expect(screen.queryByRole("heading", { name: "Yhdistetty loppuraportti" })).not.toBeInTheDocument();
  expect(screen.getByText("Tarkistamaton teksti").closest("details")).not.toHaveAttribute("open");
});

test("retry posts only the existing job and displays its completed report", async () => {
  api.mockResolvedValueOnce({ ...job, status: "queued", can_retry_report: false })
    .mockResolvedValueOnce({ ...job, status: "completed", result: "Uusi loppuraportti" });
  render(<PartialResults initialJob={job} />);
  fireEvent.click(screen.getByRole("button", { name: "Korjaa loppuraportti" }));
  expect(await screen.findByText("Uusi loppuraportti")).toBeVisible();
  expect(api.mock.calls[0][0]).toBe("/research-jobs/saved/retry-report");
  expect(api.mock.calls[0][1].method).toBe("POST");
  expect(api.mock.calls.every(([path]) => path.startsWith("/research-jobs/saved"))).toBe(true);
});

test("old job explains why retry is unavailable and no-output failure is explicit", () => {
  render(<PartialResults initialJob={{ ...job, can_retry_report: false, partial_result: "", draft: "" }} />);
  expect(screen.queryByRole("button", { name: "Korjaa loppuraportti" })).not.toBeInTheDocument();
  expect(screen.getByText("Tutkimuksesta ei valmistunut luettavia välituloksia.")).toBeVisible();
});
