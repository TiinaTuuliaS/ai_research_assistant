# AI Markkinatutkimusassistentti

Kokeellinen portfoliodemo, joka tuottaa verkkolähteisiin perustuvia **kilpailijavertailuja**
ja **markkinatutkimuksia**. Markkinatutkimuksessa voi tarkastella nykytilaa tai kehitystä.
Raportit kuvaavat olemassa olevaa tietoa; ne eivät kehitä käyttäjälle yritysideoita tai strategioita.

## Ominaisuudet

- Tutkimuksen eteneminen ja agenttien välitulokset näkyvät käyttöliittymässä.
- Raporteissa on lähdeviitteet, vertailutaulukot ja tietojen rajaukset.
- Kirjautunut käyttäjä voi palata raportteihinsa, ladata TXT-tiedoston tai tallentaa PDF:n.
- Uuden tilin luominen vaatii kertakäyttöisen kutsukoodin.
- Tavallisella käyttäjätilillä voi aloittaa yhteensä kolme tutkimusta.
- Epäonnistuneesta viimeistelystä voidaan tallentaa erikseen merkitty rajattu kooste.

## Teknologiat

| Osa | Teknologiat |
| --- | --- |
| Käyttöliittymä | React 18, JavaScript, React Router, CSS, Framer Motion |
| Raporttien näyttäminen | React Markdown, remark-gfm; PDF selaimen tulostuksella |
| Backend ja rajapinta | Python, FastAPI, Uvicorn |
| AI-työnkulku | CrewAI 1.15.28, OpenAI-mallit |
| Verkkohaku | Serper API |
| Tietokanta | SQLite, SQLAlchemy |
| Tiedon rakenteet ja asetukset | Pydantic, YAML, python-dotenv |
| Testaus | unittest, Jest, React Testing Library |
| Kehitystyökalut | uv, npm, Create React App |

## Kolmen agentin työnkulku

1. **Tutkija** etsii lähteet ja kokoaa lähdekohtaiset havainnot ehtoineen.
2. **Analyytikko** muodostaa havaintojen perusteella vertailun tai markkinakuvauksen.
3. **Kirjoittaja** muotoilee tulokset luettavaksi, lähteistetyksi raportiksi.

Tutkijan ja analyytikon tiedonsiirto käyttää Pydantic-rakenteita. Lähdetunnisteita,
tukikatkelmia ja päätelmien tukea tarkistetaan ennen raportin tallentamista.

## Paikallinen käynnistys

Tarvitset Python 3.10–3.13:n, uv:n ja Node.js 20+:n. Projektin juuressa:

```powershell
uv sync --locked
npm --prefix ai-research-frontend ci
```

Kopioi `.env.example` tiedostoksi `.env`, jos sitä ei vielä ole. Lisää siihen
`OPENAI_API_KEY` ja `SERPER_API_KEY`. Älä tallenna avaimia versionhallintaan.

```powershell
npm run dev
```

- Käyttöliittymä: http://localhost:3000
- API-dokumentaatio: http://127.0.0.1:8000/docs

Pysäytä palvelut painamalla Ctrl+C. Backendin koodi- ja agenttiohjemuutokset vaativat
uudelleenkäynnistyksen. Vaihtoehtoisesti palvelut voi käynnistää omissa terminaaleissaan
komennoilla `npm run front` ja `npm run backend`; käytä yhtä käynnistystapaa kerrallaan.

## Asetukset ja tallennus

- `RESEARCH_MODEL`: tutkimusmalli, oletuksena `openai/gpt-4.1-mini`.
- `SYNTHESIS_MODEL`: valinnainen erillinen malli analyysiin, kirjoittamiseen ja loppuarviointiin.
  Tyhjänä käytetään tutkimusmallia.
- `ADMIN_USER_IDS`: pilkuin erotetut ylläpitäjien käyttäjätunnisteet ilman tutkimuskertarajaa.
  Asetus ei anna pääsyä muiden käyttäjien raportteihin.

Käyttäjät ja raportit tallentuvat oletuksena paikalliseen `app.db`-tietokantaan.
Tietokanta, `.env` ja `.runtime`-kansio eivät kuulu versionhallintaan.
Tekniset virhelokit ovat tiedostossa `.runtime/backend-errors.log`.

## Testaus

```powershell
uv run --no-sync python -m unittest discover -s tests
npm --prefix ai-research-frontend test -- --watchAll=false --runInBand
npm --prefix ai-research-frontend run build
```

Automaattiset testit eivät tee maksullisia AI-kutsuja. Oikeat tutkimukset käyttävät
OpenAI- ja Serper-palveluita ja aiheuttavat API-kuluja. Erillinen maksullinen arviointiajo:
`uv run python -m scripts.evaluate_reports competition` (tai `market`).
Se tallentaa tulokset `.runtime/evaluations/`-kansioon, ei käyttäjien raporttihistoriaan.

## Rajoitteet

Aineisto koostuu hakutuloskatkelmista ja rajatuista sivuteksteistä. Kartoitus ei ole kattava,
eivätkä lähdeviitteet tai automaattiset testit takaa väitteiden oikeellisuutta.
Mallit voivat yhdistää toimijoiden tietoja väärin tai tehdä lähteen ylittäviä päätelmiä.
Olennaiset hinnat, ehdot ja johtopäätökset on tarkistettava alkuperäisistä lähteistä.

Arviointityö ja tunnetut rajoitteet: [docs/evaluation-notes.md](docs/evaluation-notes.md).

Railwayn käyttöönotto, muuttujat ja tietokannan palautus: [docs/railway.md](docs/railway.md).

## Julkaisuympäristö

Käytä HTTPS:ää, `COOKIE_SECURE=true`-asetusta, oikeaa `ALLOWED_ORIGINS`-arvoa ja pysyvää
tietokantalevyä. Frontendin API-osoite asetetaan buildissä muuttujalla `REACT_APP_API_URL`.
Backend käyttää yhtä prosessia; sen uudelleenkäynnistys keskeyttää käynnissä olevat tutkimukset.

## Projektin rakenne

- `ai-research-frontend/` – käyttöliittymä ja fronttitestit.
- `src/` – API, käyttäjät, tietokanta ja agenttityönkulku.
- `tests/` – backend-testit ja niiden lähdeaineistot.
- `scripts/` – kehityspalvelujen käynnistys ja maksullinen arviointityökalu.
- `docs/` – arvioinnin havainnot ja tunnetut rajat.

## Testaajien kutsuminen

Luo yksi kutsukoodi projektin juuressa: `uv run --no-sync python -m scripts.create_invite`.
Komento tulostaa koodin kerran; toimita se testaajalle itse. Tietokantaan tallentuu
vain koodin tiiviste. Koodi kelpaa yhden tilin luomiseen ja tili saa kolme tutkimusta.
Nykyiset tilit ja ylläpitäjän oikeudet säilyvät. Julkiset esimerkit eivät vaadi kutsua.
Vanha `/research`-rajapinta on suljettu; tutkimukset käynnistetään `/research-jobs`-reitillä.
