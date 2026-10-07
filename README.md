# AI Markkinatutkimusassistentti

Sovellus auttaa selvittämään idean kysyntää, vertailemaan kilpailijoita ja tutkimaan
markkinoiden muutoksia. Viisi AI-agenttia tuottaa omat näkemyksensä ja yhteisen
loppuraportin lähteineen. Työn etenemistä voi seurata käyttöliittymässä.

Etusivuun voi tutustua vapaasti. Tutkimusten tekeminen ja omien raporttien katselu
vaativat kirjautumisen. Raportin voi ladata tekstinä, tallentaa PDF:ksi selaimen
tulostustoiminnolla tai jakaa siitä otteen.

Käyttäjätilillä voi aloittaa yhteensä kolme tutkimusta kaikista tutkimustavoista.
Myös keskeytyneet tutkimukset kuluttavat käyttökerran; aiemmat tutkimukset lasketaan
mukaan. Raja tarkistetaan palvelimella, ja jäljellä olevat kerrat näkyvät lomakkeessa.
Omia raportteja voi katsella rajan täytyttyäkin.

Ylläpitäjän tutkimusrajan voi poistaa palvelimen `ADMIN_USER_IDS`-asetuksella
(pilkuin erotetut olemassa olevien käyttäjien tietokantatunnisteet).
Tunnisteet määritetään erikseen paikallisesti ja Railwayn ympäristömuuttujissa.
Rajattomuus ei anna pääsyä muiden käyttäjien raportteihin.

## Teknologiat

- **React ja JavaScript** – käyttöliittymä, React Router – sivujen reititys.
- **Python ja FastAPI** – backend ja REST-rajapinta.
- **CrewAI ja OpenAI (GPT-4.1 mini)** – agenttien yhteistyö ja raporttien tuottaminen.
- **Serper** – verkkohaku tutkimusten lähteitä varten.
- **SQLite ja SQLAlchemy** – käyttäjien ja raporttien tallennus.
- **CSS ja Framer Motion** – ulkoasu ja animaatiot.
- **Jest, React Testing Library ja unittest** – automaattiset testit.
- **uv ja npm** – riippuvuuksien hallinta ja kehityskomennot.

## Asennus

Tarvitset Python 3.10–3.13:n, uv:n ja Node.js 20+:n. Suorita komennot projektin juuressa:

```powershell
uv sync --locked
npm --prefix ai-research-frontend ci
```

Kopioi `.env.example` tiedostoksi `.env`, jos sitä ei vielä ole.
Lisää siihen `OPENAI_API_KEY` ja `SERPER_API_KEY`.

## Käynnistys

```powershell
npm run dev
```

Avaa http://localhost:3000. API:n dokumentaatio löytyy osoitteesta
http://127.0.0.1:8000/docs. Pysäytä palvelut painamalla Ctrl+C.

Voit myös käynnistää palvelut **erikseen kahdessa terminaalissa**:

```powershell
npm run front
```

```powershell
npm run backend
```

Valitse yksi käynnistystapa kerrallaan, jotta portit eivät ole jo käytössä.
Backendin koodimuutokset vaativat uudelleenkäynnistyksen.

## Rakenne

- `ai-research-frontend/` – React-käyttöliittymä ja sen testit.
- `src/` – FastAPI-rajapinta, kirjautuminen ja tietokanta.
- `src/ai_research_assistant/` – agentit, YAML-tehtävänannot ja lähteiden tarkistus.
- `tests/` – backendin testit.
- `scripts/` – yhteinen käynnistyskomento.
- `reports/` – aiemman version tallentamat raporttitiedostot.

Nykyiset käyttäjät ja raportit tallentuvat paikalliseen `app.db`-tietokantaan.
`.env` ja tietokanta eivät kuulu versionhallintaan.

## Tarkistukset

```powershell
uv run --no-sync python -m unittest discover -s tests
npm --prefix ai-research-frontend test -- --watchAll=false --runInBand
npm --prefix ai-research-frontend run build
```

Testit eivät tee maksullisia AI-hakuja. Varsinaiset tutkimukset käyttävät OpenAI- ja
Serper-palveluita ja voivat aiheuttaa kustannuksia. Tulokset perustuvat verkkohakujen
katkelmiin: lähdelinkkien tarkistus ei takaa kaikkien väitteiden oikeellisuutta.

Tutkija palauttaa kaikissa kolmessa tutkimustavassa Pydantic-validoidun
`ResearchResult`-olion: aihe ja havainnot (otsikko, yhteenveto, HTTP(S)-lähdeosoite,
osuvuus 1–10). CrewAI muodostaa olion `output_pydantic`-asetuksen avulla.
Virheellinen rakenne tai haussa tuntematon lähde keskeyttää työn. Validoiduista
kentistä muodostettu teksti välitetään nykyisille seuraaville agenteille ja
raporttinäkymään. Osuvuus ei tarkoita lähteen luotettavuutta.

Muiden agenttien tekstit tarkistetaan erillisellä mallikutsulla. Tarkistus arvioi kielen selkeyttä, aiheen
mukaista sisältöä ja väitteiden tukea hakutuloskatkelmissa sekä korjaa sanamuotoja
ja poistaa perusteettomia väitteitä. Mallin tekemä tarkistus ei takaa virheettömyyttä.
Hylättyä välitulosta yritetään korjata kerran ja loppuraporttia enintään kahdesti.
Yhden tutkimuksen verkkohakutyökalua voi kutsua enintään kuusi kertaa palveluun asti.
Tarkistukset ja korjausyritykset lisäävät AI-kutsuja. Vanhoja raportteja ei muuteta.
Mallin voi vaihtaa palvelimen `RESEARCH_MODEL`-asetuksella; oletus on
`openai/gpt-4.1-mini`. Mallinvaihto vaikuttaa laatuun ja tokenien hintaan.

Oikeita tuotoksia voi arvioida komennolla `uv run python -m scripts.evaluate_reports demand`
(vaihtoehdot: `demand`, `competition`, `market`). Tämä käyttää API-krediittejä ja
tallentaa testiraportin `.runtime/evaluations/`-kansioon, ei käyttäjien raportteihin.

Paikallinen sovellus käyttää Reactia, FastAPI:a, SQLitea ja CrewAI:ta. Julkaisussa
tarvitaan HTTPS, `COOKIE_SECURE=true`, oikea `ALLOWED_ORIGINS` ja pysyvä tietokantalevy.
Frontendin API-osoitteen voi asettaa `REACT_APP_API_URL`-muuttujalla buildin yhteydessä.
Käytä yhtä backend-prosessia: uudelleenkäynnistys keskeyttää käynnissä olevat tutkimukset.
