export const emptyDraft = { research_type: "demand", topic: "", goal: "", target_market: "", budget_eur: "", idea: "", audience: "", problem: "", solution: "", competitors: "", competition_market: "", industry: "", region: "", question: "" };
const KEY = "research-draft";

export function readDraft() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(KEY));
    if (saved && !saved.research_type) {
      saved.idea = saved.idea || saved.topic;
      saved.audience = saved.audience || saved.target_market;
      saved.problem = saved.problem || saved.goal;
    }
    return Object.fromEntries(Object.entries(emptyDraft).map(([key, fallback]) =>
      [key, typeof saved?.[key] === "string" ? saved[key].slice(0, 1000) : fallback]));
  } catch { return { ...emptyDraft }; }
}

export function saveDraft(draft) {
  try { sessionStorage.setItem(KEY, JSON.stringify(draft)); } catch { /* In-memory editing still works. */ }
}

export function clearDraft() {
  try { sessionStorage.removeItem(KEY); } catch { /* Storage may be disabled. */ }
}
