import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import { emptyDraft, readDraft, saveDraft } from "./researchDraft";
import { researchTypes, researchPayload, researchPreview } from "./researchTypes";
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
function Form() {
  const [draft, setDraft] = useState(emptyDraft);
  return <MemoryRouter><Dashboard draft={draft} setDraft={setDraft} /></MemoryRouter>;
}
test("two choices preserve unfinished answers without offering demand research", () => {
  expect(researchTypes.map(t => t.id)).toEqual(["competition", "market"]);
  render(<Form />);
  const label = "Mitä tuotteita tai palveluja vertaillaan?";
  fireEvent.change(screen.getByLabelText(label), { target: { value: "Pyörähuollot" } });
  fireEvent.click(screen.getByRole("button", { name: /Markkinan tilannekuva ja kehitys/ }));
  expect(screen.queryByLabelText(label)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /Kilpailutarjonnan kartoitus/ }));
  expect(screen.getByLabelText(label)).toHaveValue("Pyörähuollot");
  expect(screen.queryByRole("button", { name: /Onko idealleni kysyntää/ })).not.toBeInTheDocument();
});
test("only selected context reaches the API", () => {
  const payload = researchPayload({ ...emptyDraft, solution: "Huolto", competitors: "A", criteria: "Hinta", problem: "old demand", question: "other mode" });
  expect(payload).toMatchObject({research_type: "competition", topic: "Huolto", competitors: "A", goal: "Vertailuperusteet: Hinta"});
  expect(payload).not.toHaveProperty("problem");
  expect(JSON.stringify(payload)).not.toContain("old demand");
});
test("market period and gaps follow the selected mode", () => {
  const draft = {...emptyDraft, research_type: "market", industry: "Huoltopalvelut", market_focus: "changes", period: "2023–2026"};
  expect(researchPayload(draft).goal).toContain("2023–2026");
  expect(researchPreview({...draft, period: ""}).gaps).toContain("Muutoksen tarkastelujakso jäi avoimeksi.");
});
test("removed demand draft resets instead of being submitted as a comparison", () => {
  sessionStorage.setItem("research-draft", JSON.stringify({research_type: "demand", idea: "Old idea", topic: "Old"}));
  expect(readDraft()).toEqual(emptyDraft);
  saveDraft({...emptyDraft, research_type: "market", industry: "Huolto", period: "2023–2026"});
  expect(readDraft()).toMatchObject({research_type: "market", industry: "Huolto", period: "2023–2026"});
  sessionStorage.clear();
});
