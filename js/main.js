document.addEventListener('DOMContentLoaded', () => {

  /* ── DATA ── */
  const DATA = {};
  async function loadData() {
    const files = [
      ['profile',   'data/profile.json'],
      ['activities','data/activities.json'],
      ['certificates','data/certificates.json'],
      ['skills',    'data/skills.json'],
    ];
    for (const [key, url] of files) {
      try {
        const r = await fetch(url);
        DATA[key] = await r.json();
      } catch { DATA[key] = {}; }
    }
    // merge localStorage overrides
    for (const key of Object.keys(DATA)) {
      const saved = localStorage.getItem('portfolio_' + key);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) {
            DATA[key] = parsed;
          } else {
            DATA[key] = deepMerge(DATA[key], parsed);
          }
        } catch {}
      }
    }
  }
  function deepMerge(base, override) {
    const result = { ...base };
    for (const k of Object.keys(override)) {
      if (override[k] !== null && override[k] !== undefined && override[k] !== '') {
        if (typeof override[k] === 'object' && !Array.isArray(override[k]) && typeof result[k] === 'object') {
          result[k] = deepMerge(result[k], override[k]);
        } else {
          result[k] = override[k];
        }
      }
    }
    return result;
  }

  /* ── RENDER ── */
  function renderHero() {
    const p = DATA.profile || {};
    document.getElementById('heroHeadline').innerHTML =
      `<span class="hh-line">${p.heroTitleL1 || 'Programación'}</span>` +
      `<span class="hh-line hl-glow">${p.heroTitleL2 || 'II'}</span>`;
    document.getElementById('heroSub').textContent = p.heroSub || 'Universidad Tecnológica de Panamá';
    document.getElementById('heroDesc').textContent = p.heroDesc || 'Portafolio Académico del semestre';
    const photo = document.getElementById('heroPhoto');
    if (p.heroPhoto) photo.src = p.heroPhoto;
  }

  function renderAbout() {
    const p = DATA.profile || {};
    document.getElementById('aboutName').textContent = p.name || 'Irvin Martínez';
    document.getElementById('aboutEmail').textContent = p.email || 'irvin.martinez@utp.ac.pa';
    document.getElementById('aboutCareer').textContent = p.career || 'Ciberseguridad';
    document.getElementById('aboutFaculty').textContent = p.faculty || 'FISC';
    document.getElementById('aboutUni').textContent = p.university || 'UTP Panamá';
    document.getElementById('aboutProfessor').textContent = p.professor || 'Napoleón Ibarra';
    document.getElementById('aboutSubject').textContent = p.subject || 'Programación II';
    document.getElementById('aboutYear').textContent = p.year || '2026';
    document.getElementById('aboutBio').textContent = p.bio || 'Estudiante de Ciberseguridad...';
    const aboutPhoto = document.getElementById('aboutPhoto');
    if (p.heroPhoto) aboutPhoto.src = p.heroPhoto;
  }

  function renderActivities() {
    const grid = document.querySelector('.acts-grid');
    const items = DATA.activities || [];
    if (!items.length) {
      grid.innerHTML = '<p style="color:var(--text2)">No hay actividades registradas.</p>';
      return;
    }
    grid.innerHTML = items.map((a, i) => {
      const name = a.name || a.title || 'Actividad ' + (i+1);
      const statusClass = (a.status || 'pendiente').toLowerCase();
      const statusLabel = { entregado: 'Entregado', devuelto: 'Devuelto', pendiente: 'Pendiente' }[statusClass] || a.status || 'Pendiente';
      const coverSrc = a.cover || a.image || '';
      const imgTag = coverSrc ? `<img class="act-cover" src="${coverSrc}" alt="${name}" data-lb="${coverSrc}" />` : '';
      const score = a.score || a.puntaje || a.grade || '—';
      const btnHref = a.url || a.link || a.pdf || '#';
      return `<div class="act-card glass">
        ${imgTag}
        <h3>${name}</h3>
        <div class="act-meta">
          <span>📅 ${a.date || '—'}</span>
          <span>⭐ ${score}</span>
          <span class="act-status ${statusClass}">● ${statusLabel}</span>
        </div>
        <a href="${btnHref}" target="_blank" rel="noopener" class="act-btn">Ver actividad</a>
      </div>`;
    }).join('');
  }

  function renderCertificates() {
    const grid = document.querySelector('.certs-grid');
    const items = DATA.certificates || [];
    if (!items.length) {
      grid.innerHTML = '<p style="color:var(--text2)">No hay certificados.</p>';
      return;
    }
    grid.innerHTML = items.map(c => {
      const name = c.name || c.title || 'Certificado';
      const org = c.organization || c.org || c.description || '';
      const imgSrc = c.image || c.img || '';
      const imgTag = imgSrc ? `<img class="cert-img" src="${imgSrc}" alt="${name}" data-lb="${imgSrc}" />` : '';
      return `<div class="cert-card glass">
        <h3>${name}</h3>
        <div class="cert-org">${org}</div>
        ${imgTag}
      </div>`;
    }).join('');
  }

  function renderSkills() {
    const data = DATA.skills || {};
    const bars = data.bars || data.items || [];
    const chips = data.chips || [];

    // chips
    const chipsEl = document.querySelector('.schips');
    if (chips.length) {
      chipsEl.innerHTML = chips.map(c => `<span class="chip glass">${c}</span>`).join('');
    } else {
      chipsEl.innerHTML = '';
    }

    // bars
    const barsEl = document.querySelector('.sbars');
    if (bars.length) {
      barsEl.innerHTML = bars.map(b => {
        const pct = b.level || b.percentage || b.percent || 0;
        return `<div class="sbar-item">
        <div class="sbar-label"><span>${b.name || ''}</span><span>${pct}%</span></div>
        <div class="sbar-track"><div class="sbar-fill" data-pct="${pct}"></div></div>
      </div>`;
      }).join('');
      // animate bars
      requestAnimationFrame(() => {
        document.querySelectorAll('.sbar-fill').forEach(el => {
          el.style.width = el.dataset.pct + '%';
        });
      });
    } else {
      barsEl.innerHTML = '';
    }
  }

  function renderContact() {
    const p = DATA.profile || {};
    const emailEl = document.getElementById('cEmail');
    const linkedinEl = document.getElementById('cLinkedin');
    const githubEl = document.getElementById('cGithub');
    const introEl = document.getElementById('contactIntro');

    const email = p.email || (p.social && p.social.email) || '';
    const linkedin = p.linkedin || (p.social && p.social.linkedin) || '';
    const github = p.github || (p.social && p.social.github) || '';
    const name = p.name || '';

    if (email) {
      emailEl.href = 'mailto:' + email;
      emailEl.querySelector('.cl-text').textContent = email;
    }
    if (linkedin) {
      linkedinEl.href = linkedin.startsWith('http') ? linkedin : 'https://' + linkedin;
    }
    if (github) {
      githubEl.href = github.startsWith('http') ? github : 'https://' + github;
    }
    if (name) {
      introEl.textContent = `${name} — ${p.university || 'UTP Panamá'}`;
    }
  }

  function renderAll() {
    renderHero();
    renderAbout();
    renderActivities();
    renderCertificates();
    renderSkills();
    renderContact();
    initLightbox();
    initReveal();
  }

  /* ── THEME TOGGLE ── */
  const themeBtn = document.getElementById('themeBtn');
  const themeBtnMobile = document.getElementById('themeBtnMobile');
  const html = document.documentElement;

  function getTheme() { return localStorage.getItem('theme') || 'dark'; }
  function setTheme(t) {
    html.dataset.theme = t;
    localStorage.setItem('theme', t);
    const icon = t === 'dark' ? '🌙' : '☀️';
    themeBtn.textContent = icon;
    if (themeBtnMobile) {
      themeBtnMobile.textContent = t === 'dark' ? '☀️ Modo claro' : '🌙 Modo oscuro';
    }
  }
  setTheme(getTheme());
  themeBtn.addEventListener('click', () => {
    setTheme(html.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  if (themeBtnMobile) {
    themeBtnMobile.addEventListener('click', () => {
      setTheme(html.dataset.theme === 'dark' ? 'light' : 'dark');
    });
  }

  /* ── MOBILE MENU ── */
  const burger = document.getElementById('burger');
  const mnav = document.getElementById('mnav');
  burger.addEventListener('click', () => {
    const open = burger.classList.toggle('open');
    mnav.classList.toggle('open');
    burger.setAttribute('aria-expanded', open);
    mnav.setAttribute('aria-hidden', !open);
  });
  mnav.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      burger.classList.remove('open');
      mnav.classList.remove('open');
      mnav.setAttribute('aria-hidden', 'true');
    });
  });

  /* ── LIGHTBOX ── */
  function initLightbox() {
    const lb = document.getElementById('lb');
    const lbImg = document.getElementById('lbImg');
    const lbBg = document.getElementById('lbBg');
    const lbClose = document.getElementById('lbClose');

    document.querySelectorAll('[data-lb]').forEach(el => {
      el.addEventListener('click', e => {
        e.stopPropagation();
        lbImg.src = el.dataset.lb;
        lbImg.alt = el.alt || '';
        lb.classList.add('open');
        lb.setAttribute('aria-hidden', 'false');
      });
    });

    function closeLb() {
      lb.classList.remove('open');
      lb.setAttribute('aria-hidden', 'true');
    }
    lbClose.addEventListener('click', closeLb);
    lbBg.addEventListener('click', closeLb);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLb(); });
  }

  /* ── REVEAL ON SCROLL ── */
  function initReveal() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.15 });
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
  }

  /* ── CURSOR ── */
  const dot = document.getElementById('curDot');
  const ring = document.getElementById('curRing');
  document.addEventListener('mousemove', e => {
    dot.style.left = e.clientX + 'px';
    dot.style.top = e.clientY + 'px';
    ring.style.left = e.clientX + 'px';
    ring.style.top = e.clientY + 'px';
  });
  document.querySelectorAll('a, button, .act-card, .cert-card, .chip, .lb-img, .act-cover, .cert-img').forEach(el => {
    el.addEventListener('mouseenter', () => { dot.classList.add('hover'); ring.classList.add('hover'); });
    el.addEventListener('mouseleave', () => { dot.classList.remove('hover'); ring.classList.remove('hover'); });
  });

  /* ── LAVA LAMP CANVAS ── */
  const canvas = document.getElementById('lavaCanvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let w, h, t = 0;
    function resize() { w = canvas.width = canvas.parentElement.offsetWidth; h = canvas.height = canvas.parentElement.offsetHeight; }
    resize();
    window.addEventListener('resize', resize);
    function draw() {
      t += 0.0025;
      ctx.clearRect(0, 0, w, h);
      const grd = ctx.createRadialGradient(w*0.5+Math.sin(t)*80, h*0.5+Math.cos(t*0.7)*60, 10, w*0.5, h*0.5, 400);
      const alpha = html.dataset.theme === 'light' ? 0.04 : 0.06;
      grd.addColorStop(0, `rgba(108,57,255,${alpha*2})`);
      grd.addColorStop(0.4, `rgba(0,229,160,${alpha})`);
      grd.addColorStop(1, 'transparent');
      ctx.fillStyle = grd;
      ctx.fillRect(0, 0, w, h);
      const grd2 = ctx.createRadialGradient(w*0.3+Math.cos(t*0.5)*100, h*0.7+Math.sin(t*0.8)*80, 10, w*0.3, h*0.7, 300);
      grd2.addColorStop(0, `rgba(255,60,140,${alpha})`);
      grd2.addColorStop(1, 'transparent');
      ctx.fillStyle = grd2;
      ctx.fillRect(0, 0, w, h);
      requestAnimationFrame(draw);
    }
    draw();
  }

  /* ── NAV ACTIVE ── */
  const navLinks = document.querySelectorAll('.nl, .mnl');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const id = e.target.id;
        navLinks.forEach(l => {
          l.classList.toggle('active', l.getAttribute('href') === '#' + id);
        });
      }
    });
  }, { threshold: 0.3 });
  document.querySelectorAll('section[id]').forEach(s => observer.observe(s));

  /* ── BOOT ── */
  loadData().then(() => {
    renderAll();
  });

});
