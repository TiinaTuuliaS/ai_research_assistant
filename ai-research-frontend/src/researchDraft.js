import { selectedMarketRegion } from "./researchTypes";

export const emptyDraft = { research_type: "competition", topic: "", goal: "", target_market: "", solution: "", competitors: "", competition_region: "", criteria: "", industry: "", region: "Suomi", market_focus: "overview" };
const KEY = "research-draft";

export function readDraft() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(KEY));
    // Removed-mode drafts are reset, never silently submitted as another research type.
    if (saved && !["competition", "market"].includes(saved.research_type)) return { ...emptyDraft };
    if (saved && !["overview", "changes"].includes(saved.market_focus)) saved.market_focus = "overview";
    if (saved) saved.region = selectedMarketRegion(saved.region).value;
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
