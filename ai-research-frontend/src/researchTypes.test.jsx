import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import { emptyDraft } from "./researchDraft";
import { researchPayload, researchPreview } from "./researchTypes";
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
function Form() {
  const [draft, setDraft] = useState(emptyDraft);
  return <MemoryRouter><Dashboard draft={draft} setDraft={setDraft} /></MemoryRouter>;
}
test("choices change fields and preserve each mode's unfinished answers", () => {
  render(<Form />);
  fireEvent.change(screen.getByLabelText("Mitä tuotteesi tai palvelusi tekee?"), { target: { value: "Oma idea" } });
  fireEvent.click(screen.getByRole("button", { name: /Miten erotun kilpailijoista/ }));
  expect(screen.queryByLabelText("Mitä tuotteesi tai palvelusi tekee?")).not.toBeInTheDocument();
  expect(screen.getByLabelText(/Tunnetut kilpailijat/)).not.toBeRequired();
  fireEvent.click(screen.getByRole("button", { name: /Mitä tällä markkinalla tapahtuu/ }));
  expect(screen.getByLabelText(/Mitä aluetta tarkastellaan/)).not.toBeRequired();
  fireEvent.click(screen.getByRole("button", { name: /Onko idealleni kysyntää/ }));
  expect(screen.getByLabelText("Mitä tuotteesi tai palvelusi tekee?")).toHaveValue("Oma idea");
});
test("only the selected mode's context reaches the server", () => {
  const draft = { ...emptyDraft, research_type: "competition", solution: "Palvelu", competition_market: "Suomi", competitors: "Yritys A", problem: "Hidden demand context", question: "Hidden market context" };
  expect(researchPayload(draft)).toMatchObject({ research_type: "competition", topic: "Palvelu", target_market: "Asiakkaat: Suomi. Alue: ei määritelty.", competitors: "Yritys A", problem: "", goal: "", budget_eur: null });
});

test("preview follows the selected topic and openly identifies missing scope", () => {
  render(<Form />);
  const preview = screen.getByRole("region", { name: "Tutkimuskysymyksen esikatselu" });
  expect(preview).toHaveTextContent("Alue jäi määrittelemättä.");
  fireEvent.change(screen.getByLabelText("Mitä tuotteesi tai palvelusi tekee?"), { target: { value: "Älypuhelimen käytön verkkokurssi" } });
  fireEvent.change(screen.getByLabelText(/Keitä asiakkaasi ovat/), { target: { value: "Eläkeläiset" } });
  fireEvent.change(screen.getByLabelText(/Mitä aluetta tarkastellaan/), { target: { value: "Suomi" } });
  expect(preview).toHaveTextContent("Älypuhelimen käytön verkkokurssi");
  expect(preview).toHaveTextContent("Asiakkaat: Eläkeläiset. Alue: Suomi.");
  expect(preview).not.toHaveTextContent("Alue jäi määrittelemättä.");
});

test("mode-specific refinements reach the request without leaking other modes", () => {
  const base = { ...emptyDraft, idea: "Kurssi", audience: "Eläkeläiset", demand_region: "Suomi", payer: "Omainen", criteria: "Hinta", period: "2023–2026" };
  expect(researchPayload(base).goal).toContain("Omainen");
  const competition = researchPayload({ ...base, research_type: "competition", solution: "Pyörähuolto", competition_market: "Työmatkapyöräilijät", competition_region: "Tampere" });
  expect(competition.goal).toBe("Vertailuperusteet: Hinta");
  expect(competition.target_market).toContain("Tampere");
  expect(competition.goal).not.toContain("Omainen");
  const marketDraft = { ...base, research_type: "market", industry: "Verkkokurssit", market_focus: "changes", market_audience: "Kuluttajat", region: "Suomi" };
  const market = researchPayload(marketDraft);
  expect(market.goal).toContain("2023–2026");
  expect(market.goal).toContain("ajoitettua näyttöä");
  expect(researchPreview({ ...marketDraft, period: "" }).gaps).toContain("Muutoksen tarkastelujakso jäi avoimeksi.");
});

test("new scope fields survive a draft save and restore", () => {
  const { saveDraft, readDraft } = require("./researchDraft");
  saveDraft({ ...emptyDraft, demand_region: "Suomi", payer: "Omainen", criteria: "Hinta", market_focus: "changes", period: "2023–2026" });
  expect(readDraft()).toMatchObject({ demand_region: "Suomi", payer: "Omainen", criteria: "Hinta", market_focus: "changes", period: "2023–2026" });
  sessionStorage.clear();
});
