import { fireEvent, render, screen } from "@testing-library/react";
import ReportActions from "./ReportActions";
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
const props = { topic: "Test <script>", result: "Final answer", steps: [{ key: "researcher", label: "Tutkija", output: "Actual perspective" }] };
afterEach(() => jest.restoreAllMocks());
test("PDF print document contains all perspectives and escapes the title", () => {
  const doc = document.implementation.createHTMLDocument();
  const popup = { document: doc, focus: jest.fn(), print: jest.fn() };
  jest.spyOn(window, "open").mockReturnValue(popup);
  render(<ReportActions {...props} />);
  fireEvent.click(screen.getByText("Tallenna PDF"));
  expect(popup.print).toHaveBeenCalledTimes(1);
  expect(doc.body.textContent).toContain("Actual perspective");
  expect(doc.body.textContent).toContain("Final answer");
  expect(doc.querySelector("script")).toBeNull();
});
test("fallback share links contain an excerpt, not a private app URL", () => {
  render(<ReportActions {...props} />);
  fireEvent.click(screen.getByText("Jaa raportti"));
  expect(screen.getByText("Sähköposti").getAttribute("href")).toContain("mailto:");
  const url = screen.getByText("WhatsApp").getAttribute("href");
  expect(decodeURIComponent(url)).toContain("Final answer");
  expect(url).not.toContain("localhost");
});
