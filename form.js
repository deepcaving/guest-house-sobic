/* Pliva River Lodge - enquiry form.
 *
 * The form is a Netlify Form (data-netlify="true"), so with JavaScript off
 * the browser posts it the normal way and Netlify stores the enquiry.
 *
 * With JavaScript on we do three things at once:
 *   1. POST the enquiry to Netlify in the background, so it also lands in the
 *      Netlify dashboard.
 *   2. Open WhatsApp with the enquiry already written out, so a guest who
 *      finds the site on a host without a form backend still reaches us.
 *   3. Open the guest's mail client with the enquiry ready to send, so the
 *      enquiry also reaches the host by email.
 *
 * WhatsApp is the channel that actually gets answered, so it leads. The email
 * path is the one the host asked for, so it is opened too - the guest just
 * has to press send in their own mail app, which keeps the message in their
 * hands and out of a third party's server.
 */
(function () {
  'use strict';

  var form = document.getElementById('enquiry-form');
  if (!form) return;

  var waBase = form.getAttribute('data-wa');
  var emailTo = form.getAttribute('data-email');
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

    // 3. Email - the host asked for enquiries to reach her by email.
    // A mailto: is used rather than posting from the browser, so the guest
    // stays in control of what they send and no third-party script handles
    // their details. The subject carries the dates so it is readable in the
    // inbox list.
    if (emailTo) {
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

    if (status) {
      status.hidden = false;
      status.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });
})();
