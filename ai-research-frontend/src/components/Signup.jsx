import { useState } from "react";
import { api } from "../api";

export default function Signup({ onCreated }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const signup = async event => {
    event.preventDefault();
    if (loading) return;
    setLoading(true); setError("");
    try {
      await api("/signup", { method: "POST", body: JSON.stringify({ email, password }) });
      onCreated();
    } catch (error) { setError(error.message || "Tilin luonti epäonnistui."); }
    finally { setLoading(false); }
  };
  return <form className="panel auth-card" onSubmit={signup}>
    <h1>Luo tili</h1>
    <p>Tallenna tutkimuksesi ja palaa suunnitelmiin myöhemmin.</p>
    {error && <p role="alert" className="error">{error}</p>}
    <label htmlFor="signup-email">Sähköposti tai käyttäjätunnus</label>
    <input id="signup-email" autoComplete="username" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} />
    <label htmlFor="signup-password">Salasana (vähintään 12 merkkiä)</label>
    <input id="signup-password" type="password" autoComplete="new-password" required minLength={12} maxLength={1024} value={password} onChange={e => setPassword(e.target.value)} />
    <button className="button primary" disabled={loading}>{loading ? "Luodaan tiliä…" : "Luo tili"}</button>
  </form>;
}
