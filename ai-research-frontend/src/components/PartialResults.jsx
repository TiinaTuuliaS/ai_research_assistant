import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "../api";
import AgentProgress from "./AgentProgress";
import ResearchReport from "./ResearchReport";
import ReportActions from "./ReportActions";

export default function PartialResults({ initialJob }) {
  const [job, setJob] = useState(initialJob);
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const results = useRef(null);
  const request = useRef(null);
  const id = initialJob.job_id || initialJob.id;
  const active = ["queued", "running"].includes(job.status);
  const done = (job.steps || []).filter(s => s.status === "completed").length;
  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    let timer;
    const poll = async () => {
      try {
        const next = await api(`/research-jobs/${id}`, { signal: controller.signal });
        if (controller.signal.aborted) return;
        setJob(next); setError("");
        if (["queued", "running"].includes(next.status)) timer = setTimeout(poll, 1000);
      } catch (e) {
        if (!controller.signal.aborted) setError("Seuranta katkesi. Voit jatkaa seurantaa; tutkimusta ei käynnistetä uudelleen.");
      }
    };
    poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [active, id, attempt]);
  const retry = async () => {
    if (sending || active) return;
    const controller = new AbortController();
    request.current = controller;
    setSending(true); setError("");
    try {
      const next = await api(`/research-jobs/${id}/retry-report`, { method: "POST", signal: controller.signal });
      if (!controller.signal.aborted) setJob(next);
    } catch (e) {
      if (!controller.signal.aborted) setError(e.message);
    } finally { if (!controller.signal.aborted) setSending(false); }
  };
  if (job.status === "completed") return <section className="panel result-section">
    <h2>Loppuraportti valmistui</h2>
    <ReportActions topic={job.topic} result={job.result} steps={job.steps} />
    <ResearchReport result={job.result} steps={job.steps} />
  </section>;
  return <section className="panel result-section" aria-label="Tutkimuksen osatulokset">
    <h2>{job.topic}</h2>
    <p role="status">Tutkimuksesta valmistui {done}/{job.steps?.length || 5} vaihetta.</p>
    <p>{active ? "Loppuraporttia viimeistellään. Tallennetut välitulokset ovat luettavissa alla."
      : job.validation_error || job.error || "Loppuraportti jäi kesken."}</p>
    {job.partial_result ? <>
      <p>Valmistuneet tulokset ovat tallessa omissa raporteissasi. Kooste on keskeneräinen, eikä sen väitteitä ole vahvistettu loppuanalyysissä.</p>
      <button className="button subtle" onClick={() => results.current?.scrollIntoView?.({ behavior: "smooth", block: "start" })}>Lue valmistuneet tulokset</button>
    </> : <p>Tutkimuksesta ei valmistunut luettavia välituloksia.</p>}
    {job.can_retry_report && <>
      <button className="button primary" disabled={sending} onClick={retry}>{sending ? "Käynnistetään…" : "Korjaa loppuraportti"}</button>
      <p className="field-help">Tallennettuun luonnokseen tehdään kohdistettu korjaus hylkäyssyyn ja lähteiden perusteella. Tämä ei kuluta uutta tutkimuskertaa.</p>
    </>}
    {!active && !job.can_retry_report && <p className="field-help">Pelkkää loppuraporttia ei voi uusia, koska tarvittavat välitulokset, luonnos tai korjaustiedot puuttuvat.</p>}
    {error && <p role="alert">{error}{active && <button onClick={() => setAttempt(n => n + 1)}>Jatka seurantaa</button>}</p>}
    {active && <AgentProgress job={job} />}
    {job.partial_result && <div ref={results} className="report-body" tabIndex={-1}>
      <ReportActions topic={job.topic} result={job.partial_result} partial />
      <ReactMarkdown>{job.partial_result}</ReactMarkdown>
    </div>}
    {job.draft && <details className="agent-perspective">
      <summary>Tarkistamaton kirjoittajan luonnos</summary>
      <p>Luonnos ei läpäissyt kaikkia tarkistuksia. Se voi sisältää virheellisiä väitteitä tai puuttuvia lähdeviitteitä.</p>
      <ReactMarkdown>{job.draft}</ReactMarkdown>
    </details>}
  </section>;
}
