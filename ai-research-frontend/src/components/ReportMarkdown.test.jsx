import { render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import ReportMarkdown from "./ReportMarkdown";
import ResearchReport from "./ResearchReport";
import fixture from "./__fixtures__/restaurant-table.json";

test("saved report table becomes semantic rows, headers and source links", () => {
  render(<ResearchReport result={`## Vertailu\n\n${fixture.table}\n\n## Lähteet\n`} />);
  const table = screen.getByRole("table");
  expect(within(table).getAllByRole("columnheader")).toHaveLength(4);
  expect(within(table).getAllByRole("row")).toHaveLength(4);
  for (const name of ["Daiwo Sushi", "Itsuyaki", "Itsudemo"]) expect(within(table).getByText(name)).toBeInTheDocument();
  expect(within(table).getAllByRole("link").length).toBeGreaterThan(0);
  expect(screen.getByRole("region", {name: "Raportin taulukko"})).toHaveAttribute("tabindex", "0");
});

test("the shared renderer also emits a real table in print markup", () => {
  const html = renderToStaticMarkup(<ReportMarkdown>{fixture.table}</ReportMarkdown>);
  expect(html).toContain("<table>");
  expect(html).toContain("<thead>");
  expect(html).toContain("<tbody>");
  expect(html).toContain('href="https://daiwosushi.fi/tampere/"');
});

test("ordinary Markdown and verbatim code retain their meaning", () => {
  render(<ReportMarkdown>{"## Otsikko\n\nTavallinen kappale.\n\n```text\n| code | stays |\n```"}</ReportMarkdown>);
  expect(screen.getByRole("heading", {name: "Otsikko"})).toBeInTheDocument();
  expect(screen.getByText("Tavallinen kappale.")).toBeInTheDocument();
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
  expect(screen.getByText("| code | stays |")).toBeInTheDocument();
});
