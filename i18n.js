/* Pliva River Lodge - language switcher.
   EN (default) / DE / BS / IT. Choice is remembered in localStorage.

   How it works: every translatable element carries data-i18n-key="<key>".
   The translations live in i18n-data.js as window.I18N[key][lang].
   The English text stays in the markup, so the page reads correctly
   even if the script fails to load.

   The language is also part of the address: ?lang=it opens the Italian
   page, and the address bar follows whatever language is on screen.

   Elements with data-i18n-inline="1" get textContent (keeps <b> from
   breaking the line); everything else gets innerHTML (allows <br>). */
(function () {
  'use strict';

  var LANGS = ['en', 'de', 'bs', 'it'];
  var KEY = 'prl_lang';
  var root = document.documentElement;
  var body = null;
  var switcher = null;
  var label = null;

  function readStored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function store(v) {
    try { localStorage.setItem(KEY, v); } catch (e) { /* private mode */ }
  }

  /* The language is part of the address: ?lang=de opens the German page.
     That way a link sent to a German angler shows the German page even if
     their browser is set to something else - which is the whole point when
     the link is being shared in a Facebook group or a DM. */
  function fromUrl() {
    try {
      var q = new URLSearchParams(window.location.search).get('lang');
      if (!q) return null;
      q = q.toLowerCase();
      return LANGS.indexOf(q) !== -1 ? q : null;
    } catch (e) { return null; }
  }

  function detect() {
    var u = fromUrl();
    if (u) return u;
    var v = readStored();
    if (v && LANGS.indexOf(v) !== -1) return v;
    var nav = (navigator.language || 'en').toLowerCase();
    if (nav.indexOf('de') === 0) return 'de';
    if (nav.indexOf('it') === 0) return 'it';
    if (nav.indexOf('bs') === 0 || nav.indexOf('hr') === 0 ||
        nav.indexOf('sr') === 0 || nav.indexOf('ba') === 0) return 'bs';
    return 'en';
  }

  /* Keep the address bar in step with the language on screen, so that
     copying the URL always copies the version the visitor is reading. */
  function syncUrl(lang) {
    if (!window.history || !window.history.replaceState) return;
    try {
      var url = new URL(window.location.href);
      if (lang === 'en') url.searchParams.delete('lang');
      else url.searchParams.set('lang', lang);
      window.history.replaceState({}, '',
        url.pathname + url.search + url.hash);
    } catch (e) { /* leave the URL alone */ }
  }

  function tr(key, lang) {
    var d = window.I18N;
    if (d && d[key] && d[key][lang] !== undefined) return d[key][lang];
    if (d && d[key] && d[key].en !== undefined) return d[key].en;
    return null;
  }

  function apply(lang) {
    if (LANGS.indexOf(lang) === -1) lang = 'en';

    if (!body) {
      body = document.body;
      if (!body) return;   // <body> not parsed yet
    }
    switcher = switcher || document.getElementById('langSwitch');
    label = label || document.getElementById('langLabel');

    body.setAttribute('data-lang', lang);
    root.setAttribute('lang', lang);
    root.classList.remove('no-js');
    syncUrl(lang);

    var nodes = document.querySelectorAll('[data-i18n-key]');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var key = el.getAttribute('data-i18n-key');
      // never replace the content of a container that holds interactive or
      // structural children (buttons, links, icons) - that would destroy them
      if (el.querySelector('button, a, svg, input, select, textarea, video, img')) continue;
      // never replace a container that holds a translated child either: the
      // child is translated on its own pass, and clobbering the parent would
      // drop the child (this is what used to delete the quote attribution)
      if (el.querySelector('[data-i18n-key]')) continue;
      var txt = tr(key, lang);
      if (txt === null) continue;
      if (el.getAttribute('data-i18n-inline') === '1') {
        el.textContent = txt;
      } else {
        el.innerHTML = txt;
      }
    }

    // placeholders
    var phs = document.querySelectorAll('[data-ph]');
    for (var j = 0; j < phs.length; j++) {
      var p = phs[j];
      var pt = tr(p.getAttribute('data-ph'), lang);
      if (pt !== null) p.setAttribute('placeholder', pt);
    }

    // switcher label + active tick
    if (label) {
      var ll = tr('lang_label', lang);
      label.textContent = ll === null ? lang.toUpperCase() : ll;
    }
    if (switcher) {
      var btns = switcher.querySelectorAll('[data-setlang]');
      for (var m = 0; m < btns.length; m++) {
        var b = btns[m];
        var isActive = b.getAttribute('data-setlang') === lang;
        b.classList.toggle('active', isActive);
        b.setAttribute('aria-checked', isActive ? 'true' : 'false');
      }
    }
  }

  function openMenu(open) {
    if (!switcher) return;
    switcher.classList.toggle('open', open);
    var btn = switcher.querySelector('.lang-btn');
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function init() {
    // resolve the DOM handles first - init() may run before <body> is parsed
    body = body || document.body;
    switcher = switcher || document.getElementById('langSwitch');
    label = label || document.getElementById('langLabel');

    if (switcher) {
      var btn = switcher.querySelector('.lang-btn');
      if (btn) {
        btn.addEventListener('click', function (e) {
          e.stopPropagation();
          openMenu(!switcher.classList.contains('open'));
        });
      }
      var items = switcher.querySelectorAll('[data-setlang]');
      for (var i = 0; i < items.length; i++) {
        items[i].addEventListener('click', function (e) {
          e.stopPropagation();
          var lang = this.getAttribute('data-setlang');
          store(lang);
          apply(lang);
          openMenu(false);
        });
      }
      document.addEventListener('click', function () { openMenu(false); });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') openMenu(false);
      });
    }
    apply(detect());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else if (!document.body) {
    // script ran in <head> before <body> existed - wait for it
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
