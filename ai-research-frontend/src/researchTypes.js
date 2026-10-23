export const marketRegions = [
  { value: "Suomi", label: "Suomi" },
  { value: "EU", label: "Euroopan unioni" },
  { value: "world", label: "Koko maailma — yleiskatsaus" },
];
export const selectedMarketRegion = value => marketRegions.find(region => region.value === value) || marketRegions[0];
export const marketQuestions = [
  { value: "overview", label: "Markkinan nykytila", question: "Millainen markkinan nykytila on ja mitkä ovat sen keskeiset toimijat ja ilmiöt?" },
  { value: "changes", label: "Markkinan kehitys", question: "Mitä markkinalla on muuttunut ja mitä ajoitettua näyttöä muutoksista löytyy?" },
];
const area = name => ({ name, label: "Mitä aluetta tarkastellaan?", placeholder: "Esim. Tampereen seutu tai Suomi", help: "Paikalliselle palvelulle kaupunki tai seutu, verkkopalvelulle asiakkaiden maa tai kielialue. Voit jättää avoimeksi.", max: 200, optional: true });
export const researchTypes = [
  { id: "competition", icon: "🔎", title: "Kilpailijavertailu", description: "Selvitä vaihtoehtojen palvelut, hinnat ja ehdot.", outcome: "Valitse vertailtavat tuotteet tai palvelut, alue ja vertailuperusteet.", fields: [
    { name: "solution", label: "Mitä vertaillaan?", placeholder: "Esim. japanilaiset ravintolat, pyörähuollot tai projektinhallintaohjelmistot", help: "Nimeä yksi vertailtava tuote- tai palveluryhmä.", max: 500, multiline: true },
    { ...area("competition_region"), label: "Miltä alueelta?" },
    { name: "criteria", label: "Mitä haluat vertailla?", placeholder: "Esim. hinnat, valikoima, palvelun sisältö tai sopimusehdot", help: "Voit jättää tyhjäksi, jolloin tutkimus valitsee aiheeseen sopivat vertailuperusteet.", max: 500, optional: true },
    { name: "competitors", label: "Tietyt yritykset tai palvelut", placeholder: "Yritysten nimet tai verkkosivut", help: "Voit jättää tyhjäksi. Tutkimus etsii silloin vaihtoehtoja kuvauksesi perusteella.", max: 1000, multiline: true, optional: true },
  ] },
  { id: "market", icon: "📈", title: "Markkinan tilannekuva ja kehitys", description: "Hahmota toimijat, muutokset ja niiden merkitys.", outcome: "Rajaa tutkittava markkina, alue ja kysymys.", fields: [
    { name: "industry", label: "Mitä markkinaa tai toimialaa haluat tutkia?", placeholder: "Esim. kiertotalous, aurinkoenergia tai lemmikkieläinpalvelut", help: "Nimeä yksi markkina tai toimiala. Voit tarkentaa aihetta esimerkiksi rakennusmateriaalien kierrätykseen.", max: 500, multiline: true },
    { name: "region", label: "Mitä aluetta tarkastellaan?", options: marketRegions, defaultValue: "Suomi", help: "EU-valinta tarkastelee EU-maiden markkinaa. Koko maailma tuottaa yleiskatsauksen valituista maista ja alueista." },
    { name: "market_focus", label: "Mikä on tutkimuksen pääkysymys?", options: marketQuestions, defaultValue: "overview" },
  ] },
];
export function selectedType(draft) {
  return researchTypes.find(type => type.id === draft.research_type) || researchTypes[0];
}
export function researchPayload(draft) {
  const type = selectedType(draft).id;
  const value = key => (draft[key] || "").trim();
  const region = type === "competition" ? value("competition_region") : selectedMarketRegion(draft.region).label;
  const focus = marketQuestions.find(item => item.value === draft.market_focus) || marketQuestions[0];
  const goal = type === "market" ? focus.question
    : (value("criteria") ? `Vertailuperusteet: ${value("criteria")}` : "");
  return { research_type: type, topic: value(type === "competition" ? "solution" : "industry"),
    target_market: `Alue: ${region || "ei määritelty"}.`, language: "suomi", goal,
    competitors: type === "competition" ? value("competitors") : "" };
}
export function researchPreview(draft) {
  const payload = researchPayload(draft);
  const regionKey = payload.research_type === "competition" ? "competition_region" : "region";
  const gaps = [];
  if (payload.research_type === "competition" && !draft[regionKey]?.trim()) gaps.push("Alue jäi määrittelemättä.");
  const question = payload.research_type === "competition" ? "Mitä vaihtoehtoja löytyy ja miten niiden tarjonta eroaa?" : "";
  return { text: [payload.topic || "Tutkimusaihe odottaa kuvaustasi.", payload.target_market, question, payload.goal, payload.competitors && `Vertailuun rajatut yritykset tai palvelut: ${payload.competitors}`].filter(Boolean).join("\n\n"), gaps };
}
