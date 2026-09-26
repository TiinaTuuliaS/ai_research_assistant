import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const statuses = { empty: "Aloittamatta", draft: "Luonnos", approved: "Hyväksytty", review: "Tarkistettava" };
const guidance = {
  customer: "Kenelle palvelusi on tarkoitettu? Kuvaile asiakkaan ongelma ja nykyinen tapa ratkaista se.",
  offering: "Mitä asiakas saa sinulta konkreettisesti? Kerro myös osaamisestasi ja rajaa, mitä palveluun ei kuulu.",
  competition: "Mitä vaihtoehtoja asiakkaalla jo on? Miten ratkaisusi eroaisi niistä asiakkaalle tärkeällä tavalla?",
  sales: "Mistä tavoitat ensimmäiset asiakkaat ja miten esittelet palvelusi? Valitse aluksi yksi realistinen kanava.",
  finance: "Kirjaa alustava hintasi, arvioitu myyntimäärä ja tärkeimmät kulut. Merkitse arviot oletuksiksi. Tässä vaiheessa summia ei lasketa automaattisesti.",
  assumptions: "Mitä et vielä tiedä? Kirjaa tärkeimmät oletukset ja millainen tieto voisi muuttaa suunnitelmaasi.",
};
const count = plan => Object.values(plan.sections).filter(s => s.status === "approved").length;
const date = value => new Date(value).toLocaleString("fi-FI");

