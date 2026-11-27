#!/usr/bin/env python3
"""The labels of the photo viewer, in the six languages.

    python3 tools/gallery_labels.py

The viewer is built by gallery.js, so these words are not in the markup
the way the rest of the text is: the script reads them from the
dictionary when it opens the viewer, and again when the visitor changes
the language.

The counter ("12 / 84") needs no translation - a number is a number.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _dict_writer import insert_keys

LABELS = {
    "gal_lb_title": {
        "en": "Photo gallery",
        "de": "Fotogalerie",
        "bs": "Galerija fotografija",
        "it": "Galleria fotografie",
        "fr": "Galerie de photos",
        "nl": "Fotogalerij",
    },
    "gal_lb_close": {
        "en": "Close",
        "de": "Schließen",
        "bs": "Zatvori",
        "it": "Chiudi",
        "fr": "Fermer",
        "nl": "Sluiten",
    },
    "gal_lb_prev": {
        "en": "Previous photo",
        "de": "Vorheriges Foto",
        "bs": "Prethodna fotografija",
        "it": "Foto precedente",
        "fr": "Photo précédente",
        "nl": "Vorige foto",
    },
    "gal_lb_next": {
        "en": "Next photo",
        "de": "Nächstes Foto",
        "bs": "Sljedeća fotografija",
        "it": "Foto successiva",
        "fr": "Photo suivante",
        "nl": "Volgende foto",
    },
    "gal_lb_photo": {
        "en": "Photo",
        "de": "Foto",
        "bs": "Fotografija",
        "it": "Foto",
        "fr": "Photo",
        "nl": "Foto",
    },
}

if __name__ == "__main__":
    raise SystemExit(insert_keys(LABELS, "gal_p"))
