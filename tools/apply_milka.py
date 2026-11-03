#!/usr/bin/env python3
"""Apply Milka's answers (3 Nov 2026) to the i18n dictionary.

    python3 tools/apply_milka.py

Milka confirmed the following, and this script writes the new wording into
i18n-data.js for all four languages, and into tools/italian.py so the Italian
source file stays the single place the Italian copy lives.

What changed and why
--------------------
  Q1  real email address, and she answers enquiries herself
  Q2  a van can be arranged from Banja Luka, Sarajevo AND Split
  Q4  all three airports approved, so "on request" goes
  Q5  NO fishing equipment rental - the claim is removed
  Q6  the real address is Pljeva, not just "Šipovo"
  Q9  guides speak English only, EUR 150-200 per day for the group
  Q10 licence is EUR 40-70 per day depending on the river, not a flat 50
  Q11 tourist tax is included in the packages

Q3 (all room-only prices approved) and Q7 (check-in/out times) need no text
change - the numbers stay exactly as they are.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICT = ROOT / "i18n-data.js"
ITALIAN = ROOT / "tools" / "italian.py"

# key -> {lang: text}
NEW = {
    # --- Q6: the real address is Pljeva ---
    "brand_sub": {
        "en": "Pljeva · Šipovo · Bosnia &amp; Herzegovina",
        "de": "Pljeva · Šipovo · Bosnien &amp; Herzegowina",
        "bs": "Pljeva · Šipovo · Bosna i Hercegovina",
        "it": "Pljeva · Šipovo · Bosnia ed Erzegovina",
    },
    "con_addr_v": {
        "en": "Pljeva, Šipovo<br>Bosnia &amp; Herzegovina<br>2 km downstream of the Pliva springs",
        "de": "Pljeva, Šipovo<br>Bosnien &amp; Herzegowina<br>2 km unterhalb der Pliva-Quellen",
        "bs": "Pljeva, Šipovo<br>Bosna i Hercegovina<br>2 km nizvodnije od izvora Plive",
        "it": "Pljeva, Šipovo<br>Bosnia ed Erzegovina<br>2 km a valle delle sorgenti del Pliva",
    },
    "foot_sip": {
        "en": "Pljeva, Šipovo<br>Bosnia &amp; Herzegovina<br>Fly fishing on the Pliva · Open year-round",
        "de": "Pljeva, Šipovo<br>Bosnien &amp; Herzegowina<br>Fliegenfischen auf der Pliva · Ganzjährig geöffnet",
        "bs": "Pljeva, Šipovo<br>Bosna i Hercegovina<br>Mušičarenje na Plivi · Otvoreno cijele godine",
        "it": "Pljeva, Šipovo<br>Bosnia ed Erzegovina<br>Pesca a mosca sul Pliva · Aperto tutto l'anno",
    },
    # --- Q2 + Q4: all three airports, arranged with the lodge ---
    "r7_s": {
        "en": "Sarajevo, Banja Luka and Split — arranged with the lodge",
        "de": "Sarajevo, Banja Luka und Split — mit dem Haus arrangiert",
        "bs": "Sarajevo, Banja Luka i Split — organizuje se s pansionom",
        "it": "Sarajevo, Banja Luka e Split — organizzati con la locanda",
    },
    "air_p": {
        "en": "We arrange door-to-door transfers in a private van or car from Sarajevo, Banja Luka and Split. Tell us your flight and we will be waiting with a name board.",
        "de": "Wir arrangieren Tür-zu-Tür-Transfers in einem privaten Van oder Auto ab Sarajevo, Banja Luka und Split. Nennen Sie uns Ihren Flug, und wir warten mit einem Namensschild.",
        "bs": "Organizujemo transfer od vrata do vrata privatnim kombijem ili autom iz Sarajeva, Banje Luke i Splita. Javite nam let i čekat ćemo s natpisom.",
        "it": "Organizziamo trasferimenti porta a porta con un van o un'auto privata da Sarajevo, Banja Luka e Split. Ci dica il suo volo e la aspettiamo con un cartello con il suo nome.",
    },
    "air_spu_p": {
        "en": "Croatia, one border crossing. Excellent low-cost connectivity from the UK, Germany and Italy. We cross at Kamensko with our own van, so there is no second vehicle to change into and no transfer you have to arrange yourself.",
        "de": "Kroatien, eine Grenzüberfahrt. Hervorragende Low-Cost-Verbindungen aus Großbritannien, Deutschland und Italien. Wir überqueren bei Kamensko mit unserem eigenen Van — Sie müssen also nicht in ein zweites Fahrzeug umsteigen und selbst nichts organisieren.",
        "bs": "Hrvatska, jedan prelaz granice. Odlične niskotarifne veze iz Ujedinjenog Kraljevstva, Njemačke i Italije. Prelazimo na Kamenskom svojim kombijem, pa ne morate prelaziti u drugo vozilo niti sami organizovati prijevoz.",
        "it": "Croazia, un solo attraversamento di frontiera. Ottimi collegamenti low cost dal Regno Unito, dalla Germania e dall'Italia. Attraversiamo a Kamensko con il nostro van: non dovete cambiare veicolo né organizzarvi il trasferimento da soli.",
    },
    # --- Q9: guides speak English, EUR 150-200 per day for the group ---
    "r8_b": {
        "en": "Fishing guide",
        "de": "Fischguide",
        "bs": "Vodič za ribolov",
        "it": "Guida di pesca",
    },
    "r8_s": {
        "en": "English-speaking · €150–200 per day for the group",
        "de": "Englischsprachig · €150–200 pro Tag für die ganze Gruppe",
        "bs": "Govori engleski · 150–200 € po danu za cijelu grupu",
        "it": "Parla inglese · 150–200 € al giorno per l'intero gruppo",
    },
    "pkg_hosted": {
        "en": "Fishing guides speak English. A guided day costs €150–200 for the group, depending on how many of you there are — so it works out cheaper the more anglers you bring. Ask about the autumn Blue-Winged Olive hatch.",
        "de": "Unsere Fischguides sprechen Englisch. Ein begleiteter Tag kostet €150–200 für die ganze Gruppe, je nachdem, wie viele von Ihnen kommen — je mehr Angler, desto günstiger pro Person. Fragen Sie nach der herbstlichen Blue-Winged-Olive-Schlüpfe.",
        "bs": "Naši vodiči za ribolov govore engleski. Vođeni dan košta 150–200 € za cijelu grupu, zavisno od toga koliko vas dođe — što više ribolovaca, to je jeftinije po osobi. Pitajte o jesenskom roju bijele mušice.",
        "it": "Le nostre guide di pesca parlano inglese. Una giornata guidata costa 150–200 € per l'intero gruppo, a seconda di quanti siete — più anglici siete, più conviene a testa. Chiedete della schiusa autunnale del Blu-Winged Olive.",
    },
    "angl_l3": {
        "en": "<b>Guided days</b> — a local English-speaking guide on the river",
        "de": "<b>Geführte Tage</b> – ein englischsprachiger Guide aus der Region auf dem Fluss",
        "bs": "<b>Vodeni dani</b> – lokalni vodič koji govori engleski na rijeci",
        "it": "<b>Giornate guidate</b> — una guida locale che parla inglese sul fiume",
    },
    "pkg1_l3": {
        "en": "6 days guided fishing with a local English-speaking guide",
        "de": "6 Tage begleitetes Fischen mit einem englischsprachigen Guide aus der Region",
        "bs": "6 dana vođenog ribolova sa lokalnim vodičem koji govori engleski",
        "it": "6 giorni di pesca guidata con una guida locale che parla inglese",
    },
    "pkg1_l6": {
        "en": "Own rods and waders — bring your own or hire them in Šipovo",
        "de": "Eigene Ruten und Watlings — mitbringen oder in Šipovo ausleihen",
        "bs": "Vlastiti štapovi i čizme — ponesite svoje ili iznajmite u Šipovu",
        "it": "Le tue canne e stivali da guado — porta le tue o affittale a Šipovo",
    },
    # --- Q10: licence is EUR 40-70 per day depending on the river ---
    "pkg1_l4": {
        "en": "Fishing licence — €40–70 per day depending on the river, included",
        "de": "Angel-Lizenz — €40–70 pro Tag je nach Fluss, inklusive",
        "bs": "Dozvola za ribolov — 40–70 € po danu zavisno od rijeke, uključeno",
        "it": "Permesso di pesca — 40–70 € al giorno a seconda del fiume, incluso",
    },
    "pkg3_l4": {
        "en": "Fishing licence — €40–70 per day depending on the river, included",
        "de": "Angel-Lizenz — €40–70 pro Tag je nach Fluss, inklusive",
        "bs": "Dozvola za ribolov — 40–70 € po danu zavisno od rijeke, uključeno",
        "it": "Permesso di pesca — 40–70 € al giorno a seconda del fiume, incluso",
    },
    "rates_note": {
        "en": "Room-only rates are per night, breakfast included. The fishing licence is <b>€40–70 per day</b> depending on which river you fish, and is not included in room-only rates; we arrange it for you on arrival. Children under 6 stay free and pay no licence. Children 6–12 pay half rate and no licence. Tourist tax is €2 per person per night — it is already included in our packages, and on room-only stays it is charged on arrival and shown separately on your invoice.",
        "de": "Die Übernachtungspreise gelten pro Nacht inklusive Frühstück. Die Angel-Lizenz beträgt <b>€40–70 pro Tag</b> je nachdem, welchen Fluss Sie befischen, und ist in den Übernachtungspreisen nicht enthalten; wir besorgen sie Ihnen bei Ankunft. Kinder unter 6 Jahren sind kostenlos und zahlen keine Lizenz. Kinder von 6 bis 12 Jahren zahlen den halben Preis und keine Lizenz. Die Kurtaxe beträgt €2 pro Person und Nacht — in unseren Paketen ist sie bereits enthalten, bei reinen Übernachtungen wird sie bei Ankunft berechnet und separat auf Ihrer Rechnung ausgewiesen.",
        "bs": "Cijene smještaja su po noći i uključuju doručak. Dozvola za ribolov iznosi <b>40–70 € po danu</b> zavisno od toga na kojoj rijeci lovite, i nije uključena u cijene smještaja; mi je pribavljamo za vas pri dolasku. Djeca mlađa od 6 godina besplatno su i ne plaćaju dozvolu. Djeca od 6 do 12 godina plaćaju pola cijene i ne plaćaju dozvolu. Boravišna taksa je 2 € po osobi po noći — u našim je paketima već uključena, a kod smještaja bez paketa naplaćuje se pri dolasku i iskazuje zasebno na računu.",
        "it": "Le tariffe di soggiorno sono per notte e includono la colazione. Il permesso di pesca è di <b>40–70 € al giorno</b> a seconda del fiume che peschi, e non è incluso nelle tariffe di soggiorno; noi lo procuriamo per te all'arrivo. I bambini sotto i 6 anni soggiornano gratis e non pagano il permesso. I bambini dai 6 ai 12 anni pagano metà tariffa e non pagano il permesso. La tassa di soggiorno è di 2 € a persona a notte — è già inclusa nei nostri pacchetti, mentre per i soggiorni senza pacchetto viene addebitata all'arrivo e riportata separatamente sulla fattura.",
    },
    # --- Q11: tourist tax is included in the packages ---
    "pkg_p": {
        "en": "All packages include the lodge, the table, the guide, the fishing licence and the tourist tax — there is nothing to pay on arrival. November and December rates are lower — see each card.",
        "de": "Alle Pakete enthalten das Haus, den Tisch, den Guide, die Angel-Lizenz und die Kurtaxe — bei der Ankunft ist nichts zu zahlen. Im November und Dezember sind die Preise niedriger — siehe jede Karte.",
        "bs": "Svi paketi uključuju pansion, sto, vodiča, dozvolu za ribolov i boravišnu taksu — pri dolasku se ne plaća ništa. Cijene u novembru i decembru su niže – vidite svaku karticu.",
        "it": "Tutti i pacchetti includono la locanda, la tavola, la guida, il permesso di pesca e la tassa di soggiorno — all'arrivo non devi pagare nulla. A novembre e dicembre le tariffe sono più basse: vedi ogni scheda.",
    },
    "seas_pa": {
        "en": "Seven nights, six days of guided fishing, full board, licence, tourist tax and the Sarajevo transfer. Group of four. The BWO hatch is at its tail end and the grayling are in prime condition.",
        "de": "Sieben Nächte, sechs Tage begleitetes Fischen, Vollpension, Lizenz, Kurtaxe und der Transfer ab Sarajevo. Vier Personen. Die BWO-Schlüpfe sind am Ende und die Äsche in Bestform.",
        "bs": "Sedam noći, šest dana vođenog ribolova, puni pansion, dozvola, boravišna taksa i transfer sa Sarajeva. Grupa od četiri. Rok bijele mušice je na izmaku, a lipljen je u savršenoj kondiciji.",
        "it": "Sette notti, sei giorni di pesca guidata, pensione completa, permesso, tassa di soggiorno e transfer da Sarajevo. Gruppo di quattro. La schiusa della BWO è al suo epilogo e i temoli sono in condizioni perfette.",
    },
    "seas_pb": {
        "en": "Four nights, three fishing days, half board, licence, tourist tax and transfer. The easy way to try the river — and the easiest to fill in the gaps between trips.",
        "de": "Vier Nächte, drei Fischeitage, Halbpension, Lizenz, Kurtaxe und Transfer. Der einfache Weg, den Fluss zu testen – und am leichtesten zwischen zwei Reisen zu füllen.",
        "bs": "Četiri noći, tri ribolovna dana, polupansion, dozvola, boravišna taksa i transfer. Najlakši način da isprobate rijeku – i najlakše popuniti praznine između putovanja.",
        "it": "Quattro notti, tre giorni di pesca, mezza pensione, permesso, tassa di soggiorno e transfer. Il modo più semplice di provare il fiume — e il più facile per colmare i vuoti fra un viaggio e l'altro.",
    },
    # --- Q8: the form now also reaches the host by email ---
    "form_sent": {
        "en": "Thank you — WhatsApp and your email app have opened with your details ready to send. Press send in either one and we will reply within 24 hours.",
        "de": "Danke — WhatsApp und Ihr E-Mail-Programm haben sich mit Ihren Angaben geöffnet. Senden Sie in einer der beiden Apps, und wir antworten innerhalb von 24 Stunden.",
        "bs": "Hvala — WhatsApp i vaša aplikacija za e-poštu otvorili su se s vašim podacima spremanim za slanje. Pošaljite u jednoj od njih i odgovorit ćemo vam u roku od 24 sata.",
        "it": "Grazie — WhatsApp e la tua app di posta si sono aperti con i tuoi dati pronti per l'invio. Premi invia in uno dei due e ti risponderemo entro 24 ore.",
    },
}


def main():
    raw = DICT.read_text(encoding="utf-8")
    body = raw[raw.index("{") : raw.rindex("}") + 1]
    data = json.loads(body)

    missing = [k for k in NEW if k not in data]
    if missing:
        raise SystemExit(f"these keys are not in the dictionary: {missing}")

    for key, langs in NEW.items():
        for lang, text in langs.items():
            data[key][lang] = text

    # Rebuild the file in the original style and key order.
    # The head is everything up to the opening brace of the object.
    head = raw[: raw.index("{")].rstrip()
    if not head.endswith("="):
        head += " ="
    out = [head + " {\n"]
    keys = list(data.keys())
    for i, k in enumerate(keys):
        e = data[k]
        out.append(f'  "{k}": {{\n')
        for j, lang in enumerate(["en", "de", "bs", "it"]):
            # "it" is the last field inside this key's object, so it never
            # carries a trailing comma. Only the key block itself is
            # separated by a comma, and the very last block is not.
            comma = "" if j == 3 else ","
            out.append(f'    "{lang}": {json.dumps(e[lang], ensure_ascii=False)}{comma}\n')
        out.append("  }" + ("," if i < len(keys) - 1 else "") + "\n")
    out.append("};\n")
    DICT.write_text("".join(out), encoding="utf-8")
    print(f"i18n-data.js: updated {len(NEW)} keys.")

    # Keep tools/italian.py in step - it is the source of the Italian column.
    src = ITALIAN.read_text(encoding="utf-8")
    for key, langs in NEW.items():
        if "it" not in langs:
            continue
        # Match the existing entry: "key": "value",
        pattern = re.compile(r'("%s":\s*)"((?:[^"\\]|\\.)*)"' % re.escape(key))
        match = pattern.search(src)
        if not match:
            print(f"  ! could not find {key} in tools/italian.py - add it by hand")
            continue
        replacement = match.group(1) + json.dumps(langs["it"], ensure_ascii=False)
        src = src[: match.start()] + replacement + src[match.end() :]
    ITALIAN.write_text(src, encoding="utf-8")
    print(f"tools/italian.py: updated {len(NEW)} Italian strings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