export default function Plans({ user }) {
  const [items, setItems] = useState([]);
  const [plan, setPlan] = useState(null);
  const [title, setTitle] = useState("");
  const [section, setSection] = useState("customer");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [retry, setRetry] = useState(0);
  const [conflict, setConflict] = useState(false);
  const alive = useRef(true);
  const dirty = !!plan && content !== plan.sections[section].content;
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    api("/plans", { signal: controller.signal }).then(data => {
      if (!controller.signal.aborted) setItems(data);
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [user.user_id, retry]);
  useEffect(() => {
    if (!dirty) return;
    const warn = event => { event.preventDefault(); event.returnValue = ""; };
    const navigate = event => {
      if (event.target.closest("a[href]") && !window.confirm("Sinulla on tallentamattomia muutoksia. Poistutaanko tallentamatta?")) {
        event.preventDefault(); event.stopPropagation();
      }
    };
    window.addEventListener("beforeunload", warn);
    document.addEventListener("click", navigate, true);
    return () => { window.removeEventListener("beforeunload", warn); document.removeEventListener("click", navigate, true); };
  }, [dirty]);
  const discard = () => !dirty || window.confirm("Hylätäänkö tämän osion tallentamattomat muutokset?");
  const adopt = (data, key = "customer") => {
    setPlan(data); setSection(key); setContent(data.sections[key].content); setConflict(false);
    setItems(previous => [data, ...previous.filter(item => item.id !== data.id)]);
  };
  const request = async (work, success) => {
    setBusy(true); setError(""); setNotice("");
    try { const data = await work(); if (alive.current) success(data); }
    catch (e) { if (alive.current) { setError(e.message); setConflict(e.status === 409); } }
    finally { if (alive.current) setBusy(false); }
  };
  const open = id => { if (discard()) request(() => api(`/plans/${id}`), data => adopt(data)); };
  const save = action => request(() => api(`/plans/${plan.id}/sections/${section}`, {
    method: "POST", body: JSON.stringify({ content, action, version: plan.version }),
  }), data => { adopt(data, section); setNotice(action === "approve" ? "Osio hyväksytty suunnitelmaan." : "Luonnos tallennettu. Myöhempien osioiden tarkistustarve on päivitetty."); });

  return <main className="plans-page">
    <p className="eyebrow">Omat sivut</p><h1>Yritysideasta suunnitelmaksi</h1>
    <p>Rakenna suunnitelmaa omaan tahtiisi. Tallenna keskeneräinen ajatus ja hyväksy osio, kun haluat käyttää sitä suunnitelmasi lähtökohtana.</p>
    <p><Link to="/history">Avaa aiemmat tutkimusraportit →</Link></p>
    <form className="panel plan-create" onSubmit={event => {
      event.preventDefault(); if (busy || !discard()) return;
      request(() => api("/plans", { method: "POST", body: JSON.stringify({ title }) }), data => { adopt(data); setTitle(""); });
    }}>
      <label htmlFor="plan-title">Uuden suunnitelman nimi</label>
      <input id="plan-title" value={title} maxLength={160} required onChange={e => setTitle(e.target.value)} placeholder="Esim. Oma ohjelmistopalvelu" disabled={busy} />
      <button className="button primary" disabled={busy || !title.trim()}>Luo suunnitelma</button>
      <p className="field-help">Luominen ja muokkaaminen eivät käytä tekoälyä tai aiheuta AI-kuluja.</p>
    </form>
    {loading && <p role="status">Ladataan suunnitelmia…</p>}
    {error && <p className="error" role="alert">{error} {conflict ? <button onClick={() => open(plan.id)} disabled={busy}>Avaa ajantasainen versio</button> : !plan && <button onClick={() => setRetry(n => n + 1)}>Hae suunnitelmat uudelleen</button>}</p>}
    {notice && <p role="status">{notice}</p>}
    {!loading && !items.length && !error && <p>Ei vielä suunnitelmia. Anna ideallesi nimi ja aloita asiakkaasta ja ongelmasta.</p>}
    <div className="plan-list">{items.map(item => <button className={`plan-card ${plan?.id === item.id ? "selected" : ""}`} key={item.id} onClick={() => open(item.id)} disabled={busy} aria-pressed={plan?.id === item.id}>
      <strong>{item.title}</strong><span>{count(item)} / 6 osiota hyväksytty</span><small>Päivitetty {date(item.updated_at)}</small>
    </button>)}</div>
    {plan && <>
      <section className="panel plan-workspace">
        <h2>{plan.title}</h2><p>{count(plan)} / 6 osiota hyväksytty</p>
        <progress aria-label="Suunnitelman hyväksytyt osiot" value={count(plan)} max="6" />
        <p className="field-help">Eteneminen kuvaa omia hyväksyntöjäsi, ei liikeidean kannattavuutta. Aiemman osion muutos merkitsee myöhemmät hyväksytyt osiot tarkistettaviksi.</p>
        {count(plan) === 6 && <p className="notice">Kaikki osiot on hyväksytty. Suunnitelmasi ensimmäinen versio on koossa — voit jatkaa sen kehittämistä.</p>}
        <div className="plan-sections" role="group" aria-label="Suunnitelman osiot">{Object.entries(plan.sections).map(([key, value], index) => <button type="button" key={key} disabled={busy} aria-pressed={section === key} onClick={() => {
          if (key !== section && discard()) { setSection(key); setContent(value.content); setNotice(""); }
        }}><strong>{index + 1}. {value.title}</strong><span>{statuses[value.status]}</span></button>)}</div>
        <form onSubmit={event => { event.preventDefault(); if (!busy) save("save"); }}>
          <h3>{plan.sections[section].title}</h3><p id="section-help">{guidance[section]}</p>
          {plan.sections[section].status === "review" && <p className="notice">Aiemmat lähtötiedot muuttuivat. Tarkista sisältö ja hyväksy osio uudelleen.</p>}
          <label htmlFor="section-content">Omat tiedot ja ajatukset</label>
          <textarea id="section-content" aria-describedby="section-help" rows={9} maxLength={12000} value={content} disabled={busy} onChange={e => setContent(e.target.value)} />
          <p className="field-help">{dirty ? "Tallentamattomia muutoksia" : "Tallennettu versio"} · {content.length} / 12 000 merkkiä. Erota omat tietosi vielä testaamattomista oletuksista.</p>
          <div className="actions"><button className="button subtle" disabled={busy || !dirty || conflict}>Tallenna luonnos</button>
            <button className="button primary" type="button" disabled={busy || !content.trim() || conflict || (!dirty && plan.sections[section].status === "approved")} onClick={() => save("approve")}>Hyväksy osio</button></div>
        </form>
      </section>
      <section className="panel plan-workspace"><h2>Rakentuva kokonaisuus</h2><p>Alla ovat tallennetut osiot. Luonnokset ja tarkistettavat kohdat eivät vielä ole hyväksyttyjä lähtötietoja.</p>
        {Object.entries(plan.sections).map(([key, value]) => <article key={key}><h3>{value.title} <small>· {statuses[value.status]}</small></h3><p className="plan-text">{value.content || "Tämä osio odottaa vielä ajatuksiasi."}</p></article>)}
      </section>
      <section className="panel plan-workspace"><h2>Suunnitelman kehityshistoria</h2><p>Viimeisimmät 50 tallennettua versiota. Avaa tapahtuma nähdäksesi suunnitelman siinä vaiheessa.</p>
        {plan.revisions?.map(revision => <details key={revision.version}><summary>Versio {revision.version} · {revision.description} · {date(revision.created_at)}</summary>
          {Object.entries(revision.sections).map(([key, value]) => <div key={key}><h3>{value.title} · {statuses[value.status]}</h3><p className="plan-text">{value.content || "Ei vielä sisältöä."}</p></div>)}
        </details>)}
      </section>
    </>}
  </main>;
}
