import React, { useState } from "react";
import { motion } from "framer-motion";
import Confetti from "react-confetti";
import ReactMarkdown from "react-markdown";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

function Dashboard({ user }) {
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState("");
  const [reportTopic, setReportTopic] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [researches, setResearches] = useState([]);
  const [showConfetti, setShowConfetti] = useState(false);

  const [activeAgent, setActiveAgent] = useState(0);

  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [typingDots, setTypingDots] = useState("");

  const navigate = useNavigate();

  if (!user) {
    return (
      <p style={{ padding: "30px" }}>
        ⚠️ Kirjaudu uudelleen
      </p>
    );
  }

  // 🤖 AGENTIT
  const agents = [
    {
      name: "🔍 Research Agent",
      text:
        "Etsii markkinadataa, kilpailijoita ja relevantteja lähteitä"
    },
    {
      name: "📈 Trend Agent",
      text:
        "Etsii verkosta julkaistua tietoa nousevista trendeistä"
    },
    {
      name: "📊 Analyst Agent",
      text:
        "Vertaa kilpailijoita ja tunnistaa mahdollisuuksia"
    },
    {
      name: "🧠 Strategy Agent",
      text:
        "Rakentaa strategisia ehdotuksia"
    },
    {
      name: "✍️ Writer Agent",
      text:
        "Kirjoittaa lopullista raporttia"
    }
  ];

  // 🚀 RUN RESEARCH
  const runResearch = async () => {
    if (!topic.trim() || loading) return;

    setLoading(true);
    setResult("");
    setError("");
    setReportTopic(topic.trim());

    setActiveAgent(0);
    setProgress(0);
    setLogs([]);

    // 🔥 typing dots animation
    const dotsInterval = setInterval(() => {
      setTypingDots(prev => {
        if (prev.length >= 3) return "";
        return prev + ".";
      });
    }, 500);

    // 🔥 vaiheiden päivitys
    const updateStep = (index, percent, log) => {
      setActiveAgent(index);
      setProgress(percent);

      setLogs(prev => [...prev, log]);
    };

    // 🔍 vaihe 1
    updateStep(
      0,
      15,
      "🔍 Research Agent analysoi markkinadataa ja etsii relevantteja lähteitä"
    );

    // 📈 vaihe 2
    const t1 = setTimeout(() => {
      updateStep(
        1,
        35,
        "📈 Trend Agent tunnistaa kasvavia trendejä hakudatasta ja somesignaaleista"
      );
    }, 2000);

    // 📊 vaihe 3
    const t2 = setTimeout(() => {
      updateStep(
        2,
        55,
        "📊 Analyst Agent vertailee kilpailijoita ja markkinamahdollisuuksia"
      );
    }, 4000);

    // 🧠 vaihe 4
    const t3 = setTimeout(() => {
      updateStep(
        3,
        70,
        "🧠 Strategy Agent rakentaa strategisia suosituksia"
      );
    }, 6000);

    // ✍️ vaihe 5
    const t4 = setTimeout(() => {
      updateStep(
        4,
        85,
        "✍️ Writer Agent kirjoittaa lopullista raporttia"
      );
    }, 8000);

    try {
      const data = await api(
        "/research",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            topic: topic.trim(),
            language: "suomi"
          })
        }
      );

      setResult(data.result);

      // ✅ valmis
      setProgress(100);

      setLogs(prev => [
        ...prev,
        "✅ Tutkimus valmis"
      ]);

      // 🎉 confetti
      setShowConfetti(true);

      setTimeout(() => {
        setShowConfetti(false);
      }, 4000);

      // 🧹 tyhjennä input
      setTopic("");

    } catch (error) {
      setError(error.message || "Virhe backend-yhteydessä");
    }

    // 🔥 cleanup
    clearTimeout(t1);
    clearTimeout(t2);
    clearTimeout(t3);
    clearTimeout(t4);

    clearInterval(dotsInterval);

    setTypingDots("");

    setLoading(false);
  };

  // 📜 HISTORY
  const fetchResearches = async () => {
    try {
      setError("");
      setResearches(await api("/researches"));
    } catch (error) {
      setError(error.message || "Historian haku epäonnistui.");
    }
  };

  return (
    <div style={styles.page}>

      {/* 🌈 BACKGROUND */}
      <div style={styles.blur1}></div>
      <div style={styles.blur2}></div>

      {/* 🎉 CONFETTI */}
      {showConfetti && (
        <Confetti
          numberOfPieces={250}
          gravity={0.25}
          recycle={false}
        />
      )}

      <div style={styles.container}>

        {/* 🔥 HERO */}
        <h1 style={styles.title}>
          🤖 AI Markkinatutkimusassistentti
        </h1>

        <p style={styles.subtitle}>
          5 AI-agenttia analysoi markkinoita,
          kilpailijoita ja verkosta löytyviä trendejä.
        </p>

        {/* 🔍 SEARCH */}
        <motion.div
          style={styles.card}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >

          <input
            disabled={loading}
            style={styles.input}
            placeholder="Tutki mitä tahansa... (esim. ruokatrendit 2026)"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />

          <motion.button
            disabled={loading || !topic.trim()}
            style={styles.primaryButton}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={runResearch}
          >
            🚀 Suorita tutkimus
          </motion.button>

          {/* 🤖 AGENT BADGES */}
          <div style={styles.agentPreview}>
            <span style={styles.agentBadge}>
              🔍 Research
            </span>

            <span style={styles.agentBadge}>
              📈 Trends
            </span>

            <span style={styles.agentBadge}>
              📊 Analyst
            </span>

            <span style={styles.agentBadge}>
              🧠 Strategy
            </span>

            <span style={styles.agentBadge}>
              ✍️ Writer
            </span>
          </div>

        </motion.div>

        {error && <p role="alert">{error}</p>}
        {loading && <p role="status">Tutkimus käynnissä. Alla oleva eteneminen on arvio, ei reaaliaikainen tilatieto.</p>}
        {/* 📊 PROGRESS BAR */}
        {loading && (
          <div style={styles.progressWrapper}>
            <div
              style={{
                ...styles.progressBar,
                width: `${progress}%`
              }}
            />
          </div>
        )}

        {/* 🔥 LIVE AGENTS */}
        {loading && (
          <motion.div
            style={styles.agentList}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >

            {agents.map((agent, index) => (
              <motion.div
                key={index}
                style={{
                  ...styles.agentItem,
                  background:
                    index === activeAgent
                      ? "rgba(99,102,241,0.12)"
                      : "transparent"
                }}
                animate={{
                  scale:
                    index === activeAgent
                      ? 1.03
                      : 1,

                  opacity:
                    index <= activeAgent
                      ? 1
                      : 0.4
                }}
              >

                <div>
                  <div style={styles.agentName}>
                    {agent.name}
                  </div>

                  <div style={styles.agentDesc}>
                    {index === activeAgent && index === 4
                      ? `Kirjoittaa lopullista raporttia${typingDots}`
                      : agent.text}
                  </div>
                </div>

                <div style={styles.agentStatus}>
                  {index < activeAgent && "✔"}
                  {index === activeAgent && "🔄"}
                </div>

              </motion.div>
            ))}

            {/* 🔥 LOGS */}
            <button
              style={styles.logsButton}
              onClick={() => setShowLogs(!showLogs)}
            >
              {showLogs
                ? "▲ Piilota työvaiheet"
                : "▼ Näytä työvaiheet"}
            </button>

            {showLogs && (
              <div style={styles.logsBox}>

                {logs.map((log, index) => (
                  <div
                    key={index}
                    style={styles.logItem}
                  >
                    {log}
                  </div>
                ))}

              </div>
            )}

          </motion.div>
        )}

        {/* 📄 RESULT */}
        {result && (
          <motion.div
            style={styles.card}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >

            <div style={styles.resultHeader}>

              <h2>📄 Tulokset</h2>

              {/* 📥 PDF */}
              <button
                style={styles.pdfButton}
                onClick={() => {
                  const blob = new Blob([result], {
                    type: "text/plain"
                  });

                  const url =
                    window.URL.createObjectURL(blob);

                  const a =
                    document.createElement("a");

                  a.href = url;

                  a.download =
                    `${reportTopic || "research-report"}.txt`;

                  a.click();

                  window.URL.revokeObjectURL(url);
                }}
              >
                📥 Lataa raportti
              </button>

            </div>

            <div style={styles.result}>
              <ReactMarkdown>
                {result}
              </ReactMarkdown>
            </div>

          </motion.div>
        )}

        {/* 📜 HISTORY */}
        <motion.div
          style={styles.card}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >

          <button
            style={styles.secondaryButton}
            onClick={fetchResearches}
          >
            📜 Näytä aiemmat haut
          </button>

          {researches.map((r) => (
            <motion.div
              key={r.id}
              style={styles.historyItem}
              whileHover={{
                scale: 1.02,
                backgroundColor:
                  "rgba(99,102,241,0.05)"
              }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {

                navigate("/history", { state: { researchId: r.id } });
              }}
            >

              <h3>{r.topic}</h3>

              <p style={styles.linkText}>
                Klikkaa nähdäksesi lisää →
              </p>

            </motion.div>
          ))}

        </motion.div>

      </div>
    </div>
  );
}

