import { useEffect, useRef, useState } from "react";
import ResearchReport from "./ResearchReport";
import ReportActions from "./ReportActions";
import AgentProgress from "./AgentProgress";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import ExampleReport from "./ExampleReport";

import { researchTypes, selectedType, researchPayload } from "../researchTypes";

export default function Dashboard({ user, setUser, checking, draft, setDraft }) {
  const navigate = useNavigate();
  const type = selectedType(draft);
  const [result, setResult] = useState("");
  const [reportTopic, setReportTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const request = useRef(null);
  const [job, setJob] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [pollAttempt, setPollAttempt] = useState(0);
  const [connectionError, setConnectionError] = useState("");
  const [quota, setQuota] = useState(user?.quota);
  useEffect(() => { setQuota(user?.quota); }, [user]);
  const quotaExhausted = !!user && quota?.remaining === 0;
  const userId = user?.user_id;
  useEffect(() => {
    if (quota && setUser) setUser(current => current?.user_id === userId && current.quota !== quota
      ? { ...current, quota } : current);
  }, [quota, userId, setUser]);
  const storageKey = `research-job-${userId}`;
  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => {
    request.current?.abort();
    setResult(""); setJob(null); setError(""); setLoading(false);
    setConnectionError("");
    setJobId(userId ? sessionStorage.getItem(`research-job-${userId}`) : null);
  }, [userId]);
  useEffect(() => {
    if (!jobId || !userId) return;
    const controller = new AbortController();
    let timer;
    setLoading(true); setConnectionError("");
    const poll = async () => {
      try {
        const data = await api(`/research-jobs/${jobId}`, { signal: controller.signal });
        if (controller.signal.aborted) return;
        setJob(data);
        if (data.quota) setQuota(data.quota);
        if (data.status === "completed" || data.status === "failed") {
          sessionStorage.removeItem(storageKey); setJobId(null); setLoading(false);
          if (data.status === "completed") { setResult(data.result); setReportTopic(data.topic); }
          else setError(data.error || "Tutkimus keskeytyi.");
        } else timer = setTimeout(poll, 1000);
      } catch (error) {
        if (controller.signal.aborted) return;
        if (error.status === 404) {
          sessionStorage.removeItem(storageKey); setJobId(null); setLoading(false);
          setError("Tutkimusta ei löytynyt.");
        } else setConnectionError("Edistymisen haku katkesi. Tutkimus voi silti jatkua palvelimella.");
      }
    };
    poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [jobId, userId, storageKey, pollAttempt]);
  const field = name => ({ value: draft[name] || "", onChange: e => setDraft({ ...draft, [name]: e.target.value }) });

  const runResearch = async event => {
    event.preventDefault();
    if (loading || checking || quotaExhausted) return;
    if (!user) { navigate("/login"); return; }
    const controller = new AbortController();
    request.current = controller;
    setLoading(true); setError(""); setResult(""); setJob(null);
    try {
      const data = await api("/research-jobs", {
        method: "POST", signal: controller.signal,
        body: JSON.stringify(researchPayload(draft)),
      });
      if (!controller.signal.aborted) {
        if (data.quota) setQuota(data.quota);
        sessionStorage.setItem(storageKey, data.id); setJob(data); setJobId(data.id);
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        if (error.quota) setQuota(error.quota);
        setError(error.message || "Tutkimus epäonnistui. Yritä uudelleen."); setLoading(false);
      }
    }
  };

  return <main className="landing">
    <section className="hero">
      <div className="hero-copy">
        <h1>🤖 AI Markkinatutkimusassistentti</h1>
        <p className="lead">Tutki markkinoita eri näkökulmista. Viisi tekoälyagenttia kokoaa havainnot, punnitsee niiden merkityksen ja tiivistää vastauksen kysymykseesi.</p>
        <a className="text-link" href="#esimerkki">Katso esimerkkiraportti ilman tunnusta ↗</a>
        <div className="agent-badges" aria-label="Tutkimuksen vaiheet"><span>🔍 Tutkimus</span><span>📈 Trendit</span><span>📊 Analyysi</span><span>🧠 Strategia</span><span>✍️ Raportti</span></div>
      </div>
      <form id="tutkimus" className="panel research-form" onSubmit={runResearch}>
        <p className="eyebrow">Sinun lähtökohtasi</p>
        <h2>Mitä haluat selvittää?</h2>
        <p className="muted">Valitse kysymys, johon tarvitset vastauksen. Jokainen vaihtoehto painottaa tutkimusta eri tavalla.</p>
        <fieldset disabled={loading}>
          <legend className="sr-only">Tutkimuksen tiedot</legend>
          <div className="research-types" role="group" aria-label="Tutkimuksen tyyppi">
            {researchTypes.map(option => <button type="button" key={option.id}
              className={`research-type ${type.id === option.id ? "selected" : ""}`}
              aria-pressed={type.id === option.id}
              onClick={() => setDraft({ ...draft, research_type: option.id })}>
              <span className="research-type-icon" aria-hidden="true">{option.icon}</span>
              <strong>{option.title}</strong><span>{option.description}</span>
              <span className="selection-mark">{type.id === option.id ? "✓ Valittu" : "Valitse"}</span>
            </button>)}
          </div>
          <div className="research-type-fields" key={type.id}>
            <h3>{type.title}</h3><p className="field-help">{type.outcome}</p>
            {type.fields.map(input => <div key={input.name}>
              <label htmlFor={input.name}>{input.label}{input.optional && <span className="optional"> · valinnainen</span>}</label>
              {input.multiline
                ? <textarea id={input.name} rows={3} required={!input.optional} maxLength={input.max} placeholder={input.placeholder} {...field(input.name)} />
                : <input id={input.name} required={!input.optional} maxLength={input.max} placeholder={input.placeholder} {...field(input.name)} />}
            </div>)}
          </div>
          <details className="research-extras"><summary>Lisätiedot · valinnainen budjetti</summary>
          <label htmlFor="budget">Kokeilubudjetti (€) <span className="optional">valinnainen</span></label>
          <input id="budget" type="number" min="0" max="10000000" step="0.01" placeholder="Esim. 150" aria-describedby="budget-help" {...field("budget_eur")} />
          <p id="budget-help" className="field-help">0 € tarkoittaa kokeilua ilman ostoja. Tyhjä kenttä jättää budjetin avoimeksi.</p>
          </details>
          <p className="field-help" aria-live="polite">
            {user && quota?.unlimited ? "Ylläpitäjätili: rajattomat tutkimukset."
              : user && quota ? `Tutkimuksia jäljellä: ${quota.remaining} / ${quota.limit}.` : "Jokaisella käyttäjätilillä voi tehdä yhteensä kolme tutkimusta."}
            {!quota?.unlimited && " Aloitettu tutkimus kuluttaa yhden käyttökerran myös keskeytyessään."}
          </p>
          {quotaExhausted && <p>Tilisi tutkimukset on käytetty. <Link to="/history">Avaa omat raportit →</Link></p>}
          <button className="button primary full-width" disabled={loading || checking || quotaExhausted}>
            {loading ? "Tutkimus käynnissä…" : checking ? "Tarkistetaan kirjautumista…" : quotaExhausted ? "Tutkimukset käytetty" : user ? "Aloita tutkimus →" : "Kirjaudu ja jatka tutkimukseen →"}
          </button>
        </fieldset>
        <p className="field-help">{user ? "Raportti tallentuu omiin raportteihisi." : "Sivuun ja esimerkkiin voi tutustua vapaasti. Oman tutkimuksen tekeminen vaatii tilin."}</p>
        {error && <p role="alert" className="error">{error}</p>}
        {loading && !job && <p role="status">Käynnistetään tutkimusta…</p>}
        {connectionError && <p role="alert">{connectionError} <button type="button" onClick={() => setPollAttempt(n => n + 1)}>Jatka edistymisen seurantaa</button></p>}
        {job && <AgentProgress job={job} />}
      </form>
    </section>

    {job?.status === "failed" && job.steps?.some(step => step.output) && <section className="panel result-section">
      <h2>Tutkimuksen valmistuneet välitulokset</h2><p>Loppuraportti jäi kesken. Nämä ovat valmistuneiden agenttien vastauksia, eivät tarkistettu loppuraportti.</p>
      <ResearchReport result="" steps={job.steps} />
    </section>}
    {result && <section className="panel result-section" aria-label="Tutkimusraportti">
      <div className="result-header"><div><p className="eyebrow">Tutkimuksesi on valmis</p><h2>{reportTopic}</h2></div>
      </div>
      <ReportActions topic={reportTopic} result={result} steps={job?.steps} />
      <ResearchReport result={result} steps={job?.steps} />
      <Link className="text-link" to="/history">Avaa omat raportit →</Link>
    </section>}

    <section className="value-grid" aria-label="Raportin sisältö">
      <article><span className="step-number">01</span><h2>Agenttien näkemykset</h2><p>Tutkija, trendianalyytikko, markkina-analyytikko ja strategi tuovat esiin omat havaintonsa.</p></article>
      <article><span className="step-number">02</span><h2>Yhdistetty loppuraportti</h2><p>Kirjoittaja kokoaa olennaisen: mitä tiedetään, mitä voi päätellä ja mikä on vielä epävarmaa.</p></article>
      <article><span className="step-number">03</span><h2>Lähteet näkyvillä</h2><p>Tarkista havaintojen lähteet ja arvioi, kuinka hyvin aineisto vastaa kysymykseesi.</p></article>
    </section>
    <ExampleReport />
    <section className="method-note"><h2>Mihin raportti perustuu?</h2><p>Agentit työskentelevät peräkkäin ja hyödyntävät aiempien vaiheiden tuloksia. Aineistona ovat verkkohakujen katkelmat. Loppuraportti erottaa lähteistetyt havainnot, tulkinnat ja avoimet kysymykset.</p></section>
  </main>;
}
