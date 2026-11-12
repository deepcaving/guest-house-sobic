#!/usr/bin/env python3
"""Apply the rate-model copy changes to every language at once.

The room rows now say the unit out loud - the price is for the ROOM, not
for each person - and the meal rules say what a guest actually gets from
the day they arrive.

The English, German and Bosnian columns live in the dictionary; Italian,
French and Dutch live in their own scripts under tools/. This script
updates the first three and patches the three scripts, then the scripts
are run to regenerate the dictionary.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # the repository root
DICT = ROOT / "i18n-data.js"

# --- the new text, per language ---------------------------------------------
# Room prices: the unit is the room.
NEW = {
    "r1_s": {
        "en": "€85 per room, per night · breakfast included",
        "de": "€85 pro Zimmer, pro Nacht · Frühstück inklusive",
        "bs": "85 € po sobi, po noći · doručak uključen",
        "it": "85 € a camera, a notte · colazione inclusa",
        "fr": "85 € par chambre, par nuit · petit-déjeuner compris",
        "nl": "€ 85 per kamer, per nacht · ontbijt inbegrepen",
    },
    "r2_s": {
        "en": "€70 per room, per night · breakfast included",
        "de": "€70 pro Zimmer, pro Nacht · Frühstück inklusive",
        "bs": "70 € po sobi, po noći · doručak uključen",
        "it": "70 € a camera, a notte · colazione inclusa",
        "fr": "70 € par chambre, par nuit · petit-déjeuner compris",
        "nl": "€ 70 per kamer, per nacht · ontbijt inbegrepen",
    },
    "r3_s": {
        "en": "€110 per room, per night · river view",
        "de": "€110 pro Zimmer, pro Nacht · Flussblick",
        "bs": "110 € po sobi, po noći · pogled na rijeku",
        "it": "110 € a camera, a notte · vista sul fiume",
        "fr": "110 € par chambre, par nuit · vue sur la rivière",
        "nl": "€ 110 per kamer, per nacht · uitzicht op de rivier",
    },
    "r4_s": {
        "en": "€900 per night for the whole house · up to 16 guests",
        "de": "€900 pro Nacht für das ganze Haus · bis zu 16 Gäste",
        "bs": "900 € po noći za cijelu kuću · do 16 gostiju",
        "it": "900 € a notte per l'intera casa · fino a 16 ospiti",
        "fr": "900 € par nuit pour toute la maison · jusqu'à 16 personnes",
        "nl": "€ 900 per nacht voor het hele huis · tot 16 gasten",
    },
    "rates_head": {
        "en": ("Room prices are per room, per night. Meal prices are per person, per day. "
               "Two people sharing a double room pay €85 for the room plus €50 each for meals, "
               "and split the room between them, which is why sharing is the better deal."),
        "de": ("Die Zimmerpreise gelten pro Zimmer und pro Nacht. Die Mahlzeiten werden pro Person "
               "und pro Tag berechnet. Zwei Personen teilen sich ein Doppelzimmer, zahlen €85 für "
               "das Zimmer und je €50 für die Mahlzeiten und teilen sich das Zimmer, deshalb "
               "ist das Teilen günstiger."),
        "bs": ("Cijene smještaja odnose se na sobu, po noći. Obroci se plaćaju po osobi, po danu. "
               "Dvije osobe koje dijele dvov krevetnu sobu plaćaju 85 € za sobu i po 50 € za "
               "obroke, i dijele sobu, zato je zajednički smještaj jeftiniji."),
        "it": ("Le tariffe di soggiorno sono per camera, a notte. I pasti si calcolano a persona, "
               "a giorno. Due persone che condividono una camera doppia pagano 85 € per la "
               "camera più 50 € a testa per i pasti, e dividono la camera: per questo è più "
               "conveniente condividere."),
        "fr": ("Les tarifs de chambre sont par chambre, par nuit. Les repas sont par personne, par "
               "jour. Deux personnes partageant une chambre double paient 85 € pour la chambre "
               "plus 50 € chacun pour les repas, et se partagent la chambre — c'est pourquoi "
               "partager revient moins cher."),
        "nl": ("De kamertarieven zijn per kamer, per nacht. De maaltijden zijn per persoon, per "
               "dag. Twee die samen een dubbelkamer delen betalen € 85 voor de kamer plus € 50 "
               "elk voor de maaltijden, en delen de kamer tussen hen — daarom is delen "
               "voordeliger."),
    },
    "rates_note": {
        "en": ("Room-only rates are per room, per night, and include breakfast. Meals are priced per "
               "person, per day: half board €42 and full board €50. Full board covers two of the "
               "day's three meals — breakfast, plus either lunch or dinner. Children under 6 stay "
               "free and pay no licence. Children 6–12 pay half rate and no licence. Tourist tax "
               "is €2 per person per night — it is already included in our packages, and on "
               "room-only stays it is charged on arrival and shown separately on your invoice."),
        "de": ("Die Preise für reine Zimmerübernachtung gelten pro Zimmer und pro Nacht und "
               "inklusive Frühstück. Die Mahlzeiten werden pro Person und pro Tag berechnet: "
               "Halbpension 42 € und Vollpension 50 €. Die Vollpension deckt zwei der drei "
               "Mahlzeiten des Tages — Frühstück, plus Mittagessen oder Abendessen. Kinder unter "
               "6 Jahren bleiben kostenlos und brauchen keine Lizenz. Kinder von 6 bis 12 Jahren "
               "zahlen den halben Preis und brauchen keine Lizenz. Die Kurtaxe beträgt 2 € pro "
               "Person und Nacht — in unseren Pauschalen ist sie bereits enthalten, bei reinen "
               "Zimmerbuchungen wird sie bei der Anreise berechnet und separat auf Ihrer "
               "Rechnung ausgewiesen."),
        "bs": ("Cijene za samo smještaj odnose se na sobu, po noći, i uključuju doručak. Obroci "
               "se plaćaju po osobi, po danu: polupansion 42 € i puni pansion 50 €. Puni pansion "
               "pokriva dva od tri obroka u danu — doručak, plus ručak ili večera. Djeca mlađa "
               "od 6 godina besplatna su i ne plaćaju dozvolu. Djeca od 6 do 12 godina plaćaju "
               "pola cijene i ne plaćaju dozvolu. Boravišna taksa je 2 € po osobi po noći — u "
               "našim je paketima već uključena, a kod smještaja bez paketa naplaćuje se pri "
               "dolasku i iskazuje zasebno na vašem računu."),
        "it": ("Le tariffe di solo soggiorno sono per camera, a notte, e includono la colazione. "
               "I pasti si calcolano a persona, a giorno: mezza pensione 42 € e pensione completa "
               "50 €. La pensione completa copre due dei tre pasti della giornata — la colazione, "
               "più il pranzo o la cena. I bambini sotto i 6 anni soggiornano gratis e non "
               "pagano il permesso. I bambini dai 6 ai 12 anni pagano metà tariffa e non "
               "pagano il permesso. La tassa di soggiorno è di 2 € a persona a notte — è già "
               "inclusa nei nostri pacchetti, mentre per i soggiorni senza pacchetto viene "
               "addebitato all'arrivo e riportato separatamente sulla fattura."),
        "fr": ("Les tarifs en chambre seule sont par chambre, par nuit, et comprennent le "
               "petit-déjeuner. Les repas sont facturés par personne, par jour : demi-pension "
               "42 € et pension complète 50 €. La pension complète couvre deux des trois repas de "
               "la journée — le petit-déjeuner, plus le déjeuner ou le dîner. Les enfants de "
               "moins de 6 ans restent gratis et ne paient pas de permis. Les enfants de 6 à 12 "
               "ans paient la moitié du tarif et ne paient pas de permis. La taxe de séjour est "
               "de 2 € par personne et par nuit — elle est déjà comprise dans nos forfaits, et "
               "pour un séjour sans forfait elle est perçue à l'arrivée et mentionnée "
               "séparément sur votre facture."),
        "nl": ("Tarieven voor alleen verblijf zijn per kamer, per nacht, en omvatten het ontbijt. "
               "Maaltijden worden per persoon, per dag berekend: halfpension € 42 en volpension "
               "€ 50. Volpension dekt twee van de drie maaltijden van die dag — ontbijt, plus "
               "lunch of diner. Kinderen jonger dan 6 blijven gratis en betalen geen vergunning. "
               "Kinderen van 6 tot 12 betalen de helft en geen vergunning. De toeristenbelasting "
               "is € 2 per persoon per nacht — die zit al in onze pakketten, en bij verblijf "
               "zonder pakket wordt het bij aankomst in rekening gebracht en apart op je factuur "
               "vermeld."),
    },
    # The meals rule, as the host described it: the day is counted from the
    # day the guest arrives.
    "pkg_meals": {
        "en": ("Three meals a day, counted from your arrival day: lunch if you arrive in time, then "
               "dinner, then breakfast the next morning — and lunch again if you missed it the day "
               "before. Lunch is served at the guest house, or packed as a picnic when the fishing "
               "spot for the day is far enough to justify it."),
        "de": ("Drei Mahlzeiten am Tag, gerechnet ab dem Tag Ihrer Ankunft: Mittagessen, wenn Sie "
               "rechtzeitig ankommen, dann Abendessen, am nächsten Morgen Frühstück — und am Tag "
               "danach wieder Mittagessen, wenn Sie es am Tag zuvor verpasst haben. Das "
               "Mittagessen wird im Gästehaus serviert, oder als Picknick eingepackt, wenn das "
               "Angelplatz des Tages weit genug weg ist, um es zu rechtfertigen."),
        "bs": ("Tri obroka dnevno, računato od dana vašeg dolaska: ručak ako stignete na vrijeme, "
               "pa večera, pa sutra ujutro doručak — i opet ručak ako ste ga prošli dan "
               "preskočili. Ručak se poslužuje u pansionu, ili se pakira za piknik kada je "
               "ribolovno mjesto tog dana dovoljno daleko da to opravda."),
        "it": ("Tre pasti al giorno, contati dal giorno del tuo arrivo: pranzo se arrivi in tempo, "
               "poi cena, poi la colazione la mattina dopo — e pranzo di nuovo se il giorno "
               "prima lo hai saltato. Il pranzo viene servito in casa, oppure preparato come "
               "picnic quando il luogo di pesca del giorno è abbastanza lontano da giustificarlo."),
        "fr": ("Trois repas par jour, comptés à partir du jour de votre arrivée : le déjeuner si "
               "vous arrivez à l'heure, puis le dîner, puis le petit-déjeuner le lendemain matin "
               "— et le déjeuner à nouveau si vous l'avez manqué la veille. Le déjeuner est "
               "servi à la maison, ou emporté en pique-nique quand le point de pêche du jour est "
               "assez loin pour le justifier."),
        "nl": ("Drie maaltijden per dag, geteld vanaf uw aankomstdag: lunch als u op tijd komt, "
               "dan diner, dan de volgende ochtend ontbijt — en de dag daarna lunch als u die "
               "gemist hebt. De lunch wordt in het huis geserveerd, of ingepakt als picknick "
               "wanneer de visplek van die dag ver genoeg weg ligt om dat te rechtvaardigen."),
    },
}

# --- 1. the dictionary: English, German, Bosnian ---------------------------
raw = DICT.read_text(encoding="utf-8")
data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])

for key, values in NEW.items():
    for lang in ("en", "de", "bs"):
        assert values[lang], f"{key}/{lang} is empty"
        data[key][lang] = values[lang]

# Write it back in the same layout the tools use.
out = [raw[: raw.index("{")], "{\n"]
keys = list(data.keys())
for i, key in enumerate(keys):
    out.append(f'  "{key}": {{\n')
    entry = data[key]
    names = [n for n in ("en", "de", "bs", "it", "fr", "nl") if n in entry]
    for j, name in enumerate(names):
        comma = "," if j < len(names) - 1 else ""
        value = json.dumps(entry[name], ensure_ascii=False)
        out.append(f'    "{name}": {value}{comma}\n')
    out.append("  }" + ("," if i < len(keys) - 1 else "") + "\n")
out.append("};\n")
DICT.write_text("".join(out), encoding="utf-8")
print(f"dictionary updated: {len(NEW)} keys, en/de/bs")

# --- 1b. the English in the markup ------------------------------------------
# The page carries the English text so it reads correctly without JavaScript,
# and check_i18n.py compares the dictionary's English against it.
HTML = ROOT / "index.html"
html = HTML.read_text(encoding="utf-8")
for key, values in NEW.items():
    pattern = re.compile(
        r'(data-i18n-key="%s"[^>]*>)([^<]*)(</)' % re.escape(key)
    )
    m = pattern.search(html)
    assert m, f"index.html: {key} not found"
    html = html[: m.start(2)] + values["en"] + html[m.end(2):]
HTML.write_text(html, encoding="utf-8")
print("index.html updated with the new English")

# --- 2. the scripts that hold it, fr, nl ------------------------------------
for script, lang in (("italian.py", "it"), ("french.py", "fr"), ("dutch.py", "nl")):
    path = ROOT / "tools" / script
    text = path.read_text(encoding="utf-8")
    for key, values in NEW.items():
        pattern = re.compile(r'("%s":\s*")([^"]*)(",)' % re.escape(key))
        m = pattern.search(text)
        assert m, f"{script}: {key} not found"
        # The value may be built from several string literals; take the first
        # quoted chunk and replace it, keeping the rest of the literal intact.
        text = text[: m.start(2)] + values[lang].replace('"', '\\"') + text[m.end(2):]
    path.write_text(text, encoding="utf-8")
    print(f"{script} updated")
