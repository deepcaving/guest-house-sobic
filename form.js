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
              reason: (j && (j.error || j.detail && j.detail.message)) || ('HTTP ' + r.status)
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
   */
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
    sendByEmail().then(function (result) {
      if (result.sent) {
        saveToNetlifyForms();
        show(statusOk);
        if (status) status.hidden = true;
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
