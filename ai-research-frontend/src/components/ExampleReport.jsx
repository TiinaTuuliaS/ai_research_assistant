export default function ExampleReport() {
  const examples = [
    ["Tutkija", "Kilpailutilanne", "Tässä kuvitteellisessa tapauksessa palvelu A tarjoaa harjoitusohjelmia ja palvelu B harjoituspäiväkirjan sekä haasteita. Pelillisyys ei siis yksin olisi selvä erottautumistekijä. Tuotekuvaukset kertoisivat ominaisuuksista, mutta eivät siitä, miksi asiakkaat lopettavat käytön tai mitä he kaipaavat."],
    ["Trendianalyytikko", "Kiinnostus ei vielä osoita muutosta", "Oletetaan, että löydetty tutkimus käsittelee liikuntasovellusten käyttöä yleisesti. Se voisi auttaa ymmärtämään käyttömotiiveja, mutta ilman vertailua eri ajankohtiin siitä ei voisi päätellä kysynnän kasvua. Kansainvälistä tulosta ei myöskään voisi suoraan yleistää suomalaisiin 19–45-vuotiaisiin naisiin."],
    ["Markkina-analyytikko", "Kysyntä jää avoimeksi", "Kilpailijoiden ominaisuudet ja yleinen käyttötutkimus muodostaisivat epäsuoraa näyttöä. Ratkaiseva tieto puuttuisi: kokeeko valittu kohderyhmä kuntosaliharjoittelun jatkuvuuden ongelmaksi, auttaako ehdotettu ratkaisu siihen ja olisiko siitä halukkuutta maksaa? Näiden puuttuessa myönteinen kysyntäarvio olisi liian vahva."],
    ["Strategi", "Rajaa lupaus ennen rakentamista", "Esimerkin perusteella selvittäisin ensin, onko harjoittelurutiinin ylläpito kohderyhmälle tärkeä ratkaisematon ongelma. En suosittelisi laajan sovelluksen rakentamista pelkän kilpailijalistan perusteella. Mahdollinen suunta olisi aloittelijan harjoittelurutiinin tukeminen; tämä on testattava oletus, ei löydetty markkinarako."],
  ];
  return <section id="esimerkki" className="example-section">
    <div className="section-heading"><p className="eyebrow">Näe, mitä saat</p><h2>Eri näkökulmat, yksi selkeä kokonaisuus.</h2><p>Tutustu raportin rakenteeseen ilman tunnusta.</p></div>
    <details className="panel example-report">
      <summary><span><span className="tag">Havainnollistava esimerkki</span><strong>Uuden liikeidean kysynnän testaus</strong><span>Agenttien näkemykset · loppuraportti · lähteet</span></span><span aria-hidden="true">＋</span></summary>
      <article className="report-body">
        <p className="notice">Tämä on käsin laadittu, kuvitteellinen esimerkkiraportti. Palvelut A ja B sekä kuvattu tutkimusaineisto ovat esimerkkioletuksia, eivät oikeita tutkimuslöydöksiä.</p>
        <h3>Tutkimuskysymys</h3><p>Olisiko pelilliselle kuntosalisovellukselle kysyntää Suomessa 19–45-vuotiaiden naisten keskuudessa?</p><p><strong>Idea:</strong> harjoittelurutiinia tukeva sovellus, jossa etenemisestä saa palkintoja. <strong>Päätös:</strong> kannattaako idean kehittämiseen panostaa?</p><h3>Agenttien näkemykset</h3>
        {examples.map(([label, title, text], index) => <details key={label} className="agent-perspective" open={index === 0}><summary>{label}<span>{title}</span></summary><p>{text}</p></details>)}
        <h3>Yhdistetty loppuraportti</h3>
        <p>Kysyntää ei voi tämän esimerkkiaineiston perusteella vahvistaa. Vastaavia ominaisuuksia olisi jo tarjolla, joten pelillisyys yksin ei perustelisi uuden sovelluksen tarvetta. Kiinnostavin avoin kysymys koskisi harjoittelurutiinin ylläpitoa ja nykyisten ratkaisujen puutteita.</p>
        <p>Suositus olisi selvittää yksi asia ennen laajaa toteutusta: mikä nykyisessä harjoittelun tukemisessa jää kohderyhmältä ratkaisematta? Tämän jälkeen voisi arvioida, ratkaiseeko ehdotettu sovellus juuri sen. Aineisto ei vielä antaisi perustetta myyntiennusteelle tai kannattavuusarviolle.</p>
        <h3>Näytön vahvuus ja puutteet</h3>
        <ul><li><strong>Ominaisuudet:</strong> kilpailijan oma tuotekuvaus voisi tukea ominaisuusvertailua.</li><li><strong>Käyttäytyminen:</strong> alkuperäinen käyttötutkimus voisi selittää motiiveja vain tutkimansa väestön osalta.</li><li><strong>Kysyntä ja maksuhalukkuus:</strong> esimerkin kohderyhmää suoraan koskeva näyttö puuttuisi.</li></ul>
        <h3>Lähteet ja niiden käyttötarkoitus</h3>
        <p>Alla on esimerkki lähteiden arvioinnista. Nämä eivät ole todellisia lähdeviitteitä. Oikeassa raportissa mukana ovat löydetyt linkit ja hakupäivät.</p>
        <ul><li><strong>Palvelun A tuotesivu — kaupallinen lähde.</strong> Tukisi tietoa palvelun ilmoittamista ominaisuuksista. Ei osoittaisi käyttäjätyytyväisyyttä tai uuden tuotteen kysyntää.</li>
        <li><strong>Alkuperäinen sovellusten käyttötutkimus — riippumaton aineisto, jos sidonnaisuudet on tarkistettu.</strong> Menetelmä, otos, julkaisuvuosi ja kohdemaa ratkaisisivat, kuinka hyvin tulos soveltuu kysymykseen.</li>
        <li><strong>Paikallinen liikuntatilasto — taustatieto.</strong> Voisi kuvata harrastamista valitussa väestössä. Ei mittaisi tämän sovelluksen ostohalukkuutta.</li></ul>
        <a className="button primary" href="#tutkimus">Valmistele oma tutkimus ↑</a>
      </article>
    </details>
  </section>;
}
