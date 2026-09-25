import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import History from "./components/History";
import Login from "./components/Login";
import Signup from "./components/Signup";
import { useEffect, useState } from "react";
import { api, clearLegacyStorage } from "./api";

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    clearLegacyStorage();
    const controller = new AbortController();
    const expired = () => setUser(null);
    window.addEventListener("session-expired", expired);
    api("/me", { signal: controller.signal })
      .then(value => { if (!controller.signal.aborted) setUser(value); })
      .catch(error => {
        if (error.name !== "AbortError" && error.status !== 401) {
          setError("Palvelimeen ei saatu yhteyttä. Päivitä sivu yrittääksesi uudelleen.");
        }
      })
      .finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => {
      controller.abort();
      window.removeEventListener("session-expired", expired);
    };
  }, []);

  const logout = async () => {
    try {
      await api("/logout", { method: "POST" });
      clearLegacyStorage();
      setUser(null);
      setError("");
    } catch {
      setError("Uloskirjautuminen epäonnistui. Yritä uudelleen.");
    }
  };

  if (checking) return <p>Tarkistetaan kirjautumista…</p>;

  // 🔥 JOS EI USER → NÄYTÄ LOGIN
  if (!user) {
    return (
      <div style={{ padding: "30px" }}>
        <h2>Kirjaudu sisään</h2>
        {error && <p role="alert">{error}</p>}
        <Login setUser={value => { setError(""); setUser(value); }} />
        <Signup />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div style={styles.navbar}>

        <div style={styles.left}>
          <Link style={styles.link} to="/">🔎 Tutkimus</Link>
          <Link style={styles.link} to="/history">📜 Historia</Link>
        </div>

        <button
          style={styles.logout}
          onClick={logout}
        >
          🚪 Logout
        </button>

      </div>

      {error && <p role="alert">{error}</p>}

      <Routes>
        <Route path="/" element={<Dashboard key={user.user_id} user={user} />} />
        <Route path="/history" element={<History key={user.user_id} user={user} />} />
      </Routes>
    </BrowserRouter>
  );
}

const styles = {
  navbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "15px 25px",
    background: "#fff",
    borderBottom: "1px solid #eee"
  },

  left: {
    display: "flex",
    gap: "20px"
  },

  link: {
    textDecoration: "none",
    color: "#111",
    fontWeight: "500"
  },

  logout: {
    border: "none",
    background: "#ef4444",
    color: "white",
    padding: "8px 14px",
    borderRadius: "8px",
    cursor: "pointer"
  }
};

export default App;
