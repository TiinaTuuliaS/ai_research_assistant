import ReactMarkdown from "react-markdown";

export function reportText(result, steps = []) {
  return [...steps.filter(step => step.key !== "writer" && step.output)
    .map(step => `## ${step.label}\n\n${step.output}`), `## Yhdistetty loppuraportti\n\n${result}`].join("\n\n");
}

export default function ResearchReport({ result, steps = [] }) {
  const perspectives = steps.filter(step => step.key !== "writer" && step.output);
  const sourceHeading = /^##\s+(?:Lähteet|Sources)\s*$/im.exec(result || "");
  const body = sourceHeading ? result.slice(0, sourceHeading.index) : result;
  const sources = sourceHeading ? result.slice(sourceHeading.index + sourceHeading[0].length) : "";
  return <div className="report-body">
    <h2>Agenttien näkemykset</h2>
    {perspectives.length ? <>
      <p className="muted">Avaa kunkin agentin oma näkökulma. Näkemykset ovat tekoälyn välituloksia, eivät toisistaan riippumattomia asiantuntija-arvioita.</p>
      {perspectives.map(step => <details className="agent-perspective" key={step.key}>
        <summary>{step.label}<span>{step.description}</span></summary>
        <ReactMarkdown>{step.output}</ReactMarkdown>
      </details>)}
    </> : <p className="muted">Tähän raporttiin ei ole tallennettu agenttikohtaisia näkemyksiä.</p>}
    {body && <section className="final-report"><h2>Yhdistetty loppuraportti</h2><ReactMarkdown>{body}</ReactMarkdown></section>}
    {sources && <section className="report-sources"><h2>Lähteet</h2><ReactMarkdown>{sources}</ReactMarkdown></section>}
  </div>;
}
