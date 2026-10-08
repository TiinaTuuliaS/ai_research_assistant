import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import ResearchReport from "./ResearchReport";
import ReportActions from "./ReportActions";
import PartialResults from "./PartialResults";
import { useLocation } from "react-router-dom";
import { api } from "../api";

function History({ user }) {
  const [researches, setResearches] = useState([]);
  const [selected, setSelected] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const userId = user?.user_id;
  const requestedId = useLocation().state?.researchId;

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
    <div style={styles.page}>
      <h1>📜 Aiemmat haut</h1>
      {loading && <p role="status">Ladataan historiaa…</p>}
      {error && <p role="alert">{error} <button onClick={() => setAttempt(n => n + 1)}>Yritä uudelleen</button></p>}
      {!loading && !error && researches.length === 0 && <p>Ei vielä tutkimuksia.</p>}

      {/* 🔥 VALITTU */}
      {selected && (
        <div style={styles.selectedCard}>
          <h2>📄 {selected.topic}</h2>
          {selected.status && selected.status !== "completed"
            ? <PartialResults key={selected.id} initialJob={selected} />
            : <><ReportActions key={selected.id} topic={selected.topic} result={selected.result} steps={selected.steps} />
              <ResearchReport result={selected.result} steps={selected.steps} /></>}
        </div>
      )}

      {/* 🔥 LISTA */}
      {researches.map((r) => (
        <motion.div
          key={r.id}
          style={styles.card}
          whileHover={{ scale: 1.02 }}
          onClick={() => setSelected(r)}
          >
          <h3>{r.topic}</h3>
          {r.status && r.status !== "completed" && <p>{r.status === "failed" ? "Osatulokset · loppuraportti kesken" : "Tutkimus käynnissä"}</p>}
          <p style={{ color: "var(--accent)" }}>
            Klikkaa avataksesi →
          </p>
        </motion.div>
      ))}
    </div>
  );
}

const styles = {
  page: {
    padding: "30px",
    maxWidth: "800px",
    margin: "auto"
  },

  selectedCard: {
    background: "var(--tint)",
    padding: "20px",
    borderRadius: "12px",
    marginBottom: "20px",
    border: "2px solid var(--secondary)"
  },

  card: {
    background: "var(--surface)",
    padding: "20px",
    borderRadius: "12px",
    marginBottom: "20px",
    boxShadow: "0 5px 15px rgba(0,0,0,0.05)",
    cursor: "pointer"
  }
};

export default History;
