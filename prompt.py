def create_prompt(new_law_part: str, old_manual_content: str) -> str:
    return f"""
You are given an update Finnish construction law and a section of an existing construction manual. 
You task is to compare the new construction law text against an existing construction instruction manual to identify sections of the manual that need to be updated. Both documents are in Finnish.

New construction law:
    {new_law_part}

Old construction manual section:
  {old_manual_content}

Please follow these steps to complete the task:
1. Carefully read and analyze the new construction law text.
2. Review the old construction instruction manual section thoroughly. Pay attention to anything that no longer comply with the new construction law text.
3. Compare the content of the old manual with the new law requirements. Look for discrepancies, outdated information, or parts that no longer comply with the new regulations.
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
Suomalaisessa asuntorakentamisessa pinta-alat ovat melko pieniä ja makuuhuoneet ovat yleensä suhteellisen tiukasti mitoitettuja. Makuuhuoneet on totuttu jaottelemaan kahteen ryhmään:
• Suurempiin eli kahden hengen makuuhuoneisiin, koko noin 10...16 m2
• Pienempiin eli yhdenhengen makuuhuoneisiin, koko noin 7...12 m2
Sijoittuminen, kulkuyhteydet ja mitoitus
• Makuuhuoneet pyritään sijoittamaan asunnon pohjoisenpuoleiseen osaan, jotta auringonvalo ja lämpö häiritsevät mahdollisimman vähän nukkumista.
• Suora yhteys makuuhuoneista eteis- tai kulkutiloihin parantaa asunnon käytettävyyttä.
• Makuuhuoneiden välittömään läheisyyteen pyritään sijoittamaan myös peseytymis- ja wc-tilat.
• Makuuhuoneen viihtyvyyttä lisää kulku makuuhuoneesta ulkotiloihin.
• Kahden lapsen iso yhteinen makuuhuone voidaan jakaa kahdeksi erilliseksi tilaksi.
• Kalustuksen muunneltavuus ja väljä mitoitus tuo joustavuutta.
• Mitoituksella ja esteettömyydellä pystytään ratkaisemaan myös liikuntarajoitteisten ja ikäihmisten toimiminen asunnossa.

c. Päivitystarve:
Uuden lain 40 §:n mukaan asuin-, majoitus- ja työtilassa on oltava ikkuna luonnonvalon saamiseksi.

d.Viittaus uuteen lakiin:
40 § Asuin-, majoitus- ja työtilat

####

Example 2:

####

a. Otsikko:
Osa 3.2: Rakennushankkeen jätehuollon suunnittelu- ja ilmoitusvelvoite

b. Nykyinen sisältö:
Rakennushankkeeseen ryhtyvä on velvollinen rakentamista tai purkamista koskevassa lupahakemuksessa tai ilmoituksessa esittämään selvityksen rakennusjätteen määrästä, laadusta ja sen lajittelusta. Hakemuksessa tai ilmoituksessa ilmoitetaan erikseen terveydelle tai ympäristölle vaarallisesta rakennus- tai purkujätteestä ja sen käsittelystä. Purkamista edeltävässä selvityksessä kartoitetaan rakenteista syntyvät jätelajit, erityisesti vaaralliset jätteet, sekä tehdään karkea arvio syntyvistä jätemääristä lajikohtaisesti.

c. Päivitystarve:
Uuden lain 16 §:n mukaan rakennusjätteen selvityksessä tulee ilmoittaa arviot myös rakennus- tai purkuhankkeessa syntyvien purkumateriaalien määristä. Purkumateriaali- ja rakennusjäteselvitys on päivitettävä rakennus- tai purkuhankkeen valmistuttua siten, että siitä käyvät ilmi tiedot rakennuspaikalta pois kuljetettujen rakennus- ja purkujätteiden määristä, toimituspaikoista ja käsittelystä. Lisäksi rakentamishankkeeseen ryhtyvän on huolehdittava, että purkumateriaali- ja rakennusjäteselvityksessä edellytetyt tiedot ilmoitetaan Suomen ympäristökeskuksen ylläpitämään tietokantaan.

d.Viittaus uuteen lakiin:
16 § Purkumateriaali- ja rakennusjäteselvitys
####

Example 3:

####

a. Otsikko:
2.3 Suunnittelijoiden kelpoisuus

b. Nykyinen sisältö:
2.3 Suunnittelijoiden kelpoisuus
• MRL123 §
• MRA 48 §
Suunnittelijan koulutus ja kokemus yhdessä muodostavat suunnittelijan pätevyyden. Vaadittava kelpoisuus määräytyy suunnittelijan riittävästä pätevyydestä suhteessa kulloisenkin suunnittelutehtävän vaativuuteen. Suunnittelijoiden kelpoisuuden arvioimiseksi RakMKosassa A2esitetään suunnittelutehtävien luokitus vaativuuden mukaan ja kuhunkin luokkaan tarvittava suunnittelijan pätevyys. Kunnan rakennusvalvontaviranomaisen asia on arvioidasuunnittelijoiden kelpoisuus rakennuslupakohtaisesti rakennushankkeen laadun ja vaativuuden sekä ympäristön asettamat vaatimukset huomioon ottaen
• rakennussuunnittelijan kelpoisuus eli koulutus ja kokemus,
• erityissuunnittelijoiden kelpoisuus eli koulutus ja kokemus.
Korjaus- ja muutostyössä otetaan arvioinnissa lisäksi huomioon olemassa olevan rakennuksen asettamat lähtökohdat. Pääsuunnittelijan kelpoisuuden tulee hankkeessa olla vähintään samaa tasoa kuin hankkeen vaativimpaan suunnittelutehtävään tarvittava kelpoisuus.

c. Päivitystarve:
Uuden lain 83 §:n mukaan suunnittelijan on osoitettava pätevyytensä tavanomaiseen, vaativaan, erittäin vaativaan ja poikkeuksellisen vaativaan suunnittelutehtävään ympäristöministeriön valtuuttaman toimijan antamalla todistuksella.

d.Viittaus uuteen lakiin:
83 § Suunnittelijoiden kelpoisuusvaatimukset

Begin your analysis now, and present your findings as instructed above.
"""
