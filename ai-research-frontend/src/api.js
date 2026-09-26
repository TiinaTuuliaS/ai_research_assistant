// Use the browser's hostname so localhost and 127.0.0.1 both keep same-site cookies.
const API_URL = process.env.REACT_APP_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

export function clearLegacyStorage() {
  localStorage.removeItem("user");
  localStorage.removeItem("selectedResearch");
}

function validationMessage(details, path) {
  if (details.some(item => item.type === "extra_forbidden")) {
    return "Palvelin ei tunnista lomakkeen kenttiä. Käyttöliittymän ja palvelimen versiot eivät vastaa toisiaan. Käynnistä backend uudelleen ja päivitä sivu.";
  }
  const labels = { topic: "Tutkimusaihe", goal: "Tutkimuskysymys", target_market: "Kohdemarkkina", budget_eur: "Budjetti", problem: "Asiakkaan ongelma", competitors: "Kilpailijat", research_type: "Tutkimustyyppi", email: "Sähköposti tai käyttäjätunnus", password: "Salasana" };
  return [...new Set(details.map(item => {
    const field = item.loc?.[item.loc.length - 1];
    const label = labels[field] || "Lomakkeen kenttä";
    if (item.type === "string_too_long") return `${label}: enintään ${item.ctx?.max_length} merkkiä.`;
    if (item.type === "string_too_short") return `${label}: vähintään ${item.ctx?.min_length} merkkiä.`;
    if (item.type === "missing") return `${label} puuttuu.`;
    if (field === "budget_eur") return "Budjetin on oltava numero väliltä 0–10 000 000 €. Voit myös jättää sen tyhjäksi.";
    return `${label}: tarkista annettu arvo.`;
  }))].join(" ") || (path === "/signup" ? "Tarkista tunnus ja salasana." : "Tarkista lomakkeen tiedot.");
}

export async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "ResearchApp",
      ...options.headers,
    },
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== "/login") {
      clearLegacyStorage();
      window.dispatchEvent(new Event("session-expired"));
    }
    const message = Array.isArray(data?.detail)
      ? validationMessage(data.detail, path)
      : data?.detail || "Pyyntö epäonnistui.";
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}
