/* Pliva River Lodge - the occupancy picker in the enquiry form.
 *
 * The form asks "How many people". A fly-fishing enquiry and a
 * Booking.com-style occupancy are different questions:
 *
 *   - Fly fishing ON  -> "How many anglers?" (the dropdown: 1..5 or more)
 *   - Fly fishing OFF -> "Select occupancy" (adults, children, rooms)
 *
 * The toggle switches between them. Both write into ONE set of hidden
 * fields so the server always receives the same shape:
 *
 *   people_mode    "fishing" | "booking"
 *   people         the headline number (anglers, or total people)
 *   people_label   the guest's own wording ("2 anglers", "2 adults, 0 children, 1 room")
 *   adults         number of adults (booking mode only)
 *   children       number of children (booking mode only)
 *   rooms          number of rooms (booking mode only)
 *
 * Without JavaScript the form still posts: the dropdown stays visible with
 * its angler options, and people_mode defaults to "fishing".
 */
(function () {
  'use strict';

  var form = document.getElementById('enquiry-form');
  if (!form) return;

  var toggle = document.getElementById('f-flyfishing');
  var panelAngler = document.getElementById('people-angler');
  var panelBooking = document.getElementById('people-booking');
  var selectAngler = document.getElementById('f-people');
  var hiddenMode = document.getElementById('f-people-mode');
  var hiddenLabel = document.getElementById('f-people-label');
  var hiddenAdults = document.getElementById('f-adults');
  var hiddenChildren = document.getElementById('f-children');
  var hiddenRooms = document.getElementById('f-rooms');

  if (!toggle || !panelAngler || !panelBooking) return;

  var MIN = 0;
  var MAX = 20;

  /** The +/- stepper rows. */
  function stepper(name) {
    return {
      input: document.getElementById('occ-' + name),
      minus: document.querySelector('[data-step="' + name + '-"]'),
      plus: document.querySelector('[data-step="' + name + '+"]')
    };
  }

  var adults = stepper('adults');
  var children = stepper('children');
  var rooms = stepper('rooms');

  function clamp(value) {
    var n = parseInt(value, 10);
    if (isNaN(n)) n = MIN;
    if (n < MIN) n = MIN;
    if (n > MAX) n = MAX;
    return n;
  }

  /** The angler option values are "1".."5" and "5+". */
  function anglerCount() {
    if (!selectAngler) return 0;
    var raw = selectAngler.value;
    if (raw === '5+') return 5;
    var n = parseInt(raw, 10);
    return isNaN(n) ? 0 : n;
  }

  function isFishing() {
    return !!(toggle && toggle.checked);
  }

  /** Update every hidden field from the current state. */
  function sync() {
    var fishing = isFishing();
    var label, people;

    // An unchecked checkbox posts nothing, so the value is set here
    // explicitly. The email and the Netlify Forms copy then both know
    // which way the guest answered.
    if (toggle) toggle.value = fishing ? 'yes' : 'no';

    if (fishing) {
      people = anglerCount();
      label = selectAngler && selectAngler.selectedOptions.length
        ? selectAngler.selectedOptions[0].textContent.trim()
        : '';
      if (hiddenAdults) hiddenAdults.value = '';
      if (hiddenChildren) hiddenChildren.value = '';
      if (hiddenRooms) hiddenRooms.value = '';
    } else {
      var a = adults.input ? clamp(adults.input.value) : 0;
      var c = children.input ? clamp(children.input.value) : 0;
      var r = rooms.input ? clamp(rooms.input.value) : 0;
      people = a + c;
      label = peopleLabel(a, c, r);
      if (hiddenAdults) hiddenAdults.value = String(a);
      if (hiddenChildren) hiddenChildren.value = String(c);
      if (hiddenRooms) hiddenRooms.value = String(r);
    }

    if (hiddenMode) hiddenMode.value = fishing ? 'fishing' : 'booking';
    if (hiddenLabel) hiddenLabel.value = label;

    // The "people" field is what the rest of the site and the older
    // templates read. Keep it meaningful in both modes.
    var peopleField = document.getElementById('f-people-value');
    if (peopleField) peopleField.value = label || String(people);

    updateSummary();
  }

  /**
   * The occupancy sentence, in the same shape as the Booking.com selector:
   * "2 adults, 0 children, 1 room".
   *
   * The wording comes from the dictionary ("occ_summary_tpl") so it is in
   * the guest's language. The numbers are ours.
   */
  /**
   * The occupancy sentence: "2 adults, 0 children, 1 room".
   *
   * Each phrase has its own singular and plural form, so a party of two
   * adults and one room reads "2 adults, 0 children, 1 room" and never
   * "1 rooms". The words come from the dictionary so they are translated.
   */
  function peopleLabel(a, c, r) {
    var joiner = templateFor('occ_summary_join');
    var parts = [];
    parts.push(phrase('occ_adults', a));
    parts.push(phrase('occ_children', c));
    parts.push(phrase('occ_rooms', r));
    if (!joiner) joiner = ', ';
    return parts.join(joiner);
  }

  /**
   * One count, in the right singular or plural form.
   *
   * The keys are spelled out rather than built from a base name, so that
   * check_i18n.py can see that every one of them is actually used.
   */
  function phrase(base, n) {
    var key;
    if (base === 'occ_adults') {
      key = n === 1 ? 'occ_adults_1' : 'occ_adults_n';
    } else if (base === 'occ_children') {
      key = n === 1 ? 'occ_children_1' : 'occ_children_n';
    } else {
      key = n === 1 ? 'occ_rooms_1' : 'occ_rooms_n';
    }
    var tpl = templateFor(key);
    if (tpl) return tpl.replace(/\{n\}/g, n);
    // Fallback if the dictionary is missing.
    return n + ' ' + base.replace('occ_', '');
  }

  /** Read a dictionary entry for the current language. */
  function templateFor(key) {
    var dict = (typeof window !== 'undefined' && window.I18N) ? window.I18N : null;
    if (!dict || !dict[key]) return null;
    var lang = currentLang();
    return dict[key][lang] || dict[key].en || null;
  }

  function currentLang() {
    try {
      var stored = localStorage.getItem('prl_lang');
      if (stored) return stored;
    } catch (err) { /* private mode */ }
    var el = document.documentElement;
    return (el && el.getAttribute('lang')) || 'en';
  }

  /** Write the occupancy sentence into the visible summary line. */
  function updateSummary() {
    var summary = document.getElementById('occ-summary');
    if (!summary) return;
    var a = adults.input ? clamp(adults.input.value) : 0;
    var c = children.input ? clamp(children.input.value) : 0;
    var r = rooms.input ? clamp(rooms.input.value) : 0;
    summary.textContent = peopleLabel(a, c, r);
  }

  function showPanel(fishing) {
    panelAngler.hidden = !fishing;
    panelBooking.hidden = fishing;
  }

  function wireStepper(s, name) {
    if (!s.input) return;
    var apply = function () {
      s.input.value = String(clamp(s.input.value));
      sync();
    };
    if (s.minus) {
      s.minus.addEventListener('click', function () {
        // clamp() takes a NUMBER. s.input.value is a string, and "1" + 1
        // is "11", not 2 - so the arithmetic must be done on a parsed
        // number, never on the raw string.
        s.input.value = String(clamp(clamp(s.input.value) - 1));
        sync();
      });
    }
    if (s.plus) {
      s.plus.addEventListener('click', function () {
        s.input.value = String(clamp(clamp(s.input.value) + 1));
        sync();
      });
    }
    s.input.addEventListener('change', apply);
    s.input.addEventListener('input', apply);
  }

  wireStepper(adults, 'adults');
  wireStepper(children, 'children');
  wireStepper(rooms, 'rooms');

  if (toggle) {
    toggle.addEventListener('change', function () {
      showPanel(isFishing());
      sync();
    });
  }
  if (selectAngler) {
    selectAngler.addEventListener('change', sync);
  }

  // Start in the state the markup describes: the toggle is unchecked, so
  // the Booking.com occupancy panel is the visible one.
  showPanel(isFishing());
  sync();

  // Keep the WhatsApp preview and the rest of the page in step.
  document.addEventListener('prl:langchange', function () {
    sync();
    updateSummary();
  });
})();
