// Use the browser's hostname so localhost and 127.0.0.1 both keep same-site cookies.
const API_URL = process.env.REACT_APP_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

export function clearLegacyStorage() {
  localStorage.removeItem("user");
  localStorage.removeItem("selectedResearch");
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
      ? "Tarkista kentät. Uuden salasanan on oltava vähintään 12 merkkiä."
      : data?.detail || "Pyyntö epäonnistui.";
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}
