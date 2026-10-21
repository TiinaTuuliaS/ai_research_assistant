# AI Markkinatutkimusassistentti

Sovellus auttaa kartoittamaan kilpailutarjontaa ja tutkimaan
markkinoiden muutoksia. Kolme AI-agenttia kokoaa havainnot, analyysin ja yhteisen
loppuraportin lähteineen. Työn etenemistä voi seurata käyttöliittymässä.

Tutkimustapoja on kaksi: **kilpailutarjonnan kartoitus** sekä **markkinan tilannekuva ja kehitys**.
Kysyntätutkimusta ei voi enää käynnistää. Aiemmin tallennetut raportit säilyvät historiassa;
vanha kysyntätutkimuksen lomakeluonnos nollataan, eikä sitä muuteta huomaamatta toiseksi tutkimukseksi.
Kysyntätutkimusten keskeytyneitä raportteja ei jatketa uudella työnkululla.
Kilpailukartoitus voi vertailla olemassa olevia vaihtoehtoja ilman omaa yritysideaa.
Erottumista arvioidaan vain käyttäjän pyytäessä sitä.

Rajattu raportti voi perustua yhteen lähteeseen. Lähteiden määrä ei ole luotettavuusmittari.
Sovellus on kokeellinen portfoliodemo: lähdeviitteet ja automaattiset tarkistukset eivät takaa
väitteiden tai päätelmien oikeellisuutta.

Etusivuun voi tutustua vapaasti. Tutkimusten tekeminen ja omien raporttien katselu
vaativat kirjautumisen. Raportin voi ladata tekstinä, tallentaa PDF:ksi selaimen
tulostustoiminnolla tai jakaa siitä otteen.

Käyttäjätilillä voi aloittaa yhteensä kolme tutkimusta kaikista tutkimustavoista.
Jos uusi tutkimus epäonnistuu ennen luettavien osatulosten syntymistä, käyttökerta
palautetaan. Aiemmat tutkimukset lasketaan mukaan. Raja tarkistetaan palvelimella,
ja jäljellä olevat kerrat näkyvät lomakkeessa.
Omia raportteja voi katsella rajan täytyttyäkin.
Uusien tutkimusten aloitusaika näkyy raporttilistassa ja avatussa raportissa.
Aika tallennetaan UTC-muodossa ja näytetään selaimen paikallisessa ajassa.
Vanhoissa raporteissa päivämäärä voi puuttua.

Keskeytyneen tutkimuksen valmistuneet osatulokset näkyvät myös omissa raporteissa.
Jos AI-kirjoittaja tai myöhempi vaihe epäonnistuu mutta tarkistettuja tuloksia on,
sovellus kokoaa niistä ilman uutta AI-kutsua rajatun raportin päätelmineen ja lähteineen.
Se tallentuu omiin raportteihin ja kertoo, että analyysi jäi osittaiseksi.
Kooste säilyttää valmistuneen analyysin tai suosituksen; jos vain havaintoja on valmiina,
päätelmä kertoo tutkimustavan mukaisesti, mitä niistä ei vielä voi ratkaista.
Raakaa lähdetekstiä tai hylättyä luonnosta ei julkaista vararaporttina.
Niistä muodostetaan ilman uutta AI-kutsua kooste, joka merkitään keskeneräiseksi
myös PDF-viennissä. Hylätty kirjoittajan luonnos näkyy erikseen tarkistamattomana.
Jos tutkimuksen aiemmat vaiheet valmistuivat ja lähdeaineisto tallentui,
voit korjata tallennettua loppuraporttiluonnosta kuluttamatta uutta tutkimuskertaa.
Kirjoittaja saa luonnoksen, tarkan hylkäyssyyn ja lähteet. Se ehdottaa vain yksilöityjen
tekstikohtien korvauksia, jotka sovellus soveltaa luonnokseen. Muut kohdat säilyvät
ennallaan ennen tavallista sisältö- ja lähdetarkistusta. Epäselviä tai päällekkäisiä
korvauksia ei sovelleta. Korjaus ei takaa hyväksyntää, jos lähdeaineisto ei riitä.
Korjaus käyttää AI-palvelua ja aiheuttaa ylläpitäjälle API-kuluja, mutta ei tee uusia
verkkohakuja. Vanhoille tutkimuksille uusinta ei ole saatavilla, jos jatkamistietoja
ei tallennettu. Jos mikään vaihe ei valmistunut, sovellus kertoo sen suoraan.

