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
  const label = "Mitä vertaillaan?";
  fireEvent.change(screen.getByLabelText(label), { target: { value: "Pyörähuollot" } });
  fireEvent.click(screen.getByRole("button", { name: /Markkinan tilannekuva ja kehitys/ }));
  expect(screen.queryByLabelText(label)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /Kilpailijavertailu/ }));
  expect(screen.getByLabelText(label)).toHaveValue("Pyörähuollot");
  expect(screen.queryByRole("button", { name: /Onko idealleni kysyntää/ })).not.toBeInTheDocument();
});
test("only selected context reaches the API", () => {
  const payload = researchPayload({ ...emptyDraft, solution: "Huolto", competitors: "A", criteria: "Hinta", problem: "old demand", question: "other mode" });
  expect(payload).toMatchObject({research_type: "competition", topic: "Huolto", competitors: "A", goal: "Vertailuperusteet: Hinta"});
  expect(payload).not.toHaveProperty("problem");
  expect(JSON.stringify(payload)).not.toContain("old demand");
});
test("market changes need no period and ignore stale saved years", () => {
  const draft = {...emptyDraft, research_type: "market", industry: "Huoltopalvelut", market_focus: "changes", period: "2023–2026"};
  expect(researchPayload(draft).goal).not.toContain("2023–2026");
  expect(researchPreview({...draft, region: "Suomi", period: ""}).gaps).toEqual([]);
  render(<Form />);
  fireEvent.click(screen.getByRole("button", {name: /Markkinan tilannekuva ja kehitys/}));
  expect(screen.queryByLabelText(/Mitä ajanjaksoa/)).not.toBeInTheDocument();
});
test("removed demand draft resets instead of being submitted as a comparison", () => {
  sessionStorage.setItem("research-draft", JSON.stringify({research_type: "demand", idea: "Old idea", topic: "Old"}));
  expect(readDraft()).toEqual(emptyDraft);
  saveDraft({...emptyDraft, research_type: "market", industry: "Huolto", period: "2023–2026"});
  expect(readDraft()).toMatchObject({research_type: "market", industry: "Huolto"});
  expect(readDraft()).not.toHaveProperty("period");
  sessionStorage.clear();
});

test("comparison has four fields and ignores removed audience data", () => {
  render(<Form />);
  expect(researchTypes[0].fields).toHaveLength(4);
  expect(screen.queryByLabelText(/Keitä asiakkaita/)).not.toBeInTheDocument();
  expect(screen.getByLabelText(/Tietyt yritykset tai palvelut/)).not.toBeRequired();
  const draft = {...emptyDraft, solution: "Ravintolat", competition_region: "Tampere", competition_market: "Old audience", market_audience: "Other mode"};
  expect(researchPayload(draft).target_market).toBe("Alue: Tampere.");
  expect(researchPreview(draft).gaps).not.toContain("Asiakasryhmä jäi määrittelemättä.");
  expect(researchPreview(draft).text).not.toContain("Old audience");
});

test("market research neither asks for nor transmits an old audience", () => {
  render(<Form />);
  fireEvent.click(screen.getByRole("button", {name: /Markkinan tilannekuva ja kehitys/}));
  expect(screen.queryByLabelText(/Keitä asiakkaita/)).not.toBeInTheDocument();
  const draft = {...emptyDraft, research_type: "market", industry: "Ravintolat", region: "Suomi", market_audience: "Old audience"};
  expect(researchPayload(draft).target_market).toBe("Alue: Suomi.");
  expect(researchPreview(draft).text).not.toContain("Old audience");
  expect(researchPreview(draft).gaps).not.toContain("Asiakasryhmä jäi määrittelemättä.");
});

test("market research ignores the removed extra question", () => {
  const draft = {...emptyDraft, research_type: "market", industry: "Huoltopalvelut", market_focus: "changes", period: "2023–2026", question: "Old extra instructions"};
  expect(researchTypes[1].fields.map(field => field.name)).toEqual(["industry", "region", "market_focus"]);
  expect(researchPayload(draft).goal).not.toContain("2023–2026");
  expect(researchPayload(draft).goal).not.toContain("Old extra instructions");
  expect(researchPreview(draft).text).not.toContain("Old extra instructions");
});


test("market area dropdown defaults to Finland and sends the selected scope", () => {
  render(<Form />);
  fireEvent.click(screen.getByRole("button", {name: /Markkinan tilannekuva ja kehitys/}));
  const area = screen.getByLabelText("Mitä aluetta tarkastellaan?");
  expect(area.tagName).toBe("SELECT");
  expect(area).toHaveValue("Suomi");
  for (const [value, label] of [["EU", "Euroopan unioni"], ["world", "Koko maailma — yleiskatsaus"]]) {
    fireEvent.change(area, {target: {value}});
    expect(screen.getByRole("region", {name: "Tutkimuskysymyksen esikatselu"})).toHaveTextContent(`Alue: ${label}.`);
    expect(researchPayload({...emptyDraft, research_type: "market", region: value}).target_market).toBe(`Alue: ${label}.`);
  }
  fireEvent.click(screen.getByRole("button", {name: /Kilpailijavertailu/}));
  const comparisonArea = screen.getByLabelText(/Miltä alueelta/);
  expect(comparisonArea.tagName).toBe("INPUT");
  fireEvent.change(comparisonArea, {target: {value: "Tampereen seutu"}});
  expect(screen.getByRole("region", {name: "Tutkimuskysymyksen esikatselu"})).toHaveTextContent("Alue: Tampereen seutu.");
});

test("old free-text market areas reset to Finland without changing comparison areas", () => {
  saveDraft({...emptyDraft, research_type: "market", region: "Tampere", competition_region: "Pirkanmaa"});
  expect(readDraft()).toMatchObject({region: "Suomi", competition_region: "Pirkanmaa"});
  expect(researchPayload({...emptyDraft, research_type: "market", region: "Tampere"}).target_market).toBe("Alue: Suomi.");
  for (const region of ["Suomi", "EU", "world"]) {
    saveDraft({...emptyDraft, region});
    expect(readDraft().region).toBe(region);
  }
  sessionStorage.clear();
});
