/* Pliva River Lodge - enquiry form.
 *
 * The guest fills the form and presses "Send enquiry". We want three things
 * to happen, in this order of preference:
 *
 *   1. The enquiry is EMAILED from the server, by the Netlify Function in
 *      netlify/functions/enquiry.mjs. It arrives in Milka's inbox, with the
 *      collaborator blind-copied, and the guest does nothing beyond pressing
 *      the button. This is the path the host asked for.
 *   2. A copy always goes to Netlify Forms as well, so the enquiry is in the
 *      Netlify dashboard and never lost.
 *   3. If the email could not be sent, the guest is told so plainly. The
 *      button does NOT open WhatsApp and does NOT open the guest's mail app:
 *      WhatsApp is a separate, clearly labelled link on the page.
 *
 * With JavaScript off, the form posts to Netlify Forms as a normal Netlify
 * Form (data-netlify="true"), so the enquiry is still captured.
 */
(function () {
  'use strict';

  var form = document.getElementById('enquiry-form');
  if (!form) return;

  var waBase = form.getAttribute('data-wa');
  var emailTo = form.getAttribute('data-email');
  var functionUrl = form.getAttribute('data-function');
  var status = document.getElementById('enquiry-status');
  var statusOk = document.getElementById('enquiry-status-ok');
  var statusFallback = document.getElementById('enquiry-status-fallback');
  var bot = form.querySelector('[name="bot-field"]');

  function fieldLabel(el) {
    var lab = form.querySelector('label[for="' + el.id + '"]');
    return lab ? lab.textContent.replace(/\s+/g, ' ').trim() : el.name;
  }

  /* The occupancy fields are hidden inputs, so they have no visible label
   * to read. Give them names a guest would understand. */
  var FIELD_LABELS = {
    flyfishing: 'Fly fishing',
    people_mode: 'Trip type',
    people: 'People',
    people_label: 'Occupancy',
    adults: 'Adults',
    children: 'Children',
    rooms: 'Rooms'
  };

  /* The month names, in the four languages, so a date written as a word
   * ("in December") is recognised as a date and not as nonsense. */
  var MONTH_NAMES = (
    'january february march april may june july august september october november december ' +
    'januar februar maerz märz mai juni juli august september oktober november dezember ' +
    'januar februar mart april maj juni juli august septembar oktobar novembar decembar ' +
    'gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre'
  ).split(' ');
  var MONTH_WORDS = new RegExp(MONTH_NAMES.map(function (w) {
    return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }).join('|'), 'i');

  /* The example markers the four languages use in the placeholder:
   * "e.g.", "z. B.", "npr.", "es.". A value that starts with one of them
   * and then a number is our example, copied over, not a choice. */
  var EXAMPLE_MARKER = /^(e\.?\s?g\.?|z\.?\s?b\.?|npr\.?|es\.|example|beispiel|primjer|esempio|per esempio)\s*\d/i;

  var datesErrorKey = null;

  /* The language the page is showing right now. */
  function currentLang() {
    try {
      var stored = localStorage.getItem('prl_lang');
      if (stored) return stored;
    } catch (err) { /* private mode */ }
    var el = document.documentElement;
    return (el && el.getAttribute('lang')) || 'en';
  }

  /**
   * Check the preferred dates.
   *
   * The field shows an EXAMPLE range as its placeholder, and the guest must
   * replace it with their own dates. The dates are required: an enquiry
   * without them cannot be answered, and the example must never reach
   * Milka's inbox as if the guest had chosen it.
   *
   * Returns null when the value is good, or the i18n key of the message to
   * show when it is not.
   */
  function validateDates() {
    var field = document.getElementById('f-dates');
    if (!field) return null;
    var value = String(field.value || '').trim();

    if (!value) return 'form_dates_error';

    // Our own placeholder, copied over character for character.
    var placeholder = String(field.getAttribute('placeholder') || '').trim();
    if (placeholder && value.toLowerCase() === placeholder.toLowerCase()) {
      return 'form_dates_example';
    }

    // Our example with the marker still on it.
    if (EXAMPLE_MARKER.test(value)) return 'form_dates_example';

    // A date answer carries a day number or a month name.
    if (!/\d/.test(value) && !MONTH_WORDS.test(value)) return 'form_dates_error';

    return null;
  }

  /* Show or clear the message under the dates field. */
  function showDatesError(key) {
    var error = document.getElementById('f-dates-error');
    var field = document.getElementById('f-dates');
    datesErrorKey = key || null;
    if (error) {
      if (!key) {
        error.hidden = true;
      } else {
        var dict = (typeof window !== 'undefined' && window.I18N) ? window.I18N : null;
        var entry = dict && dict[key];
        var lang = currentLang();
        var text = entry && (entry[lang] || entry.en);
        if (text) error.textContent = text;
        error.hidden = false;
      }
    }
    if (field) {
      if (key) field.setAttribute('aria-invalid', 'true');
      else field.removeAttribute('aria-invalid');
    }
  }

  function composeMessage() {
    var lines = ['Enquiry from the website', ''];
    var fields = form.querySelectorAll('input[name], select[name], textarea[name]');
    for (var i = 0; i < fields.length; i++) {
      var el = fields[i];
      if (el.name === 'form-name' || el.name === 'bot-field') continue;
      var val = (el.value || '').trim();
      if (!val) continue;
      // The trip type reads better as words than as "fishing"/"booking".
      if (el.name === 'people_mode') {
        val = val === 'fishing' ? 'Fly fishing' : 'General stay';
      }
      if (el.name === 'flyfishing') {
        val = val === 'yes' ? 'yes' : 'no';
      }
      var label = FIELD_LABELS[el.name] || fieldLabel(el);
      lines.push(label + ': ' + val);
    }
    lines.push('');
    lines.push('Sent from ' + location.href);
    return lines.join('\n');
  }

  /** The fields, as a plain object the function understands. */
  function collectFields() {
    var out = { 'form-name': form.getAttribute('name') || 'enquiry', page: location.href };
    var fields = form.querySelectorAll('input[name], select[name], textarea[name]');
    for (var i = 0; i < fields.length; i++) {
      var el = fields[i];
      if (el.name === 'form-name') continue;
      out[el.name] = (el.value || '').trim();
    }
    return out;
  }

  function show(el) {
    if (el) el.hidden = false;
  }

  /**
   * Send the enquiry through the Netlify Function.
   *
   * Resolves to { sent: true } when the email went out. When it did not,
   * it resolves to { sent: false, reason: <what the server said> } so the
   * failure can be reported honestly instead of being swallowed.
   */
  function sendByEmail() {
    if (!functionUrl || typeof fetch !== 'function') {
      return Promise.resolve({ sent: false, reason: 'no-function' });
    }

    return fetch(functionUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(collectFields())
    })
      .then(function (r) {
        return r.json().catch(function () { return null; })
          .then(function (j) {
            if (r.ok && j && j.ok) return { sent: true };
            return {
              sent: false,
              reason: (j && (j.error || j.detail && j.detail.message)) || ('HTTP ' + r.status),
              // The server can name the field it refused, so the message
              // goes next to the field instead of the generic message.
              field: (j && j.field) || null
            };
          });
      })
      ['catch'](function (err) {
        return { sent: false, reason: String(err && err.message) };
      });
  }

  /**
   * Store a copy of the enquiry in Netlify Forms. Best effort - never fatal.
   *
   * This is a second safety net on top of the server-side copy that the
   * enquiry function writes itself. That server-side copy does not depend
   * on Netlify's "form detection" switch being on in the dashboard, so it
   * is the one that matters; this browser-side POST is kept because it
   * costs nothing and covers the case where the function is unreachable.
   *
   * The body is built from collectFields(), NOT from FormData. FormData
   * drops an UNCHECKED checkbox, so the Fly fishing switch went missing
   * from this copy while the email had it - the two copies of the same
   * enquiry disagreed. Using the same object the function receives makes
   * them identical by construction.
   */
  function saveToNetlifyForms() {
    try {
      var fields = collectFields();
      // The honeypot stays, so Netlify's own spam protection still applies.
      fields['bot-field'] = bot ? bot.value : '';
      return fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(fields).toString()
      })['catch'](function () {});
    } catch (err) {
      return undefined;
    }
  }

  /**
   * Make every WhatsApp link on the page open a chat with the enquiry
   * already written out, so a guest who taps "WhatsApp" does not have to
   * retype anything they have already filled in. The contact-block link and
   * the button under the form both get this.
   *
   * The href is kept up to date as the guest types, so the link is already
   * correct before it is clicked - and if JavaScript never runs, the plain
   * wa.me link still opens a chat.
   */
  function wireWhatsAppLinks() {
    var links = document.querySelectorAll('a[href*="wa.me/"]');
    for (var i = 0; i < links.length; i++) {
      (function (link) {
        // Keep the plain chat link as the fallback in case the guest has not
        // filled anything in yet.
        var base = waBase || link.getAttribute('href').split('?')[0];
        link.setAttribute('href', base);
        link.addEventListener('click', function () {
          refreshWhatsAppLinks();
        });
      })(links[i]);
    }
  }

  /** Rewrite every WhatsApp href with the current enquiry text. */
  function refreshWhatsAppLinks() {
    var text = composeMessage();
    // "Enquiry from the website" on its own is not worth sending.
    var hasContent = /:\s*\S/.test(text);
    var links = document.querySelectorAll('a[href*="wa.me/"]');
    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      var base = (waBase || link.getAttribute('href').split('?')[0]).split('?')[0];
      link.setAttribute(
        'href',
        hasContent ? base + '?text=' + encodeURIComponent(text) : base
      );
    }
  }

  wireWhatsAppLinks();

  // Keep the WhatsApp links in step with what the guest has typed.
  var fields = form.querySelectorAll('input[name], select[name], textarea[name]');
  for (var f = 0; f < fields.length; f++) {
    fields[f].addEventListener('input', refreshWhatsAppLinks);
    fields[f].addEventListener('change', refreshWhatsAppLinks);
  }
  refreshWhatsAppLinks();

  /* Record a WhatsApp click.
   *
   * Opening WhatsApp is the moment of interest: the guest has not sent an
   * enquiry, but they are here and they want to talk. The record lands in
   * Netlify Forms, so it shows up in the dashboard beside the enquiries,
   * with the visitor's IP address and their approximate location.
   *
   * It must never delay or break the chat. The link opens normally whether
   * this request succeeds or not, so the result is ignored on purpose.
   */
  function recordWhatsAppClick(link) {
    try {
      var url = form.getAttribute('data-function-click') ||
        '/.netlify/functions/whatsapp-click';
      var fields = collectFields();
      var payload = {
        page: location.href,
        link: link.getAttribute('data-wa-label') ||
          (link.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
        trip: fields.people_mode === 'fishing' ? 'Fly fishing' : 'General stay',
        dates: fields.dates || '',
        people: fields.people_label || fields.people || '',
        language: currentLang()
      };
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        // The guest is on their way to WhatsApp; the request has to
        // survive the page going quiet.
        keepalive: true
      })['catch'](function () {});
    } catch (err) {
      /* Never break the link. */
    }
  }

  /* Every WhatsApp link on the page, wherever it is. A delegated listener
   * catches the header, the contact block, the button under the form and
   * the footer, including any that are added later. */
  document.addEventListener('click', function (e) {
    var link = e.target && e.target.closest ? e.target.closest('a[href*="wa.me"]') : null;
    if (link) recordWhatsAppClick(link);
  });

  /* The message disappears as soon as the guest starts correcting it. */
  var datesInput = document.getElementById('f-dates');
  if (datesInput) {
    datesInput.addEventListener('input', function () {
      if (datesErrorKey) showDatesError(null);
    });

    /* The browser's OWN validation runs before the submit event, so an
     * empty field never reaches validateDates(). The invalid event is
     * how the browser says so - and it does not bubble, so it has to be
     * caught on the field itself. Showing our message here means the
     * guest reads it in the language of the PAGE, not the language of
     * their browser. */
    datesInput.addEventListener('invalid', function () {
      showDatesError('form_dates_error');
    });
  }

  /* i18n.js rewrites the message from the dictionary when the language
   * changes, so the message we chose is put back afterwards. */
  document.addEventListener('prl:langchange', function () {
    if (datesErrorKey) showDatesError(datesErrorKey);
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // Honeypot filled in = bot. Say nothing, send nothing.
    if (bot && bot.value) return;

    var btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.setAttribute('aria-busy', 'true');
    }

    // "Send enquiry" sends an email. Nothing else.
    //
    // It deliberately does NOT open WhatsApp, and does NOT open the guest's
    // mail app. A button that says "send" and then launches two other
    // applications is confusing, and it takes the guest away from the page
    // without their consent. WhatsApp is a separate, clearly labelled
    // button right next to this one, and it stays a plain link.
    //
    // If the server cannot send the email, the enquiry is still saved to
    // Netlify Forms, the guest is told plainly that the email did not go
    // out, and the WhatsApp and phone links on the page remain available.
    // The preferred dates are required, and the placeholder is only an
    // example. Nothing leaves the browser until the guest has given dates
    // of their own.
    var datesProblem = validateDates();
    if (datesProblem) {
      showDatesError(datesProblem);
      var datesField = document.getElementById('f-dates');
      if (datesField) datesField.focus();
      if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
      return;
    }
    showDatesError(null);

    sendByEmail().then(function (result) {
      if (result.sent) {
        saveToNetlifyForms();
        show(statusOk);
        if (status) status.hidden = true;
        if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
        return;
      }

      // The server refused the dates. Say so where the guest is looking,
      // not with the "email could not be sent" message.
      if (result.field === 'dates') {
        showDatesError('form_dates_error');
        var field = document.getElementById('f-dates');
        if (field) field.focus();
        if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
        return;
      }

      // The function is not available, or the provider refused the send.
      // Do not lose the enquiry - keep a copy in Netlify Forms.
      saveToNetlifyForms();
      show(statusFallback);
      if (status) status.hidden = true;
      if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
    });
  });
})();
