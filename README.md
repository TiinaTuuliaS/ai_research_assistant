# AI Markkinatutkimusassistentti

React-käyttöliittymä, FastAPI-palvelin, SQLite-tietokanta ja viiden CrewAI-agentin
tutkimusprosessi. Agentit keräävät tietoa, tutkivat trendejä, analysoivat markkinoita,
muodostavat strategian ja kirjoittavat lähteistetyn raportin.

## Käynnistys

Python >=3.10,<3.14 ja Node >=20. Python-paketit hallitaan uv:lla.

1. `uv sync`
2. Kopioi `.env.example` tiedostoksi `.env`, jos omaa `.env`-tiedostoa ei vielä ole.
   Aseta `OPENAI_API_KEY` ja `SERPER_API_KEY`. Älä tallenna avaimia Gitiin.
3. Käynnistä projektin juuresta backend:
   `uv run uvicorn src.api:app --host 127.0.0.1 --port 8000`
4. Avaa toinen pääte hakemistoon `ai-research-frontend`, suorita `npm install`
   ja `npm start`.
5. Avaa http://127.0.0.1:3000 tai http://localhost:3000.

Käyttöliittymä käyttää oletuksena selaimen omaa hostnamea ja porttia 8000,
jotta evästeet toimivat sekä localhost- että 127.0.0.1-osoitteilla.
`REACT_APP_API_URL` voi korvata rajapinnan osoitteen käyttöliittymää käynnistettäessä
tai käännettäessä. Backendin `ALLOWED_ORIGINS` on pilkuin erotettu sallittujen
käyttöliittymäosoitteiden lista. HTTPS-käytössä aseta `COOKIE_SECURE=true` ja käytä
käyttöliittymälle ja API:lle samaa sivustoa (SameSite=strict).

## Kirjautuminen ja tiedot

- Uusi salasana vaatii vähintään 12 merkkiä. Tunnus voi olla sähköposti tai käyttäjätunnus.
- Salasanat tallennetaan suolattuina PBKDF2-SHA256-tiivisteinä (600 000 kierrosta).
- Ensimmäinen päivitetyn backendin käynnistys muuntaa vanhat selväkieliset salasanat
  samassa tietokannassa. Käyttäjätunnisteet, aiemmat salasanat ja raportit säilyvät käytettävinä.
- Istunto on 12 tunnin HttpOnly/SameSite-eväste. Tietokantaan tallennetaan vain
  satunnaisen istuntotunnisteen SHA-256-tiiviste. Uloskirjautuminen mitätöi istunnon.
- Selain tarkistaa kirjautumisen `/me`-reitiltä. localStorage ei sisällä istuntoa
  tai raportteja; vanhat `user`- ja `selectedResearch`-arvot poistetaan.
- Raporttien omistaja määräytyy palvelimen istunnosta. `/researches` palauttaa
  vain omat raportit. Vanha `/researches/{user_id}` vaatii saman omistajan istunnon.
- Kirjoittavat API-pyynnöt vaativat otsakkeen `X-Requested-With: ResearchApp`.
  Selain lähettää evästeen asetuksella `credentials: include`. CORS ja Origin-tarkistus
  sallivat vain määritellyt käyttöliittymät.
- Virheellinen tai vanhentunut istunto palauttaa 401, kielletty pääsy 403,
  virheellinen syöte 422 ja epäonnistunut tutkimus 502.

Tietokannan oletussijainti on projektin juuren `app.db`; `DATABASE_URL` voi korvata sen.
Sovellus ja testit käyttävät SQLitea. Tietokanta on poistettu Gitin seurannasta
ja tietokantatiedostot ohitetaan jatkossa. Tämä ei poista aiempaa `app.db`-sisältöä
Git-historiasta. Jos tietokanta on jo jaettu, siinä olleet salasanat tulee vaihtaa;
Git-historian puhdistusta ei ole tehty automaattisesti.

## Tutkimus ja lähteet

Tutkija ja trendianalyytikko käyttävät Serper-verkkohakua. Jokaisella tutkimusajolla
on oma lähderekisteri, johon kirjataan hausta saadut URL:t, otsikot, katkelmat ja
hakupäivä. Agentit säilyttävät lähteet tehtäväketjun läpi.

Lopullisen raportin tarkistin vaatii vähintään kaksi erillistä lähdelinkkiä
tekstin yhteyteen ja vastaavan Lähteet/Sources-osion. Se hylkää linkit, joita ei
saatu kyseisen ajon hakutuloksista, ja muodostaa lähdeluettelon hakujen metatiedoista.
CrewAI yrittää korjata virheellisen raportin enintään kahdesti; epäonnistunutta
raporttia ei tallenneta. Vanhoja raportteja ei muuteta tai lähteistetä jälkikäteen.

Tarkistus varmistaa linkkien alkuperän, ei jokaisen väitteen totuutta. Kokonaisia
verkkosivuja ei lueta: raportissa kerrotaan hakutuloskatkelmiin perustuvan aineiston
rajoituksista. Julkaisemattomia markkinalukuja ei pidä keksiä. Käyttöliittymän
etenemispalkki on ajastettu arvio, ei backendin reaaliaikainen tilatieto.

Reactista raportti ladataan TXT-tiedostona. Erillinen Gradio-käyttöliittymä
(`uv run python -m ai_research_assistant.app`) ja komentorivi (`uv run run_crew`)
tukevat TXT/PDF-tallennusta. Ne ovat paikallisia vaihtoehtoja, eivät autentikoidun
FastAPI-palvelun reittejä; älä julkaise Gradio-sovellusta erikseen ilman suojausta.

## Testit

Projektin juuressa:

```powershell
uv run python -m unittest discover -s tests -v
```

Testit käyttävät erillistä tilapäistietokantaa ja korvaavat ulkoisen tutkimusajon.
Ne tarkistavat salasanojen muunnoksen, istunnot, uloskirjautumisen, vanhenemisen,
käyttöoikeudet, CSRF-tarkistukset sekä lähdelinkkien alkuperän. Ne eivät veloita
tekoäly- tai hakupalveluita eivätkä muuta omaa `app.db`-tietokantaa.

Hakemistossa `ai-research-frontend`:

```powershell
npm test -- --watchAll=false --runInBand
npm run build
```

Käyttöliittymätestit kattavat historian hakujen määrän, vanhojen tietojen erottelun,
pyyntöjen keskeytyksen, virhetilat ja istunnon palautuksen/uloskirjautumisen.