const styles = {

  page: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    paddingTop: "40px",
    background:
      "linear-gradient(135deg, #eef2ff, #f0f9ff, #faf5ff)",
    fontFamily: "Inter, sans-serif",
    position: "relative",
    overflow: "hidden"
  },

  container: {
    width: "720px",
    position: "relative",
    zIndex: 2
  },

  blur1: {
    position: "absolute",
    width: "320px",
    height: "320px",
    background: "#8b5cf6",
    filter: "blur(120px)",
    opacity: 0.18,
    top: "-80px",
    left: "-120px"
  },

  blur2: {
    position: "absolute",
    width: "320px",
    height: "320px",
    background: "#3b82f6",
    filter: "blur(120px)",
    opacity: 0.18,
    bottom: "-80px",
    right: "-120px"
  },

  title: {
    textAlign: "center",
    marginBottom: "10px",
    fontSize: "48px",
    fontWeight: "800",
    color: "#111827"
  },

  subtitle: {
    textAlign: "center",
    color: "#6b7280",
    marginBottom: "35px",
    fontSize: "18px",
    lineHeight: "1.6"
  },

  card: {
    background: "rgba(255,255,255,0.65)",
    backdropFilter: "blur(16px)",
    padding: "28px",
    borderRadius: "24px",
    marginBottom: "24px",
    border: "1px solid rgba(255,255,255,0.4)",
    boxShadow: "0 10px 40px rgba(0,0,0,0.08)"
  },

  input: {
    width: "100%",
    padding: "18px",
    borderRadius: "16px",
    border: "1px solid rgba(99,102,241,0.15)",
    marginBottom: "18px",
    fontSize: "16px",
    background: "rgba(255,255,255,0.9)",
    boxShadow: "0 0 20px rgba(99,102,241,0.08)",
    outline: "none"
  },

  primaryButton: {
    width: "100%",
    padding: "16px",
    borderRadius: "16px",
    background:
      "linear-gradient(135deg, #6366f1, #a855f7)",
    color: "white",
    border: "none",
    fontWeight: "700",
    fontSize: "16px",
    cursor: "pointer",
    boxShadow:
      "0 10px 25px rgba(99,102,241,0.3)"
  },

  secondaryButton: {
    border: "none",
    padding: "12px 18px",
    borderRadius: "12px",
    background: "#eef2ff",
    cursor: "pointer",
    fontWeight: "600",
    marginBottom: "14px"
  },

  pdfButton: {
    border: "none",
    padding: "10px 16px",
    borderRadius: "12px",
    background:
      "linear-gradient(135deg, #6366f1, #8b5cf6)",
    color: "white",
    cursor: "pointer",
    fontWeight: "600"
  },

  resultHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px"
  },

  result: {
    lineHeight: "1.8",
    color: "#1f2937"
  },

  agentPreview: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
    marginTop: "22px",
    justifyContent: "center"
  },

  agentBadge: {
    background: "rgba(99,102,241,0.08)",
    padding: "8px 14px",
    borderRadius: "999px",
    fontSize: "14px",
    fontWeight: "600",
    color: "#4f46e5"
  },

  progressWrapper: {
    width: "100%",
    height: "14px",
    background: "rgba(255,255,255,0.4)",
    borderRadius: "999px",
    overflow: "hidden",
    marginBottom: "20px"
  },

  progressBar: {
    height: "100%",
    borderRadius: "999px",
    background:
      "linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899)",
    transition: "width 0.5s ease"
  },

  agentList: {
    padding: "18px",
    borderRadius: "20px",
    marginBottom: "24px",
    background: "rgba(255,255,255,0.6)",
    backdropFilter: "blur(12px)",
    border: "1px solid rgba(255,255,255,0.3)"
  },

  agentItem: {
    padding: "14px",
    marginBottom: "10px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderRadius: "14px"
  },

  agentName: {
    fontWeight: "700",
    marginBottom: "4px"
  },

  agentDesc: {
    fontSize: "13px",
    color: "#6b7280"
  },

  agentStatus: {
    fontSize: "20px",
    minWidth: "30px",
    textAlign: "center"
  },

  logsButton: {
    marginTop: "15px",
    border: "none",
    background: "transparent",
    color: "#4f46e5",
    cursor: "pointer",
    fontWeight: "600"
  },

  logsBox: {
    marginTop: "12px",
    background: "rgba(255,255,255,0.45)",
    borderRadius: "14px",
    padding: "16px"
  },

  logItem: {
    padding: "10px 0",
    borderBottom:
      "1px solid rgba(0,0,0,0.05)",
    fontSize: "14px",
    color: "#374151"
  },

  historyItem: {
    padding: "16px",
    cursor: "pointer",
    borderRadius: "16px",
    marginTop: "10px",
    transition: "0.3s",
    background: "rgba(255,255,255,0.4)"
  },

  linkText: {
    color: "#4f46e5",
    fontWeight: "600"
  }
};

export default Dashboard;
