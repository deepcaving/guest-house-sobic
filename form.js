/* Pliva River Lodge - enquiry form.
 *
 * The guest fills the form and presses "Send enquiry". We want three things
 * to happen, in this order of preference:
 *
 *   1. The enquiry is EMAILED from the server, by the Netlify Function in
 *      netlify/functions/enquiry.mjs. It arrives in Milka's inbox, with the
 *      collaborator copied, and the guest does nothing beyond pressing the
 *      button. This is the path the host asked for.
 *   2. If the function is not configured or the provider is down, the
 *      enquiry still goes to Netlify Forms, so it is stored in the Netlify
 *      dashboard and never lost.
 *   3. If that also fails, WhatsApp opens with the enquiry written out, and
 *      the guest's own mail app opens too.
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
   * Send the enquiry through the Netlify Function. Resolves to true when the
   * email was sent, false when it could not be - in which case the caller
   * falls back to Netlify Forms and WhatsApp.
   */
  function sendByEmail() {
    if (!functionUrl || typeof fetch !== 'function') return Promise.resolve(false);

    return fetch(functionUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(collectFields())
    })
      .then(function (r) {
        if (!r.ok) return false;
        return r.json().then(function (j) { return !!(j && j.ok); });
      })
      ['catch'](function () { return false; });
  }

  /** Store the enquiry in Netlify Forms. Best effort - never fatal. */
  function saveToNetlifyForms() {
    try {
      return fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(new FormData(form)).toString()
      })['catch'](function () {});
    } catch (err) {
      return undefined;
    }
  }

  function openWhatsApp() {
    if (!waBase) return;
    var url = waBase + '?text=' + encodeURIComponent(composeMessage());
    var w = window.open(url, '_blank');
    if (w) w.opener = null;
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

  function openMailApp() {
    if (!emailTo) return;
    var subject = 'Website enquiry';
    var dateField = form.querySelector('[name="dates"]');
    if (dateField && dateField.value.trim()) {
      subject += ' - ' + dateField.value.trim();
    }
    var mailto = 'mailto:' + emailTo +
      '?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(composeMessage());
    var m = window.open(mailto, '_blank');
    if (m) m.opener = null;
  }

  wireWhatsAppLinks();

  // Keep the WhatsApp links in step with what the guest has typed.
  var fields = form.querySelectorAll('input[name], select[name], textarea[name]');
  for (var f = 0; f < fields.length; f++) {
    fields[f].addEventListener('input', refreshWhatsAppLinks);
    fields[f].addEventListener('change', refreshWhatsAppLinks);
  }
  refreshWhatsAppLinks();

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // Honeypot filled in = bot. Say nothing, send nothing.
    if (bot && bot.value) return;

    var btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.setAttribute('aria-busy', 'true');
    }

    // 1. Email, from the server. This is the path that matters.
    sendByEmail().then(function (sent) {
      if (sent) {
        // 2. Also keep a copy in the Netlify dashboard.
        saveToNetlifyForms();
        show(statusOk);
        if (status) status.hidden = true;
        if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
        return;
      }

      // 3. The function is not available. Do not lose the enquiry.
      saveToNetlifyForms();
      openWhatsApp();
      openMailApp();
      show(statusFallback);
      if (status) status.hidden = true;
      if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
    });
  });
})();
