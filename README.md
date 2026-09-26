# AI Markkinatutkimusassistentti

React-käyttöliittymä, FastAPI-palvelin, SQLite-tietokanta ja viiden CrewAI-agentin
tutkimusprosessi. Agentit keräävät tietoa, tutkivat trendejä, analysoivat markkinoita,
muodostavat strategian ja kirjoittavat lähteistetyn raportin.

## Käynnistys

Suorita komennot projektin juuresta (`ai_research_assistant`).

**Frontti ja backend samalla komennolla:**

```powershell
npm run dev
```

**Tai erikseen kahdessa terminaalissa:**

```powershell
npm run front
```

```powershell
npm run backend
```

Sovellus: http://localhost:3000 · API: http://127.0.0.1:8000/docs.
Pysäytä Ctrl+C:llä. `npm run dev` pysäyttää molemmat palvelut yhdessä.
Jos portti on jo käytössä, pysäytä aiempi palvelin ensin; komento ei sulje sitä puolestasi.
Backendin koodimuutosten jälkeen pysäytä ja käynnistä se uudelleen. Automaattinen
uudelleenkäynnistys on pois käytöstä, jotta tiedoston tallennus ei keskeytä AI-tutkimusta.
Juuren käynnistyskomennot eivät tarvitse erillistä `npm install` -asennusta.

### Ensimmäinen käyttökerta

Python >=3.10,<3.14 ja Node >=20. Python-paketit hallitaan uv:lla.

1. `uv sync`
2. Kopioi `.env.example` tiedostoksi `.env`, jos omaa `.env`-tiedostoa ei vielä ole.
   Aseta `OPENAI_API_KEY` ja `SERPER_API_KEY`. Älä tallenna avaimia Gitiin.
3. Asenna frontendin paketit projektin juuresta: `npm --prefix ai-research-frontend install`.
4. Käynnistä molemmat palvelut: `npm run dev`.
5. Avaa http://127.0.0.1:3000 tai http://localhost:3000.

Käyttöliittymä käyttää oletuksena selaimen omaa hostnamea ja porttia 8000,
jotta evästeet toimivat sekä localhost- että 127.0.0.1-osoitteilla.
`REACT_APP_API_URL` voi korvata rajapinnan osoitteen käyttöliittymää käynnistettäessä
tai käännettäessä. Backendin `ALLOWED_ORIGINS` on pilkuin erotettu sallittujen
käyttöliittymäosoitteiden lista. HTTPS-käytössä aseta `COOKIE_SECURE=true` ja käytä
käyttöliittymälle ja API:lle samaa sivustoa (SameSite=strict).

## Kirjautuminen ja tiedot

### Omat liiketoimintasuunnitelmat (ensimmäinen vaihe)

`/plans`-sivulla käyttäjä luo nimetyn suunnitelman, muokkaa kuutta osiota ja tallentaa
luonnoksia tai hyväksyy osiot erikseen. Näkymä näyttää hyväksyttyjen osioiden määrän,
rakentuvan kokonaisuuden ja viimeiset 50 tallennettua versiota sisältöineen.
Aiemman osion sisällön muuttaminen merkitsee myöhemmät hyväksytyt osiot tarkistettaviksi.
Tekstit säilyvät. Valmius tarkoittaa käyttäjän hyväksyntöjä, ei liikeidean validointia.

Suunnitelmat ja muuttumattomat versiot tallentuvat `business_plans`- ja
`plan_revisions`-tauluihin. Taulut luodaan backendin käynnistyessä. Kaikki reitit
vaativat omistajan istunnon. Versiotarkistus estää vanhan välilehden ylikirjoituksen.
Ensimmäinen vaihe ei kutsu agentteja, liitä tutkimuksia automaattisesti tai laske
talousennusteita. Tutkimusapu ja laskuri voidaan liittää myöhemmin osioihin.

Etusivu ja havainnollistava esimerkkiraportti ovat julkisia. Tutkimuksen tekeminen
ja omien raporttien katselu vaativat kirjautumisen. Tutkimuslomakkeessa annetaan aihe,
päätöksen tavoite, kohdemarkkina/asiakkaat ja valinnainen kokeilubudjetti euroina.
Nollabudjetti tarkoittaa kokeilua ilman ostoja; tyhjä budjetti ei tarkoita nollaa.
Lomakkeen luonnos säilyy välilehden sessionStorage-muistissa kirjautumisen,
rekisteröitymisen ja sivun päivityksen yli. Uloskirjautuminen poistaa luonnoksen.
Kirjautumisen jälkeen käyttäjä käynnistää tutkimuksen itse; kirjautuminen ei tee maksullista hakua.

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

