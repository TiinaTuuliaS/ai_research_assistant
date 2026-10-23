import { render, screen, within } from "@testing-library/react";
import ExampleReport from "./ExampleReport";

test("public examples show both full reports with their original table and sources", () => {
  render(<ExampleReport />);
  const renovation = screen.getByRole("article", {name: "Remonttifirmojen vertailu Tampereen seudulla", hidden: true});
  const energy = screen.getByRole("article", {name: "Uusiutuvan energian käyttö Suomessa", hidden: true});
  expect(within(renovation).getByRole("table", {hidden: true})).toBeInTheDocument();
  expect(within(renovation).getAllByRole("link", {hidden: true}).some(link => link.href === "https://airuremontit.fi/arvostelut/")).toBe(true);
  expect(energy).toHaveTextContent("Keskeiset ilmiöt ja investoinnit");
  expect(within(energy).getAllByRole("link", {hidden: true}).some(link => link.href.includes("motiva.fi"))).toBe(true);
  expect(screen.getByText(/Luettavissa ilman tunnusta/)).toBeInTheDocument();
});
