/* Pliva River Lodge - the photo gallery.

   Clicking a picture opens it OVER the page, the way the gallery on
   booking.com works: no new page, no going back. The arrows, the arrow
   keys and a swipe move between the pictures, the counter says which one
   you are looking at, and the strip at the bottom jumps straight to any
   of them.

   The grid holds the small pictures (500 px). The large ones (up to
   1280 px) are fetched only when a picture is opened, and the two next
   to it are fetched in advance so the arrows never wait.

   The buttons carry their own labels in the six languages; the labels
   are refreshed when the visitor changes the language. */
(function () {
  'use strict';

  var items = [];
  var index = 0;
  var box = null, imgEl = null, countEl = null, stripEl = null, closeBtn = null;
  var lastFocus = null;
  var touchX = null;

  function tr(key, fallback) {
    var d = window.I18N && window.I18N[key];
    var lang = document.documentElement.getAttribute('lang') || 'en';
    if (d && d[lang] !== undefined) return d[lang];
    if (d && d.en !== undefined) return d.en;
    return fallback;
  }

  function label(key, fallback) {
    var el = document.createElement('span');
    el.textContent = tr(key, fallback);
    return el;
  }

  function build() {
    if (box) return;
    box = document.createElement('div');
    box.className = 'lightbox';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.hidden = true;

    var top = document.createElement('div');
    top.className = 'lb-top';

    countEl = document.createElement('span');
    countEl.className = 'lb-count';
    top.appendChild(countEl);

    closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'lb-close';
    closeBtn.setAttribute('aria-label', tr('gal_lb_close', 'Close'));
    closeBtn.innerHTML = '<span aria-hidden="true">&#10005;</span>';
    closeBtn.addEventListener('click', close);
    top.appendChild(closeBtn);

    var prev = document.createElement('button');
    prev.type = 'button';
    prev.className = 'lb-nav lb-prev';
    prev.setAttribute('aria-label', tr('gal_lb_prev', 'Previous photo'));
    prev.innerHTML = '<span aria-hidden="true">&#8249;</span>';
    prev.addEventListener('click', function () { go(index - 1); });

    var next = document.createElement('button');
    next.type = 'button';
    next.className = 'lb-nav lb-next';
    next.setAttribute('aria-label', tr('gal_lb_next', 'Next photo'));
    next.innerHTML = '<span aria-hidden="true">&#8250;</span>';
    next.addEventListener('click', function () { go(index + 1); });

    var stage = document.createElement('div');
    stage.className = 'lb-stage';
    imgEl = document.createElement('img');
    imgEl.className = 'lb-img';
    imgEl.setAttribute('alt', '');
    stage.appendChild(imgEl);
    stage.addEventListener('click', function (e) { e.stopPropagation(); });

    stripEl = document.createElement('div');
    stripEl.className = 'lb-strip';

    box.appendChild(top);
    box.appendChild(prev);
    box.appendChild(stage);
    box.appendChild(next);
    box.appendChild(stripEl);
    document.body.appendChild(box);

    box.addEventListener('click', function (e) {
      if (e.target === box) close();
    });
    document.addEventListener('keydown', onKey);
    stage.addEventListener('touchstart', function (e) {
      touchX = e.changedTouches[0].clientX;
    }, { passive: true });
    stage.addEventListener('touchend', function (e) {
      if (touchX === null) return;
      var dx = e.changedTouches[0].clientX - touchX;
      if (Math.abs(dx) > 45) go(index + (dx < 0 ? 1 : -1));
      touchX = null;
    }, { passive: true });
  }

  function buildStrip() {
    stripEl.innerHTML = '';
    for (var i = 0; i < items.length; i++) {
      (function (n) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'lb-thumb';
        b.setAttribute('aria-label', tr('gal_lb_photo', 'Photo') + ' ' + (n + 1));
        var im = document.createElement('img');
        im.src = items[n].small;
        im.alt = '';
        im.loading = 'lazy';
        b.appendChild(im);
        b.addEventListener('click', function () { go(n); });
        stripEl.appendChild(b);
      })(i);
    }
  }

  function preload(n) {
    if (!items[n]) return;
    var im = new Image();
    im.src = items[n].large;
  }

  function go(n) {
    if (!items.length) return;
    index = (n + items.length) % items.length;
    var it = items[index];
    imgEl.src = it.large;
    imgEl.alt = it.alt;
    countEl.textContent = (index + 1) + ' / ' + items.length;
    var thumbs = stripEl.children;
    for (var i = 0; i < thumbs.length; i++) {
      thumbs[i].classList.toggle('on', i === index);
    }
    var active = thumbs[index];
    if (active && active.scrollIntoView) {
      try { active.scrollIntoView({ block: 'nearest', inline: 'center' }); } catch (e) { }
    }
    preload(index + 1);
    preload(index - 1);
  }

  function open(n) {
    build();
    if (!stripEl.children.length) buildStrip();
    lastFocus = document.activeElement;
    box.hidden = false;
    document.body.classList.add('lb-open');
    go(n);
    closeBtn.focus();
  }

  function close() {
    if (!box || box.hidden) return;
    box.hidden = true;
    document.body.classList.remove('lb-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    lastFocus = null;
  }

  function onKey(e) {
    if (!box || box.hidden) return;
    if (e.key === 'Escape') { close(); return; }
    if (e.key === 'ArrowLeft') { go(index - 1); e.preventDefault(); }
    if (e.key === 'ArrowRight') { go(index + 1); e.preventDefault(); }
    if (e.key === 'Home') { go(0); e.preventDefault(); }
    if (e.key === 'End') { go(items.length - 1); e.preventDefault(); }
  }

  function relabel() {
    if (!box) return;
    closeBtn.setAttribute('aria-label', tr('gal_lb_close', 'Close'));
    box.querySelector('.lb-prev').setAttribute('aria-label', tr('gal_lb_prev', 'Previous photo'));
    box.querySelector('.lb-next').setAttribute('aria-label', tr('gal_lb_next', 'Next photo'));
    box.setAttribute('aria-label', tr('gal_lb_title', 'Photo gallery'));
    var thumbs = stripEl.children;
    for (var i = 0; i < thumbs.length; i++) {
      thumbs[i].setAttribute('aria-label', tr('gal_lb_photo', 'Photo') + ' ' + (i + 1));
    }
  }

  function init() {
    var grid = document.querySelector('.gallery');
    if (!grid) return;
    var nodes = grid.querySelectorAll('.g-item');
    for (var i = 0; i < nodes.length; i++) {
      (function (n, el) {
        var img = el.querySelector('img');
        items.push({
          small: img ? img.getAttribute('src') : '',
          large: el.getAttribute('data-full') || (img ? img.getAttribute('src') : ''),
          alt: el.getAttribute('data-alt') || (img ? img.getAttribute('alt') : '')
        });
        el.addEventListener('click', function () { open(n); });
      })(i, nodes[i]);
    }
    document.addEventListener('prl:langchange', relabel);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
