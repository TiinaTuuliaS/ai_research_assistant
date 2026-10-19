import { compactCitations, stepText } from "./reportFormatting";

test("stored structured observations are readable without private passages", () => {
  const output = stepText(JSON.stringify({ accepted_findings: [{ title: "Palvelu", summary: "Yritys tarjoaa apua.", source: "https://example.test/", supporting_text: "PRIVATE PASSAGE", limitations: ["Kysyntä ei selviä."] }] }));
  expect(output).toContain("### Palvelu");
  expect(output).toContain("Kysyntä ei selviä.");
  expect(output).not.toContain("PRIVATE PASSAGE");
  expect(output).not.toContain("accepted_findings");
});

test("stored structured analysis shows statements and uncertainty", () => {
  const output = stepText(JSON.stringify({ answer: { statement: "Ehdollinen vastaus.", uncertainty: "Rajattu näyttö." }, conclusions: [], recommendation: "Selvitä käyttö.", gaps: ["Käyttöaste"] }));
  expect(output).toContain("Ehdollinen vastaus.");
  expect(output).toContain("Rajattu näyttö.");
  expect(stepText("## Vanha raportti\n\nTeksti.")).toBe("## Vanha raportti\n\nTeksti.");
});

test("long inline titles become stable numbered citations with matching bibliography", () => {
  const output = compactCitations("Väite [Pitkä otsikko](https://one.test/). Toinen [Toinen](https://two.test/) [Sama](https://one.test/).\n\n## Lähteet\n\n- [Toinen](https://two.test/)\n- [Pitkä otsikko](https://one.test/)");
  expect(output).toContain("Väite [1](https://one.test/).");
  expect(output).toContain("[2](https://two.test/) [1](https://one.test/)");
  expect(output).toContain("[2. Toinen](https://two.test/)");
  expect(output).toContain("[1. Pitkä otsikko](https://one.test/)");
});
