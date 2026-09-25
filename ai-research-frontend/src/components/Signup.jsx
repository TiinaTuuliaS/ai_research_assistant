import React, { useState } from "react";
import { api } from "../api";

function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const signup = async () => {
    if (loading) return;
    if (!email.trim() || password.length < 12) {
      alert("Anna tunnus ja vähintään 12 merkin salasana.");
      return;
    }

    setLoading(true);
    try {
      await api("/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      });

      alert("Tili luotu! Voit kirjautua.");

      // 🔥 tyhjennetään kentät
      setEmail("");
      setPassword("");

    } catch (error) {
      alert(error.message || "Ei yhteyttä backendiin");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h2>✨ Luo tili</h2>

        <input
          style={styles.input}
          placeholder="Sähköposti tai käyttäjätunnus"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          style={styles.input}
          type="password"
          autoComplete="new-password"
          placeholder="Salasana (vähintään 12 merkkiä)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button style={styles.button} onClick={signup} disabled={loading}>
          Rekisteröidy
        </button>
      </div>
    </div>
  );
}

const styles = {
  page: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#f5f7fb"
  },

  card: {
    background: "white",
    padding: "40px",
    borderRadius: "16px",
    boxShadow: "0 15px 40px rgba(0,0,0,0.08)",
    width: "320px"
  },

  input: {
    width: "100%",
    padding: "12px",
    marginBottom: "12px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    fontSize: "14px"
  },

  button: {
    width: "100%",
    padding: "12px",
    borderRadius: "8px",
    border: "none",
    background: "#4f46e5",
    color: "white",
    fontWeight: "bold",
    cursor: "pointer"
  }
};

export default Signup;
