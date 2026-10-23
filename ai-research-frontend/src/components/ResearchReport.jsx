import ReportMarkdown from "./ReportMarkdown";
import { compactCitations, stepText } from "./reportFormatting";

export function reportText(result, steps = []) {
  return [...steps.filter(step => step.key !== "writer" && step.output)
    .map(step => `## ${step.label}\n\n${stepText(step.output)}`), `## Yhdistetty loppuraportti\n\n${compactCitations(result)}`].join("\n\n");
}

export default function ResearchReport({ result, steps = [] }) {
  const perspectives = steps.filter(step => step.key !== "writer" && step.output);
  result = compactCitations(result);
  const sourceHeading = /^##\s+(?:Lähteet|Sources)\s*$/im.exec(result || "");
  const body = sourceHeading ? result.slice(0, sourceHeading.index) : result;
  const sources = sourceHeading ? result.slice(sourceHeading.index + sourceHeading[0].length) : "";
  return <div className="report-body">
    <h2>Agenttien näkemykset</h2>
    {perspectives.length ? <>
      <p className="muted">Avaa kunkin agentin oma näkökulma. Näkemykset ovat tekoälyn välituloksia, eivät toisistaan riippumattomia asiantuntija-arvioita.</p>
      {perspectives.map(step => <details className="agent-perspective" key={step.key}>
        <summary>{step.label}<span>{step.description}</span></summary>
        <ReportMarkdown>{stepText(step.output)}</ReportMarkdown>
      </details>)}
    </> : <p className="muted">Tähän raporttiin ei ole tallennettu agenttikohtaisia näkemyksiä.</p>}
    {body && <section className="final-report"><h2>Yhdistetty loppuraportti</h2><ReportMarkdown>{body}</ReportMarkdown></section>}
    {sources && <section className="report-sources"><h2>Lähteet</h2><ReportMarkdown>{sources}</ReportMarkdown></section>}
  </div>;
}
