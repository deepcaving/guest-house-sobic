#!/usr/bin/env python3
"""The Italian copy, and the script that writes it into i18n-data.js.

    python3 tools/italian.py

i18n-data.js says "Generated; do not edit by hand", so the Italian strings
live here, in a readable file, and this script writes them into the
dictionary. Edit IT below, re-run the script, and the site is updated.

The script refuses to run if a key in the dictionary has no Italian, or if
Italian exists for a key the dictionary does not have. It also rewrites the
whole dictionary in the original key order, so a run never changes the
English, German or Bosnian values.
"""

import json
import re
import sys
from pathlib import Path

DICT = Path(__file__).resolve().parent.parent / "i18n-data.js"

IT = {
    "brand_sub": "Sipovo · Bosnia ed Erzegovina",
    "host_line": "Ospita: Milka Smjestaj Šobić",
    "nav_lodge": "La locanda",
    "nav_fishing": "Pesca",
    "nav_pkg": "Pacchetti",
    "nav_rates": "Tariffe",
    "nav_here": "Come arrivare",
    "nav_enquire": "Richiedi",
    "lang_label": "IT",
    "hero_eyebrow": "Pesca a mosca sul Pliva · Šipovo · Republika Srpska",
    "hero_h1a": "Sette camere. Un fiume.",
    "hero_h1b": "Niente fra voi e l'acqua.",
    "hero_lede": "Una piccola locanda sul fiume, due chilometri a valle della celebre sorgente del Pliva, nel cuore delle acque di pesca a mosca secca più sottovalutate d'Europa. Cucina a legna, terrazza privata che sovrasta la riva e una padrona che cucina ciò che il fiume le dà.",
    "hero_cta1": "Vedi i pacchetti",
    "hero_cta2": "Verifica disponibilità",
    "intro_eyebrow": "Benvenuti alla locanda",
    "intro_h2": "Una casa che per comodità si trova sull'acqua",
    "intro_p": "Quasi tutte le lodge di pesca sul Pliva vi mettono in un bungalow con vista sul fiume. Noi vi mettiamo sul fiume. La sala da pranzo si apre su un prato che scende direttamente nell'acqua; i divani della terrazza sono sopra la riva; la cucina ha una griglia a legna e il fiume scorre oltre la finestra.",
    "video_tag": "Visita guidata di 53 secondi",
    "fish_eyebrow": "La pesca",
    "fish_h2": "Il Pliva è un torrente di sorgente, e lo resta",
    "fish_p": "Tre sorgenti nascono a Pljeva e si uniscono nel Pliva. Scorre per 33 km nella valle di Šipovo e confluisce nel Janj, poi nel Vrbas a Jajce. Poiché l'acqua esce dal terreno a una temperatura costante di 8 °C, il fiume non tracima mai, non diventa mai torbido e non smette mai di alimentare.",
    "fish_l2": "Acqua cristallina — vedete i pesci, poi lanciate su quello che avete visto",
    "fish_l3": "Finali lunghi e sottili (spesso oltre 5 m) e mosche piccole: taglia 18–22",
    "fish_l4": "Alto Pliva aperto tutto l'anno; il tratto di Jajce da marzo a settembre",
    "fish_l5": "Sette fiumi a portata di mano: Pliva, Janj, Ribnik, Sana, Sanica, Una, Krušnica",
    "tbl_eyebrow": "La tavola",
    "tbl_h2": "Una cucina a legna e una sala da pranzo sull'acqua",
    "tbl_p": "La sala da pranzo è il cuore della locanda: un lungo tavolo di rovere per quattordici, un camino in mattoni con griglia, una cucina completa dietro e finestre a tutta altezza lungo il fiume. La padrona cucina con ciò che dà la valle — e con ciò che il fiume ha regalato quella mattina.",
    "gal_eyebrow": "La locanda in immagini",
    "gal_h2": "Camere, acqua e lo spazio in mezzo",
    "gal_p": "Il grande prato accanto alla locanda è dove i pescatori preparano la loro attrezzatura, e dove le barche leggere possono essere assemblate per le acque tranquille dell'alto corso.",
    "stat_eyebrow": "Il fiume in numeri",
    "stat_h2": "Perché i pescatori tornano sempre",
    "stat_l1": "Tratto di pesca a mosca",
    "stat_l2": "Temolo fino a",
    "stat_l3": "Temperatura dell'acqua, tutto l'anno",
    "stat_l4": "Dall'aeroporto di Sarajevo",
    "seas_eyebrow": "La stagione tranquilla",
    "seas_h2": "Novembre e dicembre sul Pliva",
    "seas_p": "È la stagione di transizione — le settimane guidate sono finite, le schiuse autunnali vanno avanti, e il fiume è vostro. Meno pescatori sull'acqua, prezzi più bassi e un fuoco nella sala da pranzo ogni sera.",
    "seas_tag1": "15 nov – 31 dic 2026",
    "seas_h3a": "La settimana sul Pliva — 1.190 €",
    "seas_pa": "Sette notti, sei giorni di pesca guidata, pensione completa, permesso e transfer da Sarajevo. Gruppo di quattro. La schiusa della BWO è al suo epilogo e i temoli sono in condizioni perfette.",
    "seas_tag2": "Tutto l'anno",
    "seas_h3b": "Soggiorno breve — 730 €",
    "seas_pb": "Quattro notti, tre giorni di pesca, mezza pensione, permesso e transfer. Il modo più semplice di provare il fiume — e il più facile per colmare i vuoti fra un viaggio e l'altro.",
    "seas_h3c": "La settimana per chi accompagna — 950 €",
    "seas_pc": "Sette notti per chi non pesca. Il mercato di Šipovo, le cascate di Jajce, la sorgente del Janj, passeggiate lungo il fiume e cena in terrazza ogni sera.",
    "pkg_eyebrow": "Pacchetti",
    "pkg_h2": "Tre modi per venire",
    "pkg_p": "Tutti i pacchetti includono la locanda, la tavola, la guida e il permesso di pesca. La tassa di soggiorno è di 2 € a persona a notte, da pagare all'arrivo. A novembre e dicembre le tariffe sono più basse — vedi ogni scheda.",
    "pkg1_h3": "La settimana sul Pliva",
    "pkg1_len": "7 notti · 6 giorni di pesca guidata",
    "pkg2_h3": "La settimana per chi accompagna",
    "pkg2_len": "7 notti · per chi non pesca",
    "pkg3_h3": "Soggiorno breve",
    "pkg3_len": "4 notti · 3 giorni di pesca guidata",
    "pkg_from": "Da",
    "pkg_per": "/ persona",
    "pkg1_l1": "7 notti in una camera con vista sul fiume, bagno privato",
    "pkg1_l2": "Pensione completa: colazione, pranzo al sacco sull'acqua, cena",
    "pkg1_l3": "6 giorni di pesca guidata con una guida locale che parla inglese",
    "pkg1_l4": "Permesso di pesca sul Pliva — 50 €/giorno per non residenti, incluso",
    "pkg1_l5": "Transfer aeroportuale andata e ritorno da Sarajevo",
    "pkg1_l6": "Canna e stivali da guado su richiesta",
    "pkg2_l1": "7 notti in una camera con vista sul fiume, bagno privato",
    "pkg2_l2": "Pensione completa, con le cene in terrazza",
    "pkg2_l3": "Programma giornaliero: mercato di Šipovo, cascate e fortezza di Jajce",
    "pkg2_l4": "Passeggiata alla sorgente del Janj e pedalata nella valle del Pliva",
    "pkg2_l5": "Discesa in raft sulle acque tranquille dell'alto corso (estate, dai 10 anni)",
    "pkg2_l6": "Transfer aeroportuale andata e ritorno da Sarajevo",
    "pkg3_l1": "4 notti in una camera con vista sul fiume, bagno privato",
    "pkg3_l2": "Mezza pensione: colazione e cena",
    "pkg3_l3": "3 giorni di pesca guidata con una guida locale",
    "pkg3_l4": "Permesso di pesca sul Pliva — 50 €/giorno per non residenti, incluso",
    "pkg3_l5": "Transfer aeroportuale andata e ritorno da Sarajevo",
    "pkg3_l6": "Perfetto da abbinare a un viaggio a Jajce o a Šipovo",
    "pkg_hosted": "Settimane guidate con guide di nome (inglesi, tedesche, francesi e italiane) sono disponibili da 1.790 € a persona. Chiedi della schiusa autunnale del Blu-Winged Olive.",
    "rates_eyebrow": "Tariffe e servizi inclusi",
    "rates_h2": "Soggiorno da solo",
    "rates_note": "Le tariffe di soggiorno sono per notte e includono la colazione. Il permesso di pesca sul Pliva è di <b>50 € al giorno</b> per i non residenti e non è incluso nelle tariffe di soggiorno; noi lo procuriamo per te all'arrivo. I bambini sotto i 6 anni soggiornano gratis e non pagano il permesso. I bambini dai 6 ai 12 anni pagano metà tariffa e non pagano il permesso. La tassa di soggiorno è di 2 € a persona a notte, addebitata all'arrivo e riportata separatamente sulla fattura.",
    "quote_src": "Scrittore di pesca, sul Pliva e sul Ribnik",
    "air_eyebrow": "Come arrivare",
    "air_h2": "Tre aeroporti, una strada",
    "air_p": "Organizziamo transfer porta a porta con auto privata o minibus. Comunicateci il vostro volo e vi aspetteremo con un cartello con il vostro nome.",
    "air_sjj": "SJJ · SARAJEVO",
    "air_sjj_d": "≈ 4 ore · 280 km",
    "air_sjj_p": "La scelta migliore per ospiti britannici, tedeschi, svizzeri, austriaci e italiani. Voli low cost diretti da Londra, Manchester, Birmingham, Edimburgo, Berlino, Monaco, Amburgo, Vienna, Zurigo, Milano e Roma.",
    "air_sjj_r": "Consigliato per la maggior parte degli ospiti",
    "air_bnx_d": "≈ 2 ore · 105 km",
    "air_bnx_p": "L'aeroporto più vicino, con il tragitto più breve. Meno voli diretti, quindi controlla gli orari per le tue date — funziona meglio come opzione quando sei già nella regione.",
    "air_bnx_r": "Transfer più breve",
    "air_spu_d": "≈ 3,5 ore · 250 km",
    "air_spu_p": "Croazia, un solo attraversamento di frontiera. Ottimi collegamenti low cost dal Regno Unito, dalla Germania e dall'Italia. Passiamo da Kamensko e il confine di solito si attraversa senza problemi.",
    "air_spu_r": "Molti voli low cost dal Regno Unito",
    "air_note": "Vieni in auto? Abbiamo parcheggio sicuro gratuito. Arrivi in bus? Possiamo passare a prenderti a Šipovo.",
    "cta_eyebrow": "Pronti quando lo siete voi",
    "cta_h2": "Mandateci le date, al resto pensiamo noi",
    "cta_p": "Inviatci il numero di pescatori, le vostre date e l'aeroporto in cui atterrate. Vi rispondiamo entro 24 ore con un prezzo confermato e il transfer organizzato.",
    "cta_btn": "Richiedi disponibilità",
    "con_eyebrow": "Contatti",
    "con_h2": "Pliva River Lodge",
    "con_wa": "WhatsApp &amp; telefono",
    "con_email": "E-mail",
    "con_addr": "Indirizzo",
    "con_co": "Check-in / check-out",
    "con_seas": "Stagione",
    "form_name": "Il vostro nome",
    "form_email": "E-mail",
    "form_dates": "Date preferite",
    "form_people": "Quante persone",
    "form_air": "Arrivo via",
    "form_msg": "Qualcosa che dobbiamo sapere",
    "form_btn": "Invia richiesta",
    "form_note": "Rispondiamo a ogni richiesta entro 24 ore, di solito già in giornata.",
    "form_sent": "Grazie — WhatsApp si è aperto con i vostri dati pronti da inviare. Inviate il messaggio da lì e risponderemo entro 24 ore.",
    "opt_1": "1 pescatore",
    "opt_2": "2 pescatori",
    "opt_3": "3 pescatori",
    "opt_4": "4 pescatori",
    "opt_5": "5 o più",
    "opt_comp": "Accompagnatore / senza pesca",
    "opt_drive": "Arrivo in auto",
    "ph_dates": "es. 10–17 ottobre 2026",
    "ph_name": "Nome e cognome",
    "ph_email": "tu@esempio.it",
    "ph_msg": "Esperienza di pesca, esigenze alimentari, preferenze per la camera…",
    "foot_sip": "Šipovo, Republika Srpska, Bosnia ed Erzegovina<br>Pesca a mosca sul Pliva · Aperto tutto l'anno",
    "foot_safe": "Catch &amp; release. Assicurazione di viaggio consigliata.",
    "foot_contact": "Contatti",
    "foot_copy": "Tutti i diritti riservati.",
    "hero_f1": "<b>2 km</b> dalla sorgente del Pliva",
    "hero_f2": "<b>8 °C</b> tutto l'anno, cristallina",
    "hero_f3": "<b>8 km</b> di trote selvatiche &amp; temoli",
    "hero_f4": "<b>Tariffe nov–dic</b> da 1.190 €",
    "fish_l1": "<b>Trote selvatiche e temoli</b> fino a 60 cm, solo catch and release",
    "tbl_b1": "<b>Griglia a legna e camino</b> al centro della sala",
    "tbl_b2": "<b>Trotte del Pliva</b> quando la pesca del giorno lo consente",
    "tbl_b3": "<b>Prodotti locali</b> — miele, formaggio, erbe, rakija dalle colline",
    "tbl_b4": "<b>Colazione in terrazza</b>, se il tempo lo permette",
    "tbl_b5": "<b>Cena per chi non è residente</b> su accordo, con 24 ore di preavviso",
    "pkg1_note": "Gruppo di 4 · 1.590 € per due · 2.090 € da soli",
    "pkg2_note": "Gruppo di 4 · 1.230 € per due · 1.630 € da soli",
    "pkg3_note": "Gruppo di 2 · 930 € per due · 1.230 € da soli",
    "winter_label": "Nov–dic: <b>1.190 €</b> a persona",
    "con_addr_v": "Šipovo, Republika Srpska, Bosnia ed Erzegovina<br>2 km a valle delle sorgenti del Pliva",
    "con_co_v": "Dalle 11:00 · fino alle 10:00",
    "con_seas_v": "Aperto tutto l'anno. Migliore pesca a mosca secca: maggio–giugno e settembre–ottobre.",
    "angl_eyebrow": "Sull'acqua",
    "angl_h2": "Guadate il Pliva, o pescate dalla riva",
    "angl_p": "Il Pliva è abbastanza basso da poter essere guadato quasi per tutto il suo corso — dal ginocchio alla coscia su ghiaia, con una corrente costante che vi tiene teso il lenza. È il tipo d'acqua in cui un finale lungo ripaga: lanciate a monte, lasciate derivare, e la trota vi dice dov'è. Chi preferisce restare all'asciutto troverà sulla riva della locanda e sul prato lo spazio per lanciare sugli stessi pesci.",
    "angl_l1": "<b>Guado</b> — fino alla coscia, fondo ghiaioso, corrente forte",
    "angl_l2": "<b>Lancio dalla riva</b> — dalla terrazza della locanda e dal prato",
    "angl_l3": "<b>Giornate guidate</b> — una guida locale, stivali e canne inclusi",
    "angl_safe": "L'acqua è a 8 °C tutto l'anno. Una tuta in neoprene e un giubbotto di galleggiamento sono indispensabili, e forniamo entrambi. Il giubbotto si indossa sempre durante le giornate guidate.",
    "rib_eyebrow": "Un secondo fiume, a un'ora di distanza",
    "rib_h2": "Il Ribnik: temoli più grandi, a un'ora dalla porta",
    "rib_p": "Cinquanta chilometri a nord-ovest della locanda, il Ribnik scorre per cinque chilometri e mezzo prima di confluire nella Sana. È corto, basso e incredibilmente limpido — un vero chalk stream, largo appena 20 metri, profondo al massimo fino al ginocchio, con il fondo pietroso visibile a ogni lancio. Dove il Pliva vi dà temoli grandi che esaminano ogni mosca, il Ribnik ve ne dà molti di più: circa l'ottanta per cento dei pesci qui sono temoli, e arrivano a 50 cm e oltre. Nelle stesse acque vivono anche trote fario, che raggiungono il doppio chilo.",
    "rib_l1": "<b>50 km, circa un'ora</b> dalla locanda in auto",
    "rib_l2": "<b>80% temoli</b>, molti oltre 50 cm — la percentuale più alta di tutta la regione",
    "rib_l3": "<b>Bassa e facile</b> — larga 20 m, fino al ginocchio, attraversabile quasi ovunque a piedi",
    "rib_l4": "<b>Stesso permesso</b> — il tuo permesso per il Pliva vale anche per il Ribnik e la Sana",
    "rib_cta": "Chiedi una giornata sul Ribnik",
    "rib_price": "Servizio auto giornaliero per il Ribnik · da concordare alla reception",
    "nav_ribnik": "Il Ribnik",
    "r1_b": "Camera doppia o matrimoniale con vista sul fiume",
    "r1_s": "85 € a notte · colazione inclusa",
    "r2_b": "Camera singola per il pescatore da solo",
    "r2_s": "70 € a notte · colazione inclusa",
    "r3_b": "Camera tripla",
    "r3_s": "110 € a notte · vista sul fiume",
    "r4_b": "Affitto dell'intera casa",
    "r4_s": "900 € a notte · fino a 16 ospiti",
    "r5_b": "Mezza pensione",
    "r5_s": "32 € a persona al giorno · colazione e cena",
    "r6_b": "Pensione completa",
    "r6_s": "52 € a persona al giorno · tutti i pasti",
    "r7_b": "Transfer aeroportuale",
    "r7_s": "Sarajevo incluso · Banja Luka e Split su richiesta",
    "r8_b": "Noleggio attrezzatura",
    "r8_s": "Canna, mulinello, lenza e stivali da guado · 22 € al giorno",
    "rib_price_sub": "≈ 50 km · circa un'ora per tratta",
    "quote_text": "\"Ci sono peschi in abbondanza, e non sono per nulla più diffidenti verso l'esca di quanto lo siano in fiumi come il Test o l'Itchen — ma sono incredibilmente selettivi. Se avete mai pensato di pescare in un posto nuovo, è questo il viaggio che cambia il modo in cui pescate.\"",
    "pkg2_winter": "Nov–dic: <b>950 €</b> a persona",
    "pkg3_winter": "Nov–dic: <b>730 €</b> a persona",
}