Ylläpitäjän tutkimusrajan voi poistaa palvelimen `ADMIN_USER_IDS`-asetuksella
(pilkuin erotetut olemassa olevien käyttäjien tietokantatunnisteet).
Tunnisteet määritetään erikseen paikallisesti ja Railwayn ympäristömuuttujissa.
Rajattomuus ei anna pääsyä muiden käyttäjien raportteihin.

## Teknologiat

- **React ja JavaScript** – käyttöliittymä, React Router – sivujen reititys.
- **Python ja FastAPI** – backend ja REST-rajapinta.
- **CrewAI 1.15.28 ja OpenAI (GPT-4.1 mini)** – agenttien yhteistyö ja raporttien tuottaminen.
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
Serper-palveluita ja voivat aiheuttaa kustannuksia. Aineistona käytetään hakukatkelmia
ja enintään kuudelta julkiselta lähdesivulta poimittua tekstiä (enintään 8 000 merkkiä
sivulta). Lähdeluettelo kertoo, mistä sivuteksti saatiin ja mikä jäi hakukatkelmaksi.
Sivun lukeminen ei takaa väitteiden oikeellisuutta. Kartoitus ei ole kattava:
löytyneiden toimijoiden määrä ei ole markkinan kokonaismäärä.

Tutkija palauttaa molemmissa tutkimustavoissa Pydantic-validoidun
`ResearchResult`-olion: aihe ja havainnot (otsikko, yhteenveto, lähdetunniste,
osuvuus 1–10, tiedon tyyppi, kohde, alue, ajankohta ja
rajaukset). Tuntemattomia alueita ja ajankohtia ei täydennetä oletuksilla.
CrewAI muodostaa olion `output_pydantic`-asetuksen avulla. Jokaiselle lähteelle annetaan
pysyvä tunniste tutkimuksen sisällä, kuten `S1`. Agentit käyttävät tunnisteita, ja
palvelin muodostaa linkit alkuperäisistä osoitteista. Vanhat URL-pohjaiset tallenteet toimivat edelleen.
Jokainen uusi havainto sisältää yksityisen `supporting_text`-tukikatkelman omasta
lähteestään. Palvelin tarkistaa, että katkelma löytyy tallennetusta aineistosta.
Ajanjaksolle annetaan erillinen `period_support`; tuntematon ajankohta jätetään tyhjäksi.
Havainnon vuosilukua ei hyväksytä, jos se puuttuu valituista tukiteksteistä.
Lähteen julkaisupäivä ja hakupäivä säilytetään erillään havainnon ajanjaksosta.
Julkaisupäivä poimitaan eksplisiittisestä metatiedosta tai päivätystä artikkeliosoitteesta;
puuttuvaa päivää ei arvata. Katkelmat tallentuvat yksityiseen tarkistusaineistoon, eivät raporttitekstiin.
Rakennevirhettä yritetään korjata kerran. Tuntemattomaan tai tyhjään lähteeseen
viittaava havainto jätetään pois; muut havainnot jatkavat.
Jos yhtään havaintoa ei jää, tutkijan tulos kertoo aineiston puutteesta.
Erillinen AI-tarkistus arvioi, tukeeko lähde
havainnon sisältöä ja luokittelua. Raportissa näkyvät omin sanoin kirjoitetut havainnot
ja niiden rajaukset, eivät lähdekatkelmat tai sisäiset hylkäyslistat.
Validoiduista
kentistä muodostettu teksti välitetään nykyisille seuraaville agenteille ja
raporttinäkymään. Havaintojen tunnisteet ja rajaukset säilyvät sisältötarkistuksessa
ja tallennetuissa jatkamistiedoissa. Osuvuus ei tarkoita lähteen luotettavuutta.
Tutkija etsii myös kansainvälisiä kehityssuuntia. Havainto erottaa nykytilan,
havaitun muutoksen, ennusteen ja yksittäisen esimerkin sekä kertoo alueen,
ajankohdan ja paikallisen soveltamisen rajat.
Valittujen lähteiden käyttötarkoitus ja valintaperustelu tallennetaan tutkimuksen
lähdeaineistoon. Käytettyjen lähteiden perustelut näkyvät lähdeluettelossa.
Analyytikon `AnalysisResult` sisältää vastauksen, havaintotunnisteisiin sidotut
päätelmät, epävarmuudet, suosituksen ja vaihtoehdon. Kilpailijavertailussa se
erottaa osoitetun eron, yhteisen ominaisuuden ja testattavan ehdotuksen.
Tuntemattomat havaintotunnisteet ja väärä tutkimustapa hylätään. Viittauksen
olemassaolo ei yksin todista päätelmän oikeellisuutta.
Puutteellista tukikatkelmaa tai ajankohdan perustelua korjataan havaintokohtaisesti:
yksi puutteellinen havainto ei pysäytä koko tutkijavaihetta. Korjaamatta jäänyt
havainto jätetään pois ja muut havainnot säilyvät. Rakenteeltaan virheellinen
kokonaistulos voi edelleen keskeyttää vaiheen yhden korjausyrityksen jälkeen.
Havaittu muutos tarvitsee lähteen tukeman ajankohdan. Analyytikon päätelmän
vuosia verrataan juuri sen viittaamien havaintojen tukiteksteihin; käyttäjän
pyytämä vuosiväli ei itsessään ole näyttöä kehityksestä. Tunnistettu näytön puutetta
kuvaava lause saa nimetä pyydetyn ajanjakson. Tunnistus kattaa määritellyt
suomen- ja englanninkieliset ilmaukset, ei kaikkia mahdollisia sanamuotoja.
Loppuraportin johtopäätökset tarkistetaan alkuperäisiä havaintoja ja lähteitä vasten.
Käyttäjän lähtökuvauksen oletukset erotetaan lähdetiedosta. Sisältötarkistuksen
muokkaama raportti tarkistetaan vielä kerran ja sen korjaukset säilytetään;
pelkkä toinen tekstikorjaus ei hylkää raporttia. Lähdeviitteet tarkistetaan tämän
jälkeen. Nämä tarkistukset lisäävät AI-kutsuja, eivätkä takaa virheettömyyttä.

