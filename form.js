/* Pliva River Lodge - enquiry form.
 *
 * The form is a Netlify Form (data-netlify="true"), so with JavaScript off
 * the browser posts it the normal way and Netlify stores the enquiry.
 *
 * With JavaScript on we do two things at once:
 *   1. POST the enquiry to Netlify in the background, so it also lands in the
 *      Netlify dashboard.
 *   2. Open WhatsApp with the enquiry already written out, so a guest who
 *      finds the site on a host without a form backend still reaches us.
 *
 * WhatsApp is the channel that actually gets answered, so it leads.
 */
(function () {
  'use strict';

  var form = document.getElementById('enquiry-form');
  if (!form) return;

  var waBase = form.getAttribute('data-wa');
  var status = document.getElementById('enquiry-status');
  var bot = form.querySelector('[name="bot-field"]');

  function fieldLabel(el) {
    var lab = form.querySelector('label[for="' + el.id + '"]');
    return lab ? lab.textContent.replace(/\s+/g, ' ').trim() : el.name;
  }

  function composeMessage() {
    var lines = ['Enquiry from the website', ''];
    var fields = form.querySelectorAll('input[name], select[name], textarea[name]');
    for (var i = 0; i < fields.length; i++) {
      var el = fields[i];
      if (el.name === 'form-name' || el.name === 'bot-field') continue;
      var val = (el.value || '').trim();
      if (!val) continue;
      lines.push(fieldLabel(el) + ': ' + val);
    }
    lines.push('');
    lines.push('Sent from ' + location.href);
    return lines.join('\n');
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // Honeypot filled in = bot. Say nothing, send nothing.
    if (bot && bot.value) return;

    // 1. Netlify Forms - background only, failures are not fatal.
    try {
      fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(new FormData(form)).toString()
      })['catch'](function () {});
    } catch (err) { /* fetch unavailable - WhatsApp still works */ }

    // 2. WhatsApp - the guest's details, ready to send.
    if (waBase) {
      var url = waBase + '?text=' + encodeURIComponent(composeMessage());
      var w = window.open(url, '_blank');
      if (w) w.opener = null;
    }

    if (status) {
      status.hidden = false;
      status.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });
})();
