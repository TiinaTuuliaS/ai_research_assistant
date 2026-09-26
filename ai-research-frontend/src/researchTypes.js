export const researchTypes = [
  { id: "demand", icon: "💡", title: "Onko idealleni kysyntää?", description: "Selvitä tarvetta, nykyisiä vaihtoehtoja ja kysynnän merkkejä.", outcome: "Saat arvion kysynnän merkeistä ja siitä, mitä ei vielä tiedetä.", fields: [
    { name: "idea", label: "Mikä on ideasi?", placeholder: "Esim. asiakaspalautepalvelu pienyrityksille", max: 500 },
    { name: "audience", label: "Kenelle idea on tarkoitettu?", placeholder: "Esim. suomalaiset 2–10 hengen palveluyritykset", max: 500 },
    { name: "problem", label: "Minkä ongelman idea ratkaisee?", placeholder: "Kuvaile asiakkaan ongelma tai tarve.", max: 1000, multiline: true },
  ] },
  { id: "competition", icon: "🔎", title: "Miten erotun kilpailijoista?", description: "Vertaa vaihtoehtoja ja löydä mahdollisia tapoja erottua.", outcome: "Saat vertailun kilpailijoiden vahvuuksista, eroista ja mahdollisista aukoista.", fields: [
    { name: "solution", label: "Mitä oma ratkaisusi tarjoaa?", placeholder: "Kuvaile tuotteesi tai palvelusi", max: 500 },
    { name: "competitors", label: "Tunnetut kilpailijat", placeholder: "Nimet tai verkkosivut. Voit jättää tyhjäksi, niin agentit etsivät kilpailijoita.", max: 1000, multiline: true, optional: true },
    { name: "competition_market", label: "Millä markkinalla kilpailet?", placeholder: "Esim. Suomi, pienten verkkokauppojen asiakaspalvelu", max: 500 },
  ] },
  { id: "market", icon: "📈", title: "Mitä tällä markkinalla tapahtuu?", description: "Hahmota toimijat, muutokset ja niiden merkitys.", outcome: "Saat katsauksen markkinan toimijoihin ja muutoksiin oman kysymyksesi näkökulmasta.", fields: [
    { name: "industry", label: "Mikä toimiala tai ilmiö kiinnostaa?", placeholder: "Esim. digitaaliset koulutuspalvelut", max: 500 },
    { name: "region", label: "Mitä aluetta tarkastellaan?", placeholder: "Esim. Suomi, Pohjoismaat tai Eurooppa", max: 500 },
    { name: "question", label: "Mitä haluat markkinasta tietää?", placeholder: "Esim. mitkä muutokset vaikuttavat pieniin koulutusyrityksiin?", max: 1000, multiline: true },
  ] },
];

export function selectedType(draft) {
  return researchTypes.find(type => type.id === draft.research_type) || researchTypes[0];
}

export function researchPayload(draft) {
  const type = selectedType(draft).id;
  const value = key => (draft[key] || "").trim();
  const topic = value(type === "demand" ? "idea" : type === "competition" ? "solution" : "industry");
  const target_market = value(type === "demand" ? "audience" : type === "competition" ? "competition_market" : "region");
  return { research_type: type, topic, target_market, language: "suomi",
    goal: type === "market" ? value("question") : "",
    problem: type === "demand" ? value("problem") : "",
    competitors: type === "competition" ? value("competitors") : "",
    budget_eur: draft.budget_eur === "" || draft.budget_eur == null ? null : Number(draft.budget_eur) };
}
