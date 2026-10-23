# Railway-julkaisu

Valmistelut eivät luo Railway-palvelua. Docker-kuva palvelee Reactin ja API:n samasta
HTTPS-osoitteesta. Käytä yhtä instanssia ja yhtä worker-prosessia. Esimerkkiraportit
ovat mukana kuvassa; paikallinen tietokanta, avaimet ja lokit eivät kuulu buildiin.

## Palvelun luominen

1. Liitä projektin GitHub-repositorio Railway-palveluun, juurihakemisto projektin juuri.
   Dockerfile havaitaan automaattisesti. Älä aseta erillistä build- tai start-komentoa.
2. Liitä palveluun volume polkuun `/data` ennen ensimmäistä käynnistystä.
3. Aseta Variables:

   | Muuttuja | Arvo |
   | --- | --- |
   | `DATABASE_URL` | `sqlite:////data/app.db` |
   | `DIAGNOSTICS_PATH` | `/data/logs/backend-errors.log` |
   | `OPENAI_API_KEY` | oma salainen avain |
   | `SERPER_API_KEY` | oma salainen avain |
   | `RESEARCH_MODEL` | `openai/gpt-4.1-mini` |
   | `SYNTHESIS_MODEL` | `openai/gpt-4.1` |
   | `COOKIE_SECURE` | `true` |
   | `ALLOWED_ORIGINS` | palvelun tarkka HTTPS-osoite, ei loppukauttaviivaa |
   | `ADMIN_USER_IDS` | tuotannon admin-tilin tunniste |

4. Luo Railway-domain ja aseta se `ALLOWED_ORIGINS`-arvoksi. Käynnistä uusi deploy.
   `PORT` tulee Railwaylta. `railway.toml` määrittää `/health`-tarkistuksen.
   Älä ota käyttöön palvelun nukahtamista. Uudelleenjulkaisu keskeyttää käynnissä
   olevat tutkimukset; tee julkaisut silloin, kun tutkimuksia ei ole käynnissä.
5. Tarkista esimerkit, sivujen suorat osoitteet, kirjautuminen ja historia.
   Tutkimusta ei tarvitse käynnistää käyttöönoton tarkistamiseksi.

## Admin ja kutsut

Paikallista tietokantaa ei kopioida automaattisesti tuotantoon, eikä paikallinen admin
muutu tai poistu. Puhtaassa tuotantotietokannassa tunnisteet ovat erillisiä.
Nykyisen admin-tunnuksen siirto:

1. Paikallisen projektin juuressa:
   `uv run --no-sync python -m scripts.transfer_admin export .private/admin-transfer.json`
   Komento valitsee ainoan `.env`-tiedoston `ADMIN_USER_IDS`-tilin. Jos niitä on useita,
   lisää `--user-id TUNNISTE`. Vienti ei muuta paikallista tiliä.
2. Pidä siirtotiedosto yksityisenä. Se sisältää tunnuksen ja salasanan tiivisteen,
   ei salasanaa, raportteja, istuntoja tai muita käyttäjiä. `.private/` on Gitin ja
   Docker-kuvan ulkopuolella. Älä liitä sisältöä chattiin tai Railwayn build-lokeihin.
3. Lataa tiedosto Railwayn volumen tiedostotyökalulla palvelun `/data/admin-transfer.json`
   -polkuun. Suorita palvelun sisällä Railway SSH:lla:
   `/app/.venv/bin/python -m scripts.transfer_admin import /data/admin-transfer.json`
4. Komento tulostaa uuden tietokannan käyttäjätunnisteen. Aseta se Railwayn
   `ADMIN_USER_IDS`-muuttujaan ja julkaise uudelleen. Käyttäjätunnus ja salasana
   säilyvät samoina, mutta numeerinen tunniste voi vaihtua. Olemassa olevaa
   samannimistä tuotantotiliä ei ylikirjoiteta.
5. Varmista kirjautuminen ja rajattomat ylläpitäjän tutkimuskerrat ilman tutkimuksen
   käynnistämistä. Poista sitten siirtotiedosto sekä palvelimelta että paikallisesti.

Uuden tuotantotilin voi vaihtoehtoisesti luoda kutsulla. Suorita palvelun sisällä
Railway SSH:n kautta `/app/.venv/bin/python -m scripts.create_invite`, käytä koodi
rekisteröitymiseen ja ota oman tilin `user_id` kirjautumisen `/me`-vastauksesta.
Aseta se `ADMIN_USER_IDS`-muuttujaan ja julkaise uudelleen. Älä arvaa tunnistetta.
`railway run` paikallisesti ei liitä tuotantovolumea eikä ole oikea paikka luoda kutsua.

## Varmuuskopiointi ja palautus

Käyttöönotossa 23.10.2026 Railwayn Backups-näkymä ilmoitti uusien varmistusten ja
ajastusten vaativan Pro-tilauksen. Hobby-demossa varmistukset tehdään toistaiseksi
manuaalisesti alla olevalla komennolla ja ladataan myös palvelun ulkopuolelle.
Pysyvä volume ei yksin ole varmuuskopio. Tee SQLite-yhteensopiva tiedostovarmistus
palvelun sisällä testikierrosten ja tärkeiden muutosten jälkeen sekä ennen päivityksiä:

```sh
/app/.venv/bin/python -m scripts.database_backup /data/app.db /data/backups/ennen-paivitysta.db
```

Anna joka varmistukselle uusi nimi. Komento käyttää SQLite backup -rajapintaa ja
varmistaa tiedoston eheyden; se ei ylikirjoita olemassa olevaa kohdetta. Lataa kopio
myös volumen ulkopuolelle Railwayn volumen tiedostotyökaluilla. Kopio samalla
volumella ei yksin suojaa volumen menetykseltä. Varmistukset sisältävät käyttäjätietoja
ja salasanojen tiivisteitä: säilytä yksityisesti, älä lisää Git-repositorioon.

Palautuksen testaus uuteen tiedostoon:

```sh
/app/.venv/bin/python -m scripts.database_backup /data/backups/ennen-paivitysta.db /data/restored.db
```

Varsinaisessa palautuksessa estä tutkimusten aloitus huoltokatkolla, ota tuore varmistus,
luo palautettu tiedosto uudella nimellä ja vaihda `DATABASE_URL` siihen uudessa deployssa.
Älä korvaa käynnissä olevan sovelluksen tietokantatiedostoa. Tarkista kirjautuminen,
historia ja kiintiöt ennen avaamista. Paikallinen palautustesti ei korvaa tuotannon
volumen säilymisen ja Railway-varmistuksen palautuksen tarkistamista.

## Paikallinen tuotantokuvan tarkistus

Dockerin ollessa käytettävissä:

```sh
docker build -t research-demo .
docker volume create research-demo-data
docker run --rm -p 8000:8000 --mount source=research-demo-data,target=/data -e DATABASE_URL=sqlite:////data/app.db -e COOKIE_SECURE=false -e ALLOWED_ORIGINS=http://localhost:8000 research-demo
```

Avaa `http://localhost:8000`. Tämä käynnistys ei tarvitse API-avaimia esimerkkien
lukemiseen; tutkimuksia ei käynnistetä. Käynnistä kontti uudelleen samalla volumella
ja varmista testitilin säilyminen. Paikallisen HTTP-testin `COOKIE_SECURE=false`
ei kuulu Railwayn HTTPS-tuotantoon.

Lähteet: [Dockerfile](https://docs.railway.com/builds/dockerfiles),
[volumet](https://docs.railway.com/volumes),
[healthcheck](https://docs.railway.com/deployments/healthchecks).
