import ReportMarkdown from "./ReportMarkdown";
import reports from "../data/exampleReports.json";

export default function ExampleReport() {
  return <section id="esimerkki" className="example-section">
    <div className="section-heading">
      <p className="eyebrow">Oikeat esimerkkiraportit</p>
      <h2>Tutustu tutkimusten tuloksiin</h2>
      <p>Kaksi sovelluksella tuotettua raporttia kokonaisuudessaan, alkuperäisine teksteineen ja lähteineen. Luettavissa ilman tunnusta.</p>
      <p>Kokeellisen tekoälysovelluksen raportit voivat sisältää virheitä. Esimerkkejä ei ole erikseen faktantarkistettu.</p>
    </div>
    {reports.map(report => <details key={report.id} className="panel example-report">
      <summary><span><span className="tag">{report.type}</span><strong>{report.title}</strong><span>{report.area} · {report.date} · Avaa koko raportti</span></span><span aria-hidden="true">＋</span></summary>
      <div className="example-context">
        <h3>Tutkimuksen lähtötiedot</h3>
        <p>{report.question}</p>
        <p>Alue: {report.area} · Luotu: {report.date}</p>
      </div>
      <article className="report-body" aria-label={report.title}>
        <ReportMarkdown>{report.content}</ReportMarkdown>
      </article>
    </details>)}
    <a className="button primary" href="#tutkimus">Valmistele oma tutkimus ↑</a>
  </section>;
}
