# Tutkimusassistentin arvioinnista

Tämä on tekoälyn (Codex) tuottama tiivistelmä projektin kehityskeskustelujen,
koodin ja tallennettujen testitulosten perusteella. Se ei ole riippumaton auditointi
eikä lupaus raporttien virheettömyydestä.

Päivitetty 23.10.2026.
Vanhojen kokeiden kertakäyttöiset ajoskriptit ja lokit poistettiin siivouksessa 22.10.2026.
Niistä testeihin tarvittavat lähdekatkelmat on tallennettu versionhallinnan testiaineistoihin.

## Nykyinen tuote

Kolme agenttia (tutkija, analyytikko, kirjoittaja) tuottaa kilpailijavertailuja tai markkinan
nykytilaa ja kehitystä kuvaavia raportteja. Sovellus ei arvioi käyttäjän yritysideoita eikä
muodosta uusia liiketoimintasuosituksia. Nykyinen toiminta on kuvattu projektin README:ssa.

## Havaitut ongelmat ja tehdyt rajaukset

- Tarjonta ei osoita kysyntää. Kysyntätutkimus poistettiin tuotevalikoimasta.
- Yksittäinen havainto saa vastata vain osaan kysymyksestä. Esimerkiksi hinta on
  vertailuaineistoa, vaikka palvelun kaikki ominaisuudet eivät löytyisi lähteestä.
- Toimijoiden, toimipaikkojen, hintajaksojen ja maantieteellisten rajausten sekoittuminen
  on todellinen riski. Lähdetunniste tai rakenteen validointi ei yksin estä sitä.
- Visio, ennuste, markkinointilupaus ja yksittäinen asiakaskokemus tulee erottaa
  todennetusta nykytilasta. Tallennetut lähdetekstit ovat mukana regressiotesteissä.
- Yksittäinen virheellinen vertailurivi käsitellään paikallisesti. Tämä ei saa muuttaa
  tukematonta väitettä hyväksytyksi tai ohittaa muun analyysin tarkistuksia.
- Rajattu varakooste erotetaan valmiista loppuraportista. Se säilyttää hyväksytyt havainnot.
- Markdown-taulukot renderöidään yhteisellä komponentilla myös PDF-tallennuksessa.
  Kirjoittajan ohje vähentää saman tiedon toistamista taulukkona ja listoina.

## Arvioinnin rajat

Automaattiset testit varmistavat rakenteita, tiedonsiirtoa, virheenkäsittelyä ja käyttöliittymää.
Monissa sisältötarkistustesteissä mallivastaus on käsin määritelty: ne eivät mittaa mallin
itsenäistä kykyä tunnistaa tulevia virheitä. Viimeisimmässä kutsurajauksen tarkistuksessa
läpäisi 27 API-testiä ja 48 frontend-testiä. Nämä eivät olleet koko backend-testijoukon ajo.
Ajantasainen varmistus tehdään README:n testikomennoilla. Testien onnistuminen ei osoita
raporttien väitteitä tosiksi eikä todista julkaisuympäristön toimivuutta.

Oikeissa ravintola- ja coworking-kokeissa löytyi edelleen lähteen ylittäviä päätelmiä,
kuten alueellisen hintatiedon kohdistamista nimetyille ketjuille ja epäselvän buffetin
käyttöajan esittämistä lounasaikana. Mallipohjainen tarkistaja voi toistaa ensimmäisen
mallin tulkintavirheen. Loppuraportin tarkistaja näkee hyväksytyt havainnot ja niiden
katkelmat, ei koko alkuperäistä sivutekstiä. Sovellus esitellään kokeellisena demona.

## Viimeisimmät havainnot ja tehdyt korjaukset (23.10.2026)

- Remonttifirmojen vertailu (raportti 45) ja uusiutuvan energian nykytilaraportti
  (48) valmistuivat. Ne valittiin julkisiksi esimerkeiksi alkuperäisine teksteineen
  ja lähteineen. Niitä ei ole erikseen kokonaisuudessaan faktantarkistettu.
- Markkinatutkimuksen lomakkeelta poistettiin vuosirajaus. Vanhojen luonnosten
  vuosikenttä ei enää välity tutkimukseen. Ohjeissa ei oleteta käyttäjän antavan vuosia.
  Lähteiden omat ajankohdat ja niiden tarkistukset säilyvät.
- Markkinatutkimuksen alue valitaan vaihtoehdoista Suomi, Euroopan unioni ja
  koko maailma. Maailman tarkastelu on yleiskatsaus; jäsenmaan havainto ei edusta
  automaattisesti koko EU:ta. Kilpailijavertailun aluekenttä säilyi avoimena.
