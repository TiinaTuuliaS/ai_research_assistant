import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Plans from "./Plans";
import { api } from "../api";
jest.mock("../api", () => ({ api: jest.fn() }));
const base = { id: 1, title: "Oma yritys", version: 1, updated_at: "2026-09-26T12:00:00Z", sections: {
  customer: { title: "Asiakas ja ongelma", content: "", status: "empty" },
  offering: { title: "Tarjottava palvelu", content: "", status: "empty" },
  competition: { title: "Kilpailijat ja erottautuminen", content: "", status: "empty" },
  sales: { title: "Asiakashankinta", content: "", status: "empty" },
  finance: { title: "Alustava talous", content: "", status: "empty" },
  assumptions: { title: "Avoimet oletukset", content: "", status: "empty" },
}, revisions: [] };
beforeEach(() => jest.clearAllMocks());
const show = () => render(<MemoryRouter><Plans user={{ user_id: 1 }} /></MemoryRouter>);
test("creates a plan, saves a draft separately from approval and displays progress", async () => {
  api.mockResolvedValueOnce([]).mockResolvedValueOnce(base);
  show();
  await screen.findByText(/Ei vielä suunnitelmia/);
  fireEvent.change(screen.getByLabelText("Uuden suunnitelman nimi"), { target: { value: "Oma yritys" } });
  fireEvent.click(screen.getByRole("button", { name: "Luo suunnitelma" }));
  const input = await screen.findByLabelText("Omat tiedot ja ajatukset");
  expect(screen.getByRole("button", { name: "Hyväksy osio" })).toBeDisabled();
  fireEvent.change(input, { target: { value: "Pienyritykset" } });
  const draft = { ...base, version: 2, sections: { ...base.sections, customer: { ...base.sections.customer, content: "Pienyritykset", status: "draft" } } };
  api.mockResolvedValueOnce(draft);
  fireEvent.click(screen.getByRole("button", { name: "Tallenna luonnos" }));
  await screen.findByText(/Luonnos tallennettu/);
  expect(screen.getByRole("progressbar")).toHaveAttribute("value", "0");
  api.mockResolvedValueOnce({ ...draft, version: 3, sections: { ...draft.sections, customer: { ...draft.sections.customer, status: "approved" } } });
  fireEvent.click(screen.getByRole("button", { name: "Hyväksy osio" }));
  await screen.findByText("Osio hyväksytty suunnitelmaan.");
  expect(screen.getByRole("progressbar")).toHaveAttribute("value", "1");
  expect(JSON.parse(api.mock.calls[3][1].body)).toMatchObject({ action: "approve", version: 2 });
});
test("preserves edits after a conflicting save", async () => {
  api.mockResolvedValueOnce([base]).mockResolvedValueOnce(base);
  show();
  fireEvent.click(await screen.findByRole("button", { name: /Oma yritys/ }));
  fireEvent.change(await screen.findByLabelText("Omat tiedot ja ajatukset"), { target: { value: "My work" } });
  api.mockRejectedValueOnce(Object.assign(new Error("Version conflict"), { status: 409 }));
  fireEvent.click(screen.getByRole("button", { name: "Tallenna luonnos" }));
  await screen.findByRole("alert");
  expect(screen.getByLabelText("Omat tiedot ja ajatukset")).toHaveValue("My work");
  expect(screen.getByRole("button", { name: "Tallenna luonnos" })).toBeDisabled();
});
test("does not erase an unsaved section when switching is cancelled", async () => {
  api.mockResolvedValueOnce([base]).mockResolvedValueOnce(base);
  const confirm = jest.spyOn(window, "confirm").mockReturnValue(false);
  show();
  fireEvent.click(await screen.findByRole("button", { name: /Oma yritys/ }));
  fireEvent.change(await screen.findByLabelText("Omat tiedot ja ajatukset"), { target: { value: "Unsaved" } });
  fireEvent.click(screen.getByRole("button", { name: /2. Tarjottava palvelu/ }));
  await waitFor(() => expect(confirm).toHaveBeenCalled());
  expect(screen.getByLabelText("Omat tiedot ja ajatukset")).toHaveValue("Unsaved");
  confirm.mockRestore();
});
