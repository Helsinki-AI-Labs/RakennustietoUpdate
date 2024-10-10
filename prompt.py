def create_prompt(new_law_part: str, old_manual_content: str) -> str:
    return f"""
You are tasked with comparing a new construction law text against an existing construction instruction manual to identify sections of the manual that need to be updated. Both documents are in Finnish.

New construction law:
    {new_law_part}

Old construction manual:
  {old_manual_content}

Please follow these steps to complete the task:
1. Carefully read and analyze the new construction law text.
2. Review the old construction instruction manual thoroughly. Pay attention to sections that no longer comply with the new construction law text.
3. Compare the content of the old manual with the new law requirements. Look for discrepancies, outdated information, or sections that no longer comply with the new regulations.
4. For each section of the manual that needs updating, provide the following information:
   a. The section number or title in the old manual
   b. Extract all the text from the section in the old manual that needs to be updated. Return only the extracted section text and nothing else
   c. An explanation of why it needs to be updated, referencing the specific part of the new law that necessitates the change
   d. A reference to the relevant section in the new law

Remember that all text in both the new law and the old manual is in Finnish. Provide your analysis and report in Finnish as well. If you don't find any outdated sections, return the following: "Ei päivitettävää".

Below you will find examples of the updates delimited by "####"

Example 1:

####
a. Otsikko:
3.1 Makuuhuoneet

b. Nykyinen sisältö:
3.1 Makuuhuoneet
Mitoitus
Suomalaisessa asuntorakentamisessa pinta-alat ovat
melko pieniä ja makuuhuoneet ovat yleensä suhteellisen
tiukasti mitoitettuja.
Makuuhuoneet on totuttu jaottelemaan kahteen ryhmään:
• Suurempiin eli kahden hengen makuuhuoneisiin, koko
noin 10...16 m2
• Pienempiin eli yhdenhengen makuuhuoneisiin, koko
noin 7...12 m2
Sijoittuminen, kulkuyhteydet ja mitoitus
• Makuuhuoneet pyritään sijoittamaan asunnon pohjoisen-
puoleiseen osaan, jotta auringonvalo ja lämpö häiritse-
vät mahdollisimman vähän nukkumista.
• Suora yhteys makuuhuoneista eteis- tai kulkutiloihin pa-
rantaa asunnon käytettävyyttä.
• Makuuhuoneiden välittömään läheisyyteen pyritään si-
joittamaan myös peseytymis- ja wc-tilat.
• Makuuhuoneen viihtyvyyttä lisää kulku makuuhuonees-
ta ulkotiloihin.
• Kahden lapsen iso yhteinen makuuhuone voidaan jakaa
kahdeksi erilliseksi tilaksi.
• Kalustuksen muunneltavuus ja väljä mitoitus tuo jousta-
vuutta.
• Mitoituksella ja esteettömyydellä pystytään ratkaise-
maan myös liikuntarajoitteisten ja ikäihmisten toimimi-
nen asunnossa.

Päivitystarve:
Uuteen lakiin kirjattu, että makuuhuoneessa tulee olla ikkuna luonnon valon saamiseksi.

d. Ehdotus uudeksi sisällöksi:
3.1 Makuuhuoneet
Mitoitus
Suomalaisessa asuntorakentamisessa pinta-alat ovat
melko pieniä ja makuuhuoneet ovat yleensä suhteellisen
tiukasti mitoitettuja.
Makuuhuoneet on totuttu jaottelemaan kahteen ryhmään:
• Suurempiin eli kahden hengen makuuhuoneisiin, koko
noin 10...16 m2
• Pienempiin eli yhdenhengen makuuhuoneisiin, koko
noin 7...12 m2
Sijoittuminen, kulkuyhteydet ja mitoitus
• Makuuhuoneet pyritään sijoittamaan asunnon pohjoisen-
puoleiseen osaan, jotta auringonvalo ja lämpö häiritse-
vät mahdollisimman vähän nukkumista.
• Suora yhteys makuuhuoneista eteis- tai kulkutiloihin pa-
rantaa asunnon käytettävyyttä.
• Makuuhuoneiden välittömään läheisyyteen pyritään si-
joittamaan myös peseytymis- ja wc-tilat.
• Makuuhuoneen viihtyvyyttä lisää kulku makuuhuonees-
ta ulkotiloihin.
• Kahden lapsen iso yhteinen makuuhuone voidaan jakaa
kahdeksi erilliseksi tilaksi.
• Kalustuksen muunneltavuus ja väljä mitoitus tuo jousta-
vuutta.
• Mitoituksella ja esteettömyydellä pystytään ratkaise-
maan myös liikuntarajoitteisten ja ikäihmisten toimimi-
nen asunnossa.
• Makuuhuoneessa tulee olla ikkuna luonnonvalon saamiseksi.

e.Viittaus uuteen lakiin:
40 § Asuin-, majoitus- ja työtilat

####

Example 2:

####

a. Otsikko:
Osa 3.2: Rakennushankkeen jätehuollon suunnittelu- ja ilmoitusvelvoite

b. Nykyinen sisältö:
Rakennushankkeeseen ryhtyvä on velvollinen rakentamista tai purkamista koskevassa lupahakemuksessa tai ilmoituksessa esittämään selvityksen rakennusjätteen määrästä, laadusta ja sen lajittelusta. Hakemuksessa tai ilmoituksessa ilmoitetaan erikseen terveydelle tai ympäristölle vaarallisesta rakennus- tai purkujätteestä ja sen käsittelystä. Purkamista edeltävässä selvityksessä kartoitetaan rakenteista syntyvät jätelajit, erityisesti vaaralliset jätteet, sekä tehdään karkea arvio syntyvistä jätemääristä lajikohtaisesti.

c. Päivitystarve:
Uuden lain 16 §:n mukaan rakennusjätteen selvityksessä tulee ilmoittaa myös arviot syntyvistä purkumateriaaleista, ja tämä selvitys on päivitettävä hankkeen valmistuttua. Lisäksi selvitys on tallennettava Suomen ympäristökeskuksen ylläpitämään tietokantaan. Tämän kohdan tiedot tulee päivittää vastaamaan uusia velvoitteita.

d. Ehdotus uudeksi sisällöksi:
Rakennushankkeeseen ryhtyvä on velvollinen rakentamista tai purkamista koskevassa lupahakemuksessa tai ilmoituksessa esittämään selvityksen rakennusjätteen määrästä, laadusta, sen lajittelusta sekä arviot syntyvistä purkumateriaaleista. Tämä selvitys tulee päivittää hankkeen valmistuttua. Lisäksi selvitys on tallennettava Suomen ympäristökeskuksen ylläpitämään tietokantaan.

e.Viittaus uuteen lakiin:
16 § Purkumateriaali- ja rakennusjäteselvitys
####

Example 3:

####

a. Otsikko:
3.1 Makuuhuoneet

b. Nykyinen sisältö:
Ääneneristys
Asuinrakennuksessa tilojen sijoittelu on ääniteknisen suunnittelun perusta. Hiljaisuutta vaativat huoneet, kuten makuu- ja olohuoneet, sijoitetaan mahdollisimman kauas tiloista, joissa on äänekkäämpää toimintaa, kuten porrashuoneista ja viereisen tai yläpuolisen huoneiston wc- ja kylpyhuonetiloista ja keittiöstä. Kylpyhuoneet, keittiöt, vaatehuoneet yms. porrashuoneen ja makuuhuoneen välillä suojaavat makuuhuoneita porrashuonemelulta. Oleskelu- tilojen äänten kuulumista makuutiloihin pystytään vaimentamaan seinä- ja oviratkaisuilla.
Asunnossa tulee ottaa huomioon myös runko- ja askelääneneristysvaatimusten täyttyminen, liikenteen äänet ym. Rakentamishankkeeseen ryhtyvän on huolehdittava, että rakennus ja sen piha- ja oleskelualueet suunnitellaan ja rakennetaan niiden käyttötarkoituksen edellyttämällä tavalla siten, että rakennuksen sekä rakennuspaikan piha- ja oleskelualueiden melualtistus ja ääniolosuhteet eivät vaaranna terveyttä, lepoa eivätkä työntekoa.

c. Päivitystarve:
Uuteen lakiin on kirjattu vaatimus, että melualtistus ja ääniolosuhteet eivät saa vaarantaa terveyttä, lepoa eivätkä työntekoa.

d. Ehdotus uudeksi sisällöksi:
Rakennushankkeeseen ryhtyvä on velvollinen rakentamista tai purkamista koskevassa lupahakemuksessa tai ilmoituksessa esittämään selvityksen rakennusjätteen määrästä, laadusta, sen lajittelusta sekä arviot syntyvistä purkumateriaaleista. Tämä selvitys tulee päivittää hankkeen valmistuttua. Lisäksi selvitys on tallennettava Suomen ympäristökeskuksen ylläpitämään tietokantaan.

e.Viittaus uuteen lakiin:
36 § § Meluntorjunta ja ääniolosuhteet

Begin your analysis now, and present your findings as instructed above.
"""