Loppuraportti tarkistetaan erillisellä mallikutsulla. Tarkistus arvioi kielen selkeyttä, aiheen
mukaista sisältöä ja väitteiden tukea hyväksytyissä havainnoissa ja niiden tukikatkelmissa sekä korjaa sanamuotoja
ja poistaa perusteettomia väitteitä. Se ei saa koko tallennettua sivutekstiä, joten
ensimmäisessä havaintotarkistuksessa hyväksytty virhetulkinta voi jäädä tunnistamatta.
Mallin tekemä tarkistus ei takaa virheettömyyttä.
Hylättyä välitulosta ja loppuraporttia yritetään korjata kerran.
Hylätystä tutkimushavainnosta yritetään kerran säilyttää suppeampi, saman lähteen
tukema havainto. Korjattu havainto tarkistetaan uudelleen. Tarjontahavainto ei
edellytä näyttöä kysynnästä. Tämä korjaus voi lisätä enintään kaksi AI-kutsua.
Varakooste tunnistaa myös tavalliset lähdeosoitteet ja tarkistaa ne tallennetuista lähteistä.
Jos tutkijan havaintojen sisältötarkistus palauttaa virheellisen rakenteen tai
puutteellisen arviolistan, vain tarkistus uusitaan kerran; verkkohakua ei toisteta.
Yhden tutkimuksen verkkohakutyökalua voi kutsua enintään kuusi kertaa palveluun asti.
Tutkija valitsee hakutuloksista luettavat alkuperäiset sivut
aiheen mukaan. Sivulukuja tehdään enintään kuusi samassa tutkimusvaiheessa. Muualla toimivat vertailukohteet erotetaan paikallisesta näytöstä.
Havaintojen tarkistuksessa jokaisen väitteen mukana kulkee vain sen oman lähteen
aineisto. Tarkistus arvioi erikseen alueellisen yleistyksen ja lähteen riittävyyden.
Jos viimeistely epäonnistuu, varakooste voidaan tallentaa raportiksi. Hylätty luonnos
ja tarkistuksen perustelu säilyvät erikseen tutkimuksen yksityisissä jatkamistiedoissa.
Tarkistukset ja korjausyritykset lisäävät AI-kutsuja. Vanhoja raportteja ei muuteta.
Mallin voi vaihtaa palvelimen `RESEARCH_MODEL`-asetuksella; oletus on
`openai/gpt-4.1-mini`. Mallinvaihto vaikuttaa laatuun ja tokenien hintaan.
Analyysille, kirjoittajalle ja loppuraportin sisältötarkistukselle voi valita
erikseen mallin, esimerkiksi `SYNTHESIS_MODEL=openai/gpt-4.1`.
Tyhjä asetus käyttää tutkimusmallia kaikissa vaiheissa. Vahvempi malli kasvattaa
API-kuluja; vertailukokeessa se paransi päätelmien viimeistelyä, mutta ei poista
lähteiden arvioinnin tarvetta. Malliasetus ei muuta aiemmin tallennettuja raportteja.

