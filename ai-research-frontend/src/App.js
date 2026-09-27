import { BrowserRouter, Routes, Route, Link, Navigate, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import History from "./components/History";
import Login from "./components/Login";
import Signup from "./components/Signup";
import { api, clearLegacyStorage } from "./api";
import { clearDraft, emptyDraft, readDraft, saveDraft } from "./researchDraft";
import "./App.css";

function AuthPage({ user, checking, setUser, signup = false }) {
  const navigate = useNavigate();
  const location = useLocation();
  const destination = location.state?.returnTo === "/history" ? "/history" : "/";
  if (user) return <Navigate to={destination} replace />;
  return <main className="auth-page">
    <Link to="/">← Takaisin etusivulle</Link>
    <p>Tutkimuksesi tiedot säilyvät kirjautumisen ajan tässä välilehdessä.</p>
    {location.state?.notice && <p role="status">{location.state.notice}</p>}
    {checking ? <p role="status">Tarkistetaan kirjautumista…</p> : signup
      ? <Signup onCreated={() => navigate("/login", { replace: true, state: { returnTo: destination, notice: "Tili luotu. Kirjaudu jatkaaksesi." } })} />
      : <Login setUser={setUser} />}
    <p>{signup ? "Onko sinulla jo tili? " : "Ensimmäistä kertaa täällä? "}
      <Link to={signup ? "/login" : "/signup"} state={{ returnTo: destination }}>
        {signup ? "Kirjaudu sisään" : "Luo tili"}
      </Link>
    </p>
  </main>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState("");
  const [draft, setDraft] = useState(readDraft);

  const updateDraft = value => { setDraft(value); saveDraft(value); };

  useEffect(() => {
    clearLegacyStorage();
    const controller = new AbortController();
    const expired = () => setUser(null);
    window.addEventListener("session-expired", expired);
    api("/me", { signal: controller.signal })
      .then(value => { if (!controller.signal.aborted) setUser(value); })
      .catch(error => {
        if (!controller.signal.aborted && error.status !== 401) {
          setError("Palvelimeen ei saatu yhteyttä. Voit tutustua esimerkkiin ja valmistella tutkimuksen.");
        }
      })
      .finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => { controller.abort(); window.removeEventListener("session-expired", expired); };
  }, []);

  const logout = async () => {
    try {
      await api("/logout", { method: "POST" });
      clearLegacyStorage();
      clearDraft();
      setDraft({ ...emptyDraft });
      setUser(null);
      setError("");
    } catch { setError("Uloskirjautuminen epäonnistui. Yritä uudelleen."); }
  };

  return <BrowserRouter>
    <header className="site-header">
      <Link className="brand" to="/">🔎 Tutkimus</Link>
      <nav aria-label="Päänavigaatio">
        <Link to="/">Etusivu</Link>
        {user ? <>
          <Link to="/history">Omat raportit</Link>
          <button className="button subtle" onClick={logout}>Kirjaudu ulos</button>
        </> : <Link className="button subtle" to="/login">Kirjaudu sisään</Link>}
      </nav>
    </header>
    {error && <p className="notice" role="alert">{error}</p>}
    <Routes>
      <Route path="/" element={<Dashboard key={user?.user_id || "public"} user={user} setUser={setUser} checking={checking} draft={draft} setDraft={updateDraft} />} />
      <Route path="/login" element={<AuthPage user={user} checking={checking} setUser={value => { setError(""); setUser(value); }} />} />
      <Route path="/signup" element={<AuthPage signup user={user} checking={checking} setUser={setUser} />} />
      <Route path="/history" element={checking ? <p className="notice">Tarkistetaan kirjautumista…</p>
        : user ? <History key={user.user_id} user={user} />
        : <Navigate to="/login" replace state={{ returnTo: "/history" }} />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    <footer className="site-footer">Eri näkökulmia, perusteltuja päätelmiä ja tietoa päätöksen tueksi.</footer>
  </BrowserRouter>;
}