- Analyysin yleiset epävarmuustekstit kootaan näytettäessä loppuosioon.
  Kirjoittajan ohjeita täsmennettiin toiston vähentämiseksi. Väitteen tulkintaan
  tarvittavat ehdot, kuten tilastovuosi ja ennusteen luonne, kuuluvat väitteen yhteyteen.
  Ohjeistus ei takaa, että malli noudattaa tätä joka raportissa.
- Taulukoille lisättiin leveämpi asettelu. Tekstikappaleiden lukuleveys säilytettiin
  rajattuna ja pienillä näytöillä taulukot voivat vierittyä vaakasuunnassa.

## Avoimet sisältö- ja toimintavarmuusongelmat

- **Yksittäinen vuosilukuvirhe voi pysäyttää analyysin.** Kiertotaloustutkimuksessa
  (46) tutkija valmistui, mutta analyysin vuosilukutarkistus hylkäsi tuloksen ja
  kirjoittajavaihe jäi tekemättä. Tallennettiin rajattu varakooste. Hylättyä
  analyysitekstiä ei tallennettu, joten virheen tarkkaa lausetta tai vuosilukua ei
  voitu jälkikäteen varmistaa. Vuosikentän poistaminen ei korjaa tätä mekanismia.
- **Käyttökelpoista lähdeaineistoa voi pudota pois.** Samassa tutkimuksessa
  Tilastokeskuksen ja vuoden 2016 tutkimustiedotteen havainnot eivät läpäisseet
  ajankohdan ja tukitekstin tarkistuksia. Aineiston löytyminen ei siis takaa sen
  onnistunutta hyödyntämistä. Toisaalta varakoosteeseen jäi aiheeseen heikosti
  liittyvä yritystyökaluja koskeva havainto.
- **Valmistuminen ei tarkoita kysymykseen vastaamista.** Lemmikkieläinhoitoloiden
  kehitysraportti (49) valmistui, mutta aineisto kuvasi enimmäkseen nykyisiä
  palveluita. Koirakokeiden järjestämistä koskeva havainto jäi sivuun varsinaisesta
  markkinakysymyksestä. Markkinan kehitys on erityisen riippuvainen ajoitetun,
  vertailukelpoisen aineiston löytymisestä.
- **Raportti voi painottua yritysluetteloihin ja sivuaiheisiin.** Uusiutuvan energian
  käytön tutkimuksissa painotus siirtyi osittain investointeihin ja datakeskuksiin.
  Yhden lähteen yrityslista ei osoita toimijoiden keskeistä asemaa koko markkinalla.
- **Rajauksia ja väitteitä voi edelleen toistua.** Raportissa 48 on kaksi
  osittain päällekkäistä rajausosiota. Tallennetut esimerkkiraportit esitetään
  alkuperäisinä; myöhemmät ohjemuutokset eivät muuta niiden tekstiä.

## Demon käyttö ja julkaisuvalmistelut

Uusien tilien rekisteröityminen vaatii kertakäyttöisen kutsukoodin. Tavallinen tili saa
kolme tutkimusta; olemassa olevat tilit ja ylläpitäjän poikkeus säilyvät. Koodi
säilytetään tietokannassa tiivisteenä. Vanha synkroninen `/research`-rajapinta on
suljettu, ja tutkimukset käynnistetään `/research-jobs`-reitillä. Näitä toimintoja
on testattu korvatuilla mallikutsuilla erillisessä testitietokannassa.

## Railway-käyttöönotto ja tuotantotesti (23.10.2026)

Sovellus julkaistiin Railway Hobby -palveluun. React ja FastAPI toimivat samasta
HTTPS-osoitteesta, SQLite on `/data`-volumella ja virhelokin polku on
`/data/logs/backend-errors.log`. Admin-tunnus siirrettiin erikseen; paikallinen tili
säilyi. Alla olevat tuotannon käyttöpolkuhavainnot perustuvat käyttäjän ilmoituksiin
ja hänen toimittamiinsa raportteihin ja lokitulosteisiin, eivät kattavaan auditointiin.

- Etusivu ja kaksi alkuperäistä esimerkkiraporttia avautuivat.
- Admin-kirjautuminen ja rajattomat ylläpitäjän tutkimuskerrat toimivat.
- Kutsulla luotu testitili sai kolme tutkimuskertaa; käytetty kutsu hylättiin.
- Testitilin kolme tutkimusta kuluttivat kiintiön nollaan, eikä uusia tutkimuksia
  voinut enää käynnistää.
