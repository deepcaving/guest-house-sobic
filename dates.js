/* Pliva River Lodge - live date placeholder for the enquiry form.
 *
 * The "Preferred dates" field shows an EXAMPLE range one month ahead of
 * today, so a guest is always invited to book a date in the future. The
 * month name stays in the dictionary (it is translated); only the numbers
 * are computed here.
 *
 * The template lives in the dictionary key "ph_dates" and may contain:
 *   {{d1}}   first day of the example range
 *   {{d2}}   last day of the example range
 *   {{month}} month name, in the current language
 *   {{year}}  four-digit year
 *
 * If a template has no placeholders it is used as-is - that keeps a plain
 * static placeholder working and never leaves the field empty.
 */
(function () {
  'use strict';

  // Month names, index 0 = January. One entry per language.
  var MONTHS = {
    en: ['January', 'February', 'March', 'April', 'May', 'June', 'July',
         'August', 'September', 'October', 'November', 'December'],
    de: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
         'August', 'September', 'Oktober', 'November', 'Dezember'],
    bs: ['januar', 'februar', 'mart', 'april', 'maj', 'juni', 'juli',
         'august', 'septembar', 'oktobar', 'novembar', 'decembar'],
    it: ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio',
         'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
    fr: ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
         'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    nl: ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
         'augustus', 'september', 'oktober', 'november', 'december']
  };

  /* The example range: the 10th to the 17th of the month one month from
   * now. A week-long span reads as a real booking, not a single night.
   * The day is clamped to the length of the target month, so the 31st of
   * a 30-day month still produces a valid range. */
  var DAY_FROM = 10;
  var DAY_TO = 17;

  function pad2(n) {
    return (n < 10 ? '0' : '') + n;
  }

  function daysInMonth(year, monthIndex) {
    return new Date(year, monthIndex + 1, 0).getDate();
  }

  /* The target month: one month AFTER the current one, rolling over the
   * year. Built from the local date at noon so a late-evening visitor is
   * never pushed into the previous month by a timezone offset. */
  function targetMonth(now) {
    var y = now.getFullYear();
    var m = now.getMonth() + 1;      // 0-based -> 1-based
    if (m > 11) { m = 0; y = y + 1; }
    return { year: y, month: m };
  }

  function monthName(lang, monthIndex) {
    var list = MONTHS[lang] || MONTHS.en;
    return list[monthIndex] || MONTHS.en[monthIndex];
  }

  /* Build the example date range for a language. */
  function exampleRange(lang, now) {
    var t = targetMonth(now || new Date());
    var last = daysInMonth(t.year, t.month);
    var d1 = Math.min(DAY_FROM, last);
    var d2 = Math.min(DAY_TO, last);
    return {
      d1: d1,
      d2: d2,
      month: monthName(lang, t.month),
      year: t.year,
      yearShort: String(t.year).slice(2)
    };
  }

  /* Fill a template. Returns the template unchanged when it has no
   * placeholders, and never returns an empty string. */
  function fill(template, lang, now) {
    if (!template) return '';
    if (template.indexOf('{{') === -1) return template;
    var r = exampleRange(lang, now);
    return template
      .replace(/\{\{\s*d1\s*\}\}/g, r.d1)
      .replace(/\{\{\s*d2\s*\}\}/g, r.d2)
      .replace(/\{\{\s*month\s*\}\}/g, r.month)
      .replace(/\{\{\s*year\s*\}\}/g, r.year)
      .replace(/\{\{\s*yearShort\s*\}\}/g, r.yearShort);
  }

  /* Apply the live date to every [data-ph="ph_dates"] field, in the
   * current language. Called on load and again after every language
   * change, because the month name is translated. */
  function applyDates(lang, now) {
    var dict = (typeof window !== 'undefined' && window.I18N) ? window.I18N : null;
    if (!dict) return;
    var key = 'ph_dates';
    var entry = dict[key];
    if (!entry) return;
    var tmpl = entry[lang] || entry.en;
    if (!tmpl) return;
    var text = fill(tmpl, lang, now);
    if (!text) return;
    var fields = document.querySelectorAll('[data-ph="' + key + '"]');
    for (var i = 0; i < fields.length; i++) {
      fields[i].setAttribute('placeholder', text);
    }
  }

  // Expose for the tests and for the language-change hook.
  window.PRLDates = {
    applyDates: applyDates,
    fill: fill,
    exampleRange: exampleRange,
    targetMonth: targetMonth,
    daysInMonth: daysInMonth,
    MONTHS: MONTHS
  };

  /* When the language changes, i18n.js rewrites every placeholder from
   * the dictionary - which would put the STATIC template back. So the
   * date helper re-applies itself afterwards. */
  document.addEventListener('prl:langchange', function (e) {
    var lang = (e && e.detail && e.detail.lang) || readStored() || 'en';
    applyDates(lang);
  });

  function readStored() {
    try { return localStorage.getItem('prl_lang'); } catch (err) { return null; }
  }

  /* The dictionary template and the live date can land in either order:
   * i18n.js writes the template into the placeholder, dates.js writes the
   * computed date. Both hook DOMContentLoaded, so whichever runs last
   * would win - and i18n.js must NOT win, or the raw "{{d1}}" shows.
   * A short retry loop settles it: apply the date, wait a tick, apply
   * again. Two attempts is enough for the deferred scripts to have run. */
  function currentLang() {
    var l = readStored();
    if (!l) {
      // i18n.js may have detected a language but not stored it yet
      var el = document.documentElement;
      l = (el && el.getAttribute('lang')) || 'en';
    }
    return l;
  }

  function applyWhenReady() {
    applyDates(currentLang());
    setTimeout(function () { applyDates(currentLang()); }, 60);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyWhenReady);
  } else {
    applyWhenReady();
  }
})();
