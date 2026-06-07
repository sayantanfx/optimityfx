/* ============================================================
   OptimityFX — Interactions
   ============================================================ */
(function () {
  'use strict';

  /* ---- Navbar scroll state + progress bar ---- */
  const nav = document.querySelector('.nav');
  const progress = document.querySelector('.progress');
  const onScroll = () => {
    if (nav) nav.classList.toggle('scrolled', window.scrollY > 20);
    if (progress) {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      progress.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
    }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- Mobile menu ---- */
  const burger = document.querySelector('.burger');
  if (burger) {
    burger.addEventListener('click', () => document.body.classList.toggle('menu-open'));
    document.querySelectorAll('.m-drawer a').forEach(a =>
      a.addEventListener('click', () => document.body.classList.remove('menu-open')));
  }

  /* ---- Scroll reveal ---- */
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && reveals.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(el => io.observe(el));
  } else {
    reveals.forEach(el => el.classList.add('in'));
  }

  /* ---- Animated counters ---- */
  const counters = document.querySelectorAll('[data-count]');
  if ('IntersectionObserver' in window && counters.length) {
    const cio = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        const el = e.target;
        const target = parseFloat(el.dataset.count);
        const suffix = el.dataset.suffix || '';
        const dur = 1500; const start = performance.now();
        const dec = (target % 1 !== 0) ? 1 : 0;
        const tick = (now) => {
          const p = Math.min((now - start) / dur, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          el.textContent = (target * eased).toFixed(dec) + suffix;
          if (p < 1) requestAnimationFrame(tick); else el.textContent = target.toFixed(dec) + suffix;
        };
        requestAnimationFrame(tick);
        cio.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach(c => cio.observe(c));
  }

  /* ---- Portfolio filters ---- */
  const filterBtns = document.querySelectorAll('.filter-btn');
  if (filterBtns.length) {
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const f = btn.dataset.filter;
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('[data-cat]').forEach(item => {
          const show = f === 'all' || item.dataset.cat.includes(f);
          item.style.display = show ? '' : 'none';
        });
      });
    });
  }

  /* ---- Before / After sliders ---- */
  document.querySelectorAll('.ba').forEach(ba => {
    const after = ba.querySelector('.after');
    const handle = ba.querySelector('.handle');
    const range = ba.querySelector('input[type=range]');
    const set = (v) => {
      after.style.clipPath = `inset(0 0 0 ${v}%)`;
      handle.style.left = v + '%';
    };
    if (range) { range.addEventListener('input', () => set(range.value)); set(range.value || 50); }
  });

  /* ---- Video poster -> iframe ---- */
  document.querySelectorAll('.video-poster').forEach(poster => {
    poster.addEventListener('click', () => {
      const src = poster.dataset.src;
      if (!src) return;
      const frame = poster.closest('.video-frame');
      const ratio = frame.querySelector('.ratio');
      const iframe = document.createElement('iframe');
      iframe.src = src + (src.includes('?') ? '&' : '?') + 'autoplay=1';
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      iframe.loading = 'lazy';
      ratio.appendChild(iframe);
      poster.remove();
    });
  });

  /* ---- Accordion (FAQ) ---- */
  document.querySelectorAll('.acc-q').forEach(q => {
    q.addEventListener('click', () => {
      const item = q.closest('.acc-item');
      const ans = item.querySelector('.acc-a');
      const isOpen = item.classList.contains('open');
      item.classList.toggle('open');
      ans.style.maxHeight = isOpen ? null : ans.scrollHeight + 'px';
    });
  });

  /* ---- Lightbox gallery (images + video) ---- */
  const lb = document.querySelector('.lightbox');
  if (lb) {
    const stage = lb.querySelector('.lb-stage') || lb.querySelector('img');
    // Build an ordered list of clickable gallery items.
    // An item can be: a .tile carrying data-full (image) or data-video (embed),
    // or any standalone element with [data-lightbox]/[data-full]/[data-video].
    const nodes = Array.from(document.querySelectorAll(
      '.tile[data-full], .tile[data-video], [data-lightbox], [data-full]:not(.tile), [data-video]:not(.tile)'
    ));
    const items = nodes.map(n => ({
      video: n.dataset.video || null,
      src: n.dataset.full || n.dataset.lightbox || (n.tagName === 'IMG' ? n.src : (n.querySelector('img') ? n.querySelector('img').src : '')),
      node: n
    })).filter(it => it.video || it.src);

    let idx = 0;
    const render = () => {
      const it = items[idx];
      if (it.video) {
        const sep = it.video.includes('?') ? '&' : '?';
        lb.querySelector('.lb-frame').innerHTML =
          '<iframe src="' + it.video + sep + 'autoplay=1" allow="autoplay; fullscreen; encrypted-media; picture-in-picture" allowfullscreen loading="lazy"></iframe>';
        lb.classList.add('is-video');
      } else {
        lb.querySelector('.lb-frame').innerHTML = '<img src="' + it.src + '" alt="Gallery image">';
        lb.classList.remove('is-video');
      }
    };
    const open = (i) => { idx = (i + items.length) % items.length; lb.classList.add('open'); document.body.style.overflow = 'hidden'; render(); };
    const close = () => { lb.classList.remove('open'); lb.querySelector('.lb-frame').innerHTML = ''; document.body.style.overflow = ''; };
    const go = (d) => { idx = (idx + d + items.length) % items.length; render(); };

    items.forEach((it, i) => {
      it.node.style.cursor = 'pointer';
      it.node.addEventListener('click', (e) => { e.preventDefault(); open(i); });
    });
    lb.querySelector('.lb-close').addEventListener('click', close);
    lb.querySelector('.lb-next').addEventListener('click', () => go(1));
    lb.querySelector('.lb-prev').addEventListener('click', () => go(-1));
    lb.addEventListener('click', (e) => { if (e.target === lb || e.target.classList.contains('lb-frame')) close(); });
    document.addEventListener('keydown', (e) => {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowRight') go(1);
      if (e.key === 'ArrowLeft') go(-1);
    });
  }

  /* ---- Contact / form fake submit ---- */
  document.querySelectorAll('form[data-fake]').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = form.querySelector('[type=submit]');
      const orig = btn.textContent;
      btn.textContent = 'Sending…'; btn.disabled = true;
      setTimeout(() => {
        btn.textContent = '✓ Message Sent';
        form.reset();
        setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 2600);
      }, 1000);
    });
  });

  /* ---- Year ---- */
  document.querySelectorAll('[data-year]').forEach(el => el.textContent = new Date().getFullYear());
})();

/* ---- Mouse-tracking glow ---- */
(function () {
  const glow = document.createElement('div');
  glow.id = 'mouse-glow';
  glow.setAttribute('aria-hidden', 'true');
  document.body.appendChild(glow);

  let raf, mx = 50, my = 50;
  const render = () => {
    glow.style.background =
      `radial-gradient(820px circle at ${mx}% ${my}%, rgba(0,212,255,0.065), rgba(0,212,255,0.018) 35%, transparent 60%)`;
  };

  document.addEventListener('mousemove', (e) => {
    mx = (e.clientX / window.innerWidth)  * 100;
    my = (e.clientY / window.innerHeight) * 100;
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(render);
  }, { passive: true });

  // Initial soft glow at center-top
  render();
})();
