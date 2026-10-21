export default function ExampleReport() {
  const examples = [
    ["Tutkija", "Lähdekohtaiset havainnot", "Kuvitteellisen palvelun A hinnasto ilmoittaa työpisteen päivähinnan. Palvelu B ilmoittaa vain kuukausihinnan. Hintoja ei voi verrata saman käyttöjakson kustannuksina."],
    ["Markkina-analyytikko", "Vertailun rajat", "A:n ilmoittama päiväkäyttö vastaisi satunnaisen työskentelyn tarpeeseen. B:n päiväkäytön mahdollisuutta ei tunneta. Puuttuva hinnastotieto ei osoita palvelun puuttumista."],
    ["Raportin kirjoittaja", "Perusteltu yhteenveto", "Päiväkäytön vertailuun tarvittaisiin B:n ehdot. Aineisto ei osoittaisi A:ta halvimmaksi tai laadukkaimmaksi vaihtoehdoksi."],
  ];
  return <section id="esimerkki" className="example-section">
    <div className="section-heading"><p className="eyebrow">Näe, mitä saat</p><h2>Eri näkökulmat, yksi selkeä kokonaisuus.</h2><p>Tutustu raportin rakenteeseen ilman tunnusta.</p></div>
    <details className="panel example-report">
      <summary><span><span className="tag">Havainnollistava esimerkki</span><strong>Coworking-palvelujen tarjonnan vertailu</strong><span>Kolme agenttia · loppuraportti · lähteet</span></span><span aria-hidden="true">＋</span></summary>
      <article className="report-body">
        <p className="notice">Tämä on käsin laadittu, kuvitteellinen esimerkki. Palvelut A ja B eivät ole oikeita tutkimuslöydöksiä.</p>
        <h3>Tutkimuskysymys</h3><p>Mitä coworking-vaihtoehtoja satunnaiseen työskentelyyn on ja mitä niiden hinnoista ja ehdoista tiedetään?</p>
        <h3>Agenttien näkemykset</h3>
        {examples.map(([label, title, text], index) => <details key={label} className="agent-perspective" open={index === 0}><summary>{label}<span>{title}</span></summary><p>{text}</p></details>)}
        <h3>Yhdistetty loppuraportti</h3><p>Palvelusta A löytyisi päiväkäytön hintatieto, B:stä vain kuukausihinta. Vaihtoehtojen kokonaiskustannuksia ei voisi vielä verrata. Seuraavaksi olisi tarkistettava B:n päiväkäytön saatavuus ja molempien palvelujen käyttöehdot.</p>
        <h3>Näytön vahvuus ja puutteet</h3><p>Palveluntarjoajan hinnasto tukisi ilmoitettua hintaa ja sen ehtoja. Se ei osoittaisi palvelun laatua tai koko markkinan hintatasoa.</p>
        <h3>Lähteet ja niiden käyttötarkoitus</h3><p>Esimerkkilähteet olisivat A:n päivähinnasto ja B:n jäsenyysehdot. Oikeassa raportissa mukana ovat löydetyt lähdelinkit ja hakupäivät.</p>
        <a className="button primary" href="#tutkimus">Valmistele oma tutkimus ↑</a>
      </article>
    </details>
  </section>;
}