- Levykauppavertailun ensimmäinen ajo jäi rajatuksi yritysnimen tarkistuksessa.
  Paikallisesti toistettiin ristiriita: sama yritystunniste hyväksyi kirjainkokoerot,
  mutta nimivalidointi vaati täsmälleen samaa kirjoitusasua. Käsittely yhtenäistettiin
  ja vertailun näyttönimi sidottiin sen omiin havaintoihin. Korjauskierroksen 23
  kohdennettua testiä läpäisi ilman maksullisia kutsuja.
- Toinen ajo jäi rajatuksi lähdeosoitteen tarkistuksessa. Tallennetusta luonnoksesta
  puuttui rekisteröidyn URL:n `srsltid`-seurantaparametri. Tunnetun parametrin erot
  ratkaistaan nyt yksikäsitteiseen alkuperäiseen lähteeseen; sisältöparametreja ei
  poisteta eikä epäselviä vastineita arvata. Korjauskierroksen 39 kohdennettua testiä
  läpäisi ilman maksullisia kutsuja. Nämä määrät eivät ole koko backend-testijoukon ajo.
- Kolmas levykauppatutkimus valmistui loppuraportiksi. Tämä vahvistaa yhden
  kokonaisen tutkimusajon onnistumisen Railwaysta, ei kaikkien aiheiden luotettavuutta.

### Valmistuneen levykaupparaportin sisältörajoitteet

Neljän kaupan vertailussa hinta- ja valikoimatietoa saatiin lähinnä Äx:stä, joten
varsinainen kauppojen välinen hintavertailu jäi tekemättä. Välituloksiin verrattaessa
loppuraporttiin oli lisätty Äx:n sunnuntaisulku ilman näkyvää tukea niissä.
Laukontorin lauantain tiedot esitettiin taulukossa epäjohdonmukaisesti.
Verkkokaupan esimerkkihintojen soveltuvuutta Tampereen myymälään ei osoitettu,
ja aukioloaikataulukon sisältö toistui tekstissä. Näitä ei korjattu uudella
laatukorjauskierroksella. Arvio perustuu raporttiin ja välituloksiin, ei uuteen
alkuperäissivujen faktantarkistukseen.

### Tietojen säilyminen ja varmistukset

Admin-tili säilyi uudelleenjulkaisujen yli. Tuotantotietokannasta tehtiin SQLite
backup -rajapinnalla eheystarkistettu varmistus ja käyttäjä latasi sen omalle
koneelleen projektin ulkopuolelle. Tämä kopio tehtiin ennen testitiliä ja raportteja;
uusi testien jälkeinen varmistus ja sen lataaminen ovat vielä vahvistamatta.

Railwayn Backups-näkymä ilmoitti uusien varmistusten ja ajastusten vaativan
Pro-tilauksen. Hobbyssa käytössä on tässä vaiheessa manuaalinen SQLite-varmistus,
ei automaattinen varmistusaikataulu. Palautus uuteen tietokantaan on testattu
paikallisesti; tuotantovarmistuksen varsinainen palautusharjoitus on tekemättä.
Yhden palvelinprosessin työnkulku keskeyttää käynnissä olevat tutkimukset
palvelimen käynnistyessä uudelleen.

## Säilytetty arviointiaineisto

- `tests/fixtures/source_context_cases.json`: vision ja asiakaskokemuksen asiayhteys.
- `tests/fixtures/comparison_reliability.json`: tallennetut ravintola- ja coworking-havainnot.
- `ai-research-frontend/src/components/__fixtures__/restaurant-table.json`: oikean raportin
  taulukkorakenne renderöintitesteihin.
- Käyttäjäraportit säilyvät paikallisessa tietokannassa; niitä ei poisteta tiedostosiivouksessa.
- `.runtime/backups/` sisältää aiemmin poistettujen tietokantarivien varmuuskopion sekä
  vanhojen tiedostovientien arkiston. Niitä ei julkaista versionhallinnassa.

## Uudet tarkistukset

Väliaikaiset lokit ja uudet maksulliset arvioinnit tallennetaan jatkossa `.runtime`-kansioon.
Ne eivät ole sovelluksen lähdekoodia. `scripts/evaluate_reports.py` on nykyisten kahden
tutkimustavan ylläpidetty maksullinen arviointityökalu. Sen ajaminen käyttää API-krediittejä.
