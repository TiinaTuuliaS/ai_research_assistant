export const marketQuestions = [
  { value: "overview", label: "Nykyinen tarjonta ja toimijat", question: "Millaista tarjontaa markkinalla on ja keille palvelut on tarkoitettu?" },
  { value: "changes", label: "Markkinan kehitys ja muutokset", question: "Mitä markkinalla on muuttunut ja mitä ajoitettua näyttöä muutoksista löytyy?" },
  { value: "opportunities", label: "Uuden palveluntarjoajan mahdollisuudet", question: "Mitä aineisto kertoo uuden palveluntarjoajan mahdollisuuksista ja mitä jää selvittämättä?" },
];
const area = name => ({ name, label: "Mitä aluetta tarkastellaan?", placeholder: "Esim. Tampereen seutu tai Suomi", help: "Paikalliselle palvelulle kaupunki tai seutu, verkkopalvelulle asiakkaiden maa tai kielialue. Voit jättää avoimeksi.", max: 200, optional: true });
const audience = name => ({ name, label: "Keitä asiakkaita tarkastellaan?", placeholder: "Esim. työmatkapyöräilijät tai kotona asuvat eläkeläiset", help: "Nimeä ihmisryhmä tai yritystyyppi. Pelkkä toimiala, kuten palveluala, ei kuvaa asiakkaita.", max: 200, optional: true });
export const researchTypes = [
  { id: "competition", icon: "🔎", title: "Kilpailutarjonnan kartoitus", description: "Selvitä vaihtoehtojen palvelut, hinnat ja ehdot.", outcome: "Kuvaa vertailtava tarjonta ja haluamasi vertailuperusteet. Oma yritysidea ei ole välttämätön.", fields: [
    { name: "solution", label: "Mitä tuotteita tai palveluja vertaillaan?", placeholder: "Esim. pyörähuolto ja työmatkapyöräilijöiden vaatemyymälä", help: "Kerro vertailtava palvelu tai tuote. Oma suunnitelma on vapaaehtoinen; mainitse se vain, jos haluat vertailla myös sitä.", max: 500, multiline: true },
    audience("competition_market"), area("competition_region"),
    { name: "criteria", label: "Mitä ominaisuuksia haluat vertailla?", placeholder: "Esim. huoltohinnat, ajanvaraus, noutopalvelu ja vaatevalikoima", help: "Voit jättää tyhjäksi, jolloin tutkimus valitsee aiheeseen sopivat vertailuperusteet.", max: 500, optional: true },
    { name: "competitors", label: "Tunnetut kilpailijat", placeholder: "Yritysten nimet tai verkkosivut", help: "Voit jättää tyhjäksi. Tutkimus etsii silloin vaihtoehtoja kuvauksesi perusteella.", max: 1000, multiline: true, optional: true },
  ] },
  { id: "market", icon: "📈", title: "Markkinan tilannekuva ja kehitys", description: "Hahmota toimijat, muutokset ja niiden merkitys.", outcome: "Rajaa palvelut ja asiakkaat, jotta tutkimus tarkastelee oikeaa markkinaa.", fields: [
    { name: "industry", label: "Mitä palveluja tai tuotteita tutkimus koskee?", placeholder: "Esim. kuluttajille myytävät suomenkieliset digitaitojen verkkokurssit", help: "Erota palvelun sisältö ja toimitustapa: digitaitojen lähiopetus ja verkossa myytävä kurssi ovat eri asioita.", max: 500, multiline: true },
    audience("market_audience"), area("region"),
    { name: "market_focus", label: "Mikä on tutkimuksen pääkysymys?", options: marketQuestions, defaultValue: "overview" },
    { name: "period", label: "Mitä ajanjaksoa tarkastellaan?", placeholder: "Esim. 2023–2026", help: "Erityisen hyödyllinen, kun tarkastelet muutosta. Tyhjä kenttä jättää ajanjakson avoimeksi.", max: 100, optional: true },
    { name: "question", label: "Haluatko tarkentaa kysymystä?", placeholder: "Esim. miten maksuton tarjonta vaikuttaa maksullisen kurssin suunnitteluun?", help: "Kerro, millaiseen päätökseen tarvitset tietoa. Voit myös käyttää pelkkää yllä valittua pääkysymystä.", max: 700, multiline: true, optional: true },
  ] },
];
export function selectedType(draft) {
  return researchTypes.find(type => type.id === draft.research_type) || researchTypes[0];
}
export function researchPayload(draft) {
  const type = selectedType(draft).id;
  const value = key => (draft[key] || "").trim();
  const customer = value(type === "competition" ? "competition_market" : "market_audience");
  const region = value(type === "competition" ? "competition_region" : "region");
  const focus = marketQuestions.find(item => item.value === draft.market_focus) || marketQuestions[0];
  const goal = type === "market" ? [focus.question, value("question"), value("period") && `Tarkastelujakso: ${value("period")}.`].filter(Boolean).join("\n")
    : (value("criteria") ? `Vertailuperusteet: ${value("criteria")}` : "");
  return { research_type: type, topic: value(type === "competition" ? "solution" : "industry"),
    target_market: `Asiakkaat: ${customer || "ei määritelty"}. Alue: ${region || "ei määritelty"}.`, language: "suomi", goal,
    competitors: type === "competition" ? value("competitors") : "" };
}
export function researchPreview(draft) {
  const payload = researchPayload(draft);
  const customerKey = payload.research_type === "competition" ? "competition_market" : "market_audience";
  const regionKey = payload.research_type === "competition" ? "competition_region" : "region";
  const gaps = [];
  if (!draft[customerKey]?.trim()) gaps.push("Asiakasryhmä jäi määrittelemättä.");
  if (!draft[regionKey]?.trim()) gaps.push("Alue jäi määrittelemättä.");
  if (payload.research_type === "market" && draft.market_focus === "changes" && !draft.period?.trim()) gaps.push("Muutoksen tarkastelujakso jäi avoimeksi.");
  const question = payload.research_type === "competition" ? "Mitä vaihtoehtoja asiakkaille on ja mitä niiden vertailusta voi päätellä?" : "";
  return { text: [payload.topic || "Tutkimusaihe odottaa kuvaustasi.", payload.target_market, question, payload.goal, payload.competitors && `Tunnetut kilpailijat: ${payload.competitors}`].filter(Boolean).join("\n\n"), gaps };
}
