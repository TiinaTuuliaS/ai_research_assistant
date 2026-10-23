import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import ResearchReport from "./ResearchReport";
import ReportActions from "./ReportActions";
import PartialResults from "./PartialResults";
import { useLocation } from "react-router-dom";
import { api } from "../api";

function ResearchDate({ value }) {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) {
    return <p>Tutkimuspäivämäärää ei ole tallennettu.</p>;
  }
  return <p>Tutkimus aloitettu: <time dateTime={value}>{date.toLocaleString("fi-FI", {
    day: "numeric", month: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
  })}</time></p>;
}

function History({ user }) {
  const [researches, setResearches] = useState([]);
  const [selected, setSelected] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const userId = user?.user_id;
  const requestedId = useLocation().state?.researchId;
  const completed = researches.filter(r => !r.status || r.status === "completed").sort((a, b) => b.id - a.id);
  const limited = researches.filter(r => r.status === "limited").sort((a, b) => b.id - a.id);
  const unfinished = researches.filter(r => r.status && !["completed", "limited"].includes(r.status));

  // 🔥 AINA HOOKIT ENSIN
  useEffect(() => {
    if (!userId) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setResearches([]);
    setSelected(null);
    api("/researches", { signal: controller.signal })
      .then(data => {
        if (controller.signal.aborted) return;
        setResearches(data);
        // Only select reports returned by the authenticated server request.
        setSelected(data.find(r => r.id === requestedId) || null);
      })
      .catch(error => {
        if (!controller.signal.aborted) setError(error.message || "Historian haku epäonnistui.");
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [userId, requestedId, attempt]);

  // 🔥 vasta TÄMÄN JÄLKEEN return
  if (!user) {
    return <p style={{ padding: "30px" }}>⚠️ Kirjaudu sisään</p>;
  }

  return (
    <div className="history-page">
      <h1>📜 Omat raportit</h1>
      <button className="button subtle" disabled={loading} onClick={() => setAttempt(n => n + 1)}>Päivitä lista</button>
      {loading && <p role="status">Ladataan historiaa…</p>}
      {error && <p role="alert">{error} <button onClick={() => setAttempt(n => n + 1)}>Yritä uudelleen</button></p>}
      {!loading && !error && researches.length === 0 && <p>Ei vielä tutkimuksia.</p>}

      {/* 🔥 VALITTU */}
      {selected && (
        <div className="history-selected">
          <h2>📄 {selected.topic}</h2>
          <ResearchDate value={selected.created_at} />
          {selected.status && !["completed", "limited"].includes(selected.status)
            ? <PartialResults key={selected.id} initialJob={selected} />
            : <>{selected.status === "limited" && <p className="notice" role="status">Rajattu tulos – loppuraportti ei valmistunut. Kooste sisältää vain valmistuneet havainnot ja mahdollisen analyysin.</p>}<ReportActions key={selected.id} topic={selected.topic} result={selected.result} steps={selected.steps} />
              <ResearchReport result={selected.result} steps={selected.steps} /></>}
        </div>
      )}

      {/* 🔥 LISTA */}
      {[{ title: "Valmiit raportit · uusimmat ensin", items: completed },
        { title: "Rajatut tulokset · loppuraportti ei valmistunut", items: limited },
        { title: "Keskeneräiset tutkimukset ja osatulokset", items: unfinished }].map(group => group.items.length > 0 && (
        <section key={group.title} aria-label={group.title}>
          <h2>{group.title}</h2>
          {group.items.map((r) => (
        <motion.div
          key={r.id}
          className="history-card"
          whileHover={{ scale: 1.02 }}
          onClick={() => setSelected(r)}
          >
          <h3>{r.topic}</h3>
          <ResearchDate value={r.created_at} />
          {r.status && r.status !== "completed" && <p>{r.status === "limited" ? "Rajattu tulos – loppuraportti ei valmistunut" : r.status === "failed" ? "Osatulokset · loppuraportti kesken" : "Tutkimus käynnissä"}</p>}
          <p style={{ color: "var(--accent)" }}>
            Klikkaa avataksesi →
          </p>
        </motion.div>
          ))}
        </section>
      ))}
    </div>
  );
}

export default History;
