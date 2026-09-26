import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import { emptyDraft } from "./researchDraft";
import { researchPayload } from "./researchTypes";
jest.mock("react-markdown", () => ({ children }) => <div>{children}</div>);
function Form() {
  const [draft, setDraft] = useState(emptyDraft);
  return <MemoryRouter><Dashboard draft={draft} setDraft={setDraft} /></MemoryRouter>;
}
test("choices change fields and preserve each mode's unfinished answers", () => {
  render(<Form />);
  fireEvent.change(screen.getByLabelText("Mikä on ideasi?"), { target: { value: "Oma idea" } });
  fireEvent.click(screen.getByRole("button", { name: /Miten erotun kilpailijoista/ }));
  expect(screen.queryByLabelText("Mikä on ideasi?")).not.toBeInTheDocument();
  expect(screen.getByLabelText(/Tunnetut kilpailijat/)).not.toBeRequired();
  fireEvent.click(screen.getByRole("button", { name: /Mitä tällä markkinalla tapahtuu/ }));
  expect(screen.getByLabelText("Mitä aluetta tarkastellaan?")).toBeRequired();
  fireEvent.click(screen.getByRole("button", { name: /Onko idealleni kysyntää/ }));
  expect(screen.getByLabelText("Mikä on ideasi?")).toHaveValue("Oma idea");
});
test("only the selected mode's context reaches the server", () => {
  const draft = { ...emptyDraft, research_type: "competition", solution: "Palvelu", competition_market: "Suomi", competitors: "Yritys A", problem: "Hidden demand context", question: "Hidden market context" };
  expect(researchPayload(draft)).toMatchObject({ research_type: "competition", topic: "Palvelu", target_market: "Suomi", competitors: "Yritys A", problem: "", goal: "", budget_eur: null });
});