Havaintojen lähdetuki tarkistetaan erillään liiketoimintakysymyksestä: oikea
tarjontahavainto voi säilyä, vaikka se ei osoita maksavaa kysyntää. Virheellinen
tukikatkelma voidaan korjata kerran saman lähteen tallennetusta tekstistä
tutkimusvaiheessa; korjattu havainto tarkistetaan edelleen.
Tukikatkelman korjaus voi lisätä enintään yhden AI-kutsun tutkimusvaiheeseen.
Loppuraportin sisältötarkistus saa hyväksytyt havainnot tukiteksteineen,
ei koko hakuaineistoa. Havaintojen puuttuminen ei osoita tiedon puuttumista maailmasta.

Jos valittu lähde jäi ilman hyväksyttyä havaintoa, siitä voidaan poimia yksi
rajattu havainto erillisellä AI-kutsulla. Tämä tehdään enintään kuudelle valitulle
lähteelle niiden jo tallennetusta tekstistä, ilman uusia verkkohakuja. Malli
valitsee numeroidun tekstikohdan ja palvelin liittää alkuperäisen tukitekstin.
Tekstikohdissa säilytetään myös viereisten virkkeiden asiayhteys.
Lähteen osoite auttaa erottamaan julkaisijan sen mainitsemista toimittajista.
Oikein rajattu toisen kaupungin tai maan esimerkki kelpaa vertailuaineistoksi;
sen ei tarvitse osoittaa paikallista kysyntää. Lähteiden alkuperäiset tunnisteet
säilyvät myös analyysin linkeissä, vaikka numeroinnissa olisi aukkoja.
Poimitut havainnot tarkistetaan yhdessä ennen analyysia. Tämä voi lisätä enintään
kuusi poimintakutsua ja sisältötarkistuksen (virheellisen tarkistusrakenteen
uusinta korkeintaan kerran). Hylätyt poiminnat voivat käyttää saman yhden
rajauskorjauksen ja uusintatarkistuksen kuin tutkijan alkuperäiset havainnot:
esimerkiksi väärä vuosiluku voidaan poistaa menettämättä oikeaa tarjontatietoa.
Tämä lisää enintään kaksi mallikutsua, tai kolme jos uusintatarkistuksen rakennevirhe korjataan.
Jos hyväksyttyjä havaintoja ei jää, analyysia ei
käynnistetä tyhjällä aineistolla ja tutkimuskerta palautetaan.

Oikeita tuotoksia voi arvioida komennolla `uv run python -m scripts.evaluate_reports competition`
(vaihtoehdot: `competition`, `market`). Tämä käyttää API-krediittejä ja
tallentaa testiraportin `.runtime/evaluations/`-kansioon, ei käyttäjien raportteihin.

Paikallinen sovellus käyttää Reactia, FastAPI:a, SQLitea ja CrewAI:ta. Julkaisussa
tarvitaan HTTPS, `COOKIE_SECURE=true`, oikea `ALLOWED_ORIGINS` ja pysyvä tietokantalevy.
Frontendin API-osoitteen voi asettaa `REACT_APP_API_URL`-muuttujalla buildin yhteydessä.
Käytä yhtä backend-prosessia: uudelleenkäynnistys keskeyttää käynnissä olevat tutkimukset.

Tutkimusten tekniset virhetiedot tallentuvat tiedostoon `.runtime/backend-errors.log`,
joten ne säilyvät terminaalin sulkemisen jälkeen. Loki sisältää virhetyypin,
koodikohdat ja validoinnissa epäonnistuneet kentät, ei raporttisisältöä tai API-avaimia.
Lokit kiertävät automaattisesti (enintään kolme noin 1 Mt:n tiedostoa).

Tutkimuksessa on kolme agenttia: tutkija kokoaa lähteistetyt havainnot ja kehityssuunnat, analyytikko muodostaa päätelmän ja suosituksen, ja kirjoittaja viimeistelee raportin. Tutkimustavat ovat kilpailutarjonnan kartoitus sekä markkinan tilannekuva ja kehitys. Tutkijan ja analyytikon tulokset validoidaan Pydantic-malleilla.
