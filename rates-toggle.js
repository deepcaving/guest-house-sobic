/* Pliva River Lodge - rates toggle.
 *
 * The rates grid lists what the lodge charges: the room, the meals, the
 * guide, the transfers. The fishing licence is a third-party government
 * charge, so it sits outside those prices.
 *
 * Many guests are not going to fish - they come for the river, the food and
 * the quiet. Showing a licence-inclusive total as the headline would
 * frighten them off for a cost they will never pay. So the totals come in
 * two versions and the guest picks:
 *
 *   "Room and meals only"     - what a non-angler actually pays
 *   "Including the fishing    - what a fishing day comes to in total
 *    licence"
 *
 * The licence-inclusive version is never hidden; it is one click away, and
 * the licence price is always shown on its own line.
 *
 * i18n.js rewrites the total paragraph whenever the language changes, so
 * this module listens for that and re-applies the chosen version.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'prl_rates_view';

  var total = document.getElementById('ratesTotal');
  if (!total) return;

  var radios = document.querySelectorAll('input[name="rates-view"]');
  if (!radios.length) return;

  // The two versions of the total, keyed by mode. The text is read from the
  // dictionary so it follows the page language.
  function dictionary() {
    return (window.I18N && window.I18N) || {};
  }

  function currentLang() {
    return document.body.getAttribute('data-lang') || 'en';
  }

  /** The dictionary key for a mode: sep -> rates_total_sep, inc -> rates_total_inc. */
  function keyFor(mode) {
    return mode === 'inc' ? 'rates_total_inc' : 'rates_total_sep';
  }

  /** Write the chosen version of the total into the paragraph. */
  function render(mode) {
    var key = keyFor(mode);
    var dict = dictionary();
    var entry = dict[key];
    var txt = entry ? entry[currentLang()] : null;
    if (txt === null || txt === undefined) return;
    total.innerHTML = txt;
    total.setAttribute('data-mode', mode);
  }

  /** Read the saved choice, defaulting to "room and meals only". */
  function savedMode() {
    try {
      var v = window.localStorage.getItem(STORAGE_KEY);
      return v === 'inc' ? 'inc' : 'sep';
    } catch (e) {
      return 'sep';
    }
  }

  function saveMode(mode) {
    try {
      window.localStorage.setItem(STORAGE_KEY, mode);
    } catch (e) { /* private mode - the choice just will not persist */ }
  }

  function setMode(mode, persist) {
    for (var i = 0; i < radios.length; i++) {
      var r = radios[i];
      if (r.value === mode) r.checked = true;
    }
    render(mode);
    if (persist) saveMode(mode);
  }

  for (var i = 0; i < radios.length; i++) {
    (function (radio) {
      radio.addEventListener('change', function () {
        if (!radio.checked) return;
        setMode(radio.value, true);
      });
    })(radios[i]);
  }

  // i18n.js rewrites every [data-i18n-key] element on a language change,
  // including the total paragraph. Re-apply the chosen version afterwards.
  document.addEventListener('prl:langchange', function () {
    setMode(savedMode(), false);
  });

  // First paint.
  setMode(savedMode(), false);
})();
