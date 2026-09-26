import { useState } from "react";
import { api, clearLegacyStorage } from "../api";

export default function Login({ setUser }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = async event => {
    event.preventDefault();
    if (loading) return;
    setLoading(true); setError("");
    try {
      const user = await api("/login", { method: "POST", body: JSON.stringify({ email, password }) });
      clearLegacyStorage(); setUser(user);
    } catch (error) { setError(error.message || "Kirjautuminen epäonnistui."); }
    finally { setLoading(false); }
  };
  return <form className="panel auth-card" onSubmit={login}>
    <h1>Kirjaudu sisään</h1>
    <p>Pääset tekemään tutkimuksia ja palaamaan omiin raportteihisi.</p>
    {error && <p role="alert" className="error">{error}</p>}
    <label htmlFor="login-email">Sähköposti tai käyttäjätunnus</label>
    <input id="login-email" autoComplete="username" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} />
    <label htmlFor="login-password">Salasana</label>
    <input id="login-password" type="password" autoComplete="current-password" required maxLength={1024} value={password} onChange={e => setPassword(e.target.value)} />
    <button className="button primary" disabled={loading}>{loading ? "Kirjaudutaan…" : "Kirjaudu"}</button>
  </form>;
}