`config/deliverables.yaml` määrittää jokaiselle tutkimustavalle viisi erillistä
lopputulosta. API välittää tutkimustavan erillisenä tunnisteena; Crew lisää vastaavan
tehtävänannon sekä tehtävän kuvaukseen että odotettuun lopputulokseen. Tutkija kokoaa
näytön, trendianalyytikko ajalliset muutokset ja vastasignaalit, analyytikko arvioi
päätelmien kestävyyden, strategi tuottaa konkreettiset päätösvaihtoehdot ja kirjoittaja
yhdistää tulokset. Mallit eivät ole riippumattomia asiantuntijoita eikä ohjeistus
takaa analyysin laatua. Testit varmistavat työnjaon välittymisen, eivät mallin vastauksia.

Tutkimusohjeet tavoittelevat 5–8 käyttökelpoista lähdettä ja vähintään kahta
riippumatonta näyttölähdettä kaupallisten tuotesivujen lisäksi. Nämä ovat haun
tavoitteita, eivät ohjelmallisesti varmennettu laatutakuu. Tutkijalle ja trendi-
analyytikolle ohjeistetaan kummallekin enintään kolme kohdennettua hakua; tämä
on mallille annettu ohje eikä tekninen kulutusraja. Puuttuva näyttö raportoidaan.
Loppuraporttiin pyydetään näytön arviointiosio ja lähdekohtaiset selitteet.
Jos ne puuttuvat, tarkistin lisää näkyvän puutehuomion; esitystapa tai selitteen
sanamäärä ei kaada raporttia. Puuttuvat lähdeluettelomerkinnät täydennetään vain
tekstissä käytetyistä, kyseisen ajon hakutuloksissa tunnetuista lähteistä.
Tuntemattomat linkit ja liian vähäinen tekstin lähteistys hylätään edelleen.
Alle viisi tekstissä käytettyä lähdettä tuo näkyviin suppean lähdepohjan huomion.
Selitteet ovat mallin arvioita: tarkistin varmistaa niiden olemassaolon, ei laatua.
Sovellus lukee edelleen hakutuloskatkelmia, ei kokonaisia lähdesivuja.

Lomakkeessa on kolme tutkimustapaa: idean kysyntä, kilpailijavertailu ja markkinan
kartoitus. Valinta vaihtaa kysymykset ja palvelimen muodostamat agenttien painotukset.
Kilpailijoiden nimet ovat valinnaisia; tyhjän kentän tapauksessa agentit etsivät ne.
Budjetti on valinnainen lisätieto. Eri tutkimustapojen luonnokset säilyvät vaihdettaessa,
mutta piilotettuja muiden tapojen vastauksia ei lähetetä tutkimukseen.

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
odotusnäkymä näyttää oikeisiin tehtävätapahtumiin perustuvan edistymisen.

Uusissa raporteissa tutkijan, trendianalyytikon, markkina-analyytikon ja strategin
omat vastaukset ovat avattavia osioita. Niitä seuraavat tiivis yhdistetty loppuraportti
ja lähteet. Päiväkohtaisia suunnitelmia tai työpohjia ei enää vaadita. Julkinen
esimerkki havainnollistaa rakennetta eikä esitä tehtyä tutkimusta.

Käyttöliittymä käynnistää työn `POST /research-jobs` -reitillä ja hakee tilan
`GET /research-jobs/{id}` -reitiltä noin sekunnin välein. Molemmat vaativat istunnon;
vain omistaja saa työn tiedot. Agentin aloitus tulee CrewAI:n TaskStartedEventistä,
valmistuminen tehtävän callbackista tarkistusten jälkeen. Palkki kuvaa tehtäviä,
ei aika-arviota. Agenttien vastaukset säilyvät tietokannassa myös historiaa varten.
Saman välilehden päivitys palauttaa seurannan. Verkkovirheestä jatkaminen hakee
saman työn tilan eikä käynnistä uutta maksullista tutkimusta.

Taustatyöt toimivat API-prosessissa: käytä yhtä uvicorn-workeria / palvelininstanssia.
Kerrallaan sallitaan enintään kaksi työtä ja yksi per käyttäjä. Uudelleenkäynnistys
merkitsee keskeneräiset työt keskeytyneiksi; niitä ei ajeta automaattisesti uudelleen.
Usean instanssin julkaisu vaatii erillisen työjonon. Vanha synkroninen `/research`
on yhteensopivuusreitti ilman agenttikohtaista seurantaa; käyttöliittymä ei käytä sitä.

Reactissa sekä uusi raportti että historiasta avattu raportti voidaan ladata TXT:nä
tai tallentaa PDF:ksi selaimen tulostusikkunan kautta. PDF sisältää agenttien vastaukset,
loppuraportin ja lähteet. Jaa-painike käyttää laitteen jakovalikkoa, jos se on saatavilla.
Sähköposti- ja WhatsApp-vaihtoehdot avaavat lyhyen otteen viestiluonnoksena; PDF-liite
lisätään itse. Sovellus ei julkaise raporttia tai lähetä viestiä automaattisesti.
Erillinen Gradio-käyttöliittymä
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