def main():
    raw = DICT.read_text(encoding="utf-8")
    head = raw[: raw.index("{")]
    body = raw[raw.index("{") : raw.rindex("}") + 1]
    data = json.loads(body)

    missing = sorted(set(data) - set(IT))
    extra = sorted(set(IT) - set(data))
    if missing:
        print(f"ERROR: no Italian for: {', '.join(missing)}", file=sys.stderr)
        return 1
    if extra:
        print(f"ERROR: Italian for unknown keys: {', '.join(extra)}", file=sys.stderr)
        return 1

    # Build the new file, keeping the original key order and formatting style.
    out = [head, "{\n"]
    keys = list(data.keys())
    for i, k in enumerate(keys):
        e = data[k]
        out.append(f'  "{k}": {{\n')
        out.append(f'    "en": {json.dumps(e["en"], ensure_ascii=False)},\n')
        out.append(f'    "de": {json.dumps(e["de"], ensure_ascii=False)},\n')
        out.append(f'    "bs": {json.dumps(e["bs"], ensure_ascii=False)},\n')
        out.append(f'    "it": {json.dumps(IT[k], ensure_ascii=False)}\n')
        out.append("  }" + ("," if i < len(keys) - 1 else "") + "\n")
    out.append("};\n")

    DICT.write_text("".join(out), encoding="utf-8")
    print(f"Wrote {len(keys)} keys with an Italian column.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
