(function () {
  'use strict';

  const header = document.getElementById('header');
  const burger = document.getElementById('burger');
  const mnav = document.getElementById('mnav');
  const navLinks = document.querySelectorAll('.nav a, .mnav a');
  const lb = document.getElementById('lb');
  const lbImg = document.getElementById('lbImg');
  const lbBg = document.getElementById('lbBg');
  const lbClose = document.getElementById('lbClose');
  const curDot = document.getElementById('curDot');
  const curRing = document.getElementById('curRing');

  let profile = {};
  let activities = [];
  let certificates = [];
  let skillsData = { items: [], chips: [], particleCount: 60 };

  async function loadData() {
    try {
      const [p, a, c, s] = await Promise.all([
        fetch('data/profile.json').then(r => r.json()),
        fetch('data/activities.json').then(r => r.json()),
        fetch('data/certificates.json').then(r => r.json()),
        fetch('data/skills.json').then(r => r.json()),
      ]);
      profile = p; activities = a; certificates = c; skillsData = s;
    } catch (err) {
      console.warn('Error loading data:', err);
    }
  }

  document.addEventListener('mousemove', (e) => {
    curDot.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
    curRing.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
  });
  document.addEventListener('mouseleave', () => { curDot.style.opacity = '0'; curRing.style.opacity = '0'; });
  document.addEventListener('mouseenter', () => { curDot.style.opacity = '1'; curRing.style.opacity = '1'; });
  document.querySelectorAll('a, button, .cert-card').forEach(el => {
    el.addEventListener('mouseenter', () => curRing.classList.add('hover'));
    el.addEventListener('mouseleave', () => curRing.classList.remove('hover'));
  });

  window.addEventListener('scroll', () => header.classList.toggle('scrolled', window.scrollY > 60));

  burger.addEventListener('click', () => {
    const open = burger.classList.toggle('open');
    mnav.classList.toggle('open');
    burger.setAttribute('aria-expanded', open);
  });
  navLinks.forEach(link => link.addEventListener('click', () => {
    burger.classList.remove('open'); mnav.classList.remove('open');
    burger.setAttribute('aria-expanded', 'false');
  }));

  const sections = document.querySelectorAll('section[id]');
  function updateActiveNav() {
    let current = '';
    sections.forEach(s => { if (window.scrollY >= s.offsetTop - 150) current = s.id; });
    navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === `#${current}`));
  }
  window.addEventListener('scroll', updateActiveNav);

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); revealObserver.unobserve(e.target); }});
  }, { threshold: 0.15 });
  function observeReveal(parent) { parent.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el)); }

  function openLightbox(src, alt) {
    if (!src) return;
    lbImg.src = src; lbImg.alt = alt || '';
    lb.classList.add('open'); lb.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }
  function closeLightbox() {
    lb.classList.remove('open'); lb.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }
  lbBg.addEventListener('click', closeLightbox);
  lbClose.addEventListener('click', closeLightbox);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });

  const barObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const pct = parseInt(e.target.dataset.pct);
        const fill = e.target.querySelector('.sbar-fill');
        const num = e.target.querySelector('.sbar-n');
        if (fill) fill.style.width = pct + '%';
        if (num) { let c = 0; const iv = setInterval(() => { c++; num.textContent = c + '%'; if (c >= pct) clearInterval(iv); }, 15); }
        barObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.3 });

  class LavaEffect {
    constructor(canvasId) {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext('2d');
      this.particles = [];
      this.mouseX = 0.5; this.mouseY = 0.5;
      this.container = this.canvas.parentElement;
      this.width = 0; this.height = 0;
      this.particleCount = skillsData?.particleCount || 60;
      this.neonColors = [
        { r: 57, g: 255, b: 20 }, { r: 0, g: 255, b: 255 },
        { r: 255, g: 0, b: 255 }, { r: 255, g: 106, b: 0 },
      ];
      this.resize();
      window.addEventListener('resize', () => this.resize());
      this.container.addEventListener('mousemove', (e) => {
        const rect = this.container.getBoundingClientRect();
        this.mouseX = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
        this.mouseY = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height));
      });
      this.container.addEventListener('mouseleave', () => { this.mouseX = 0.5; this.mouseY = 0.5; });
      this.animate();
    }
    resize() {
      const rect = this.container.getBoundingClientRect();
      this.width = rect.width; this.height = rect.height;
      this.canvas.width = this.width; this.canvas.height = this.height;
      this.particles = [];
      for (let i = 0; i < this.particleCount; i++) this.particles.push(this.createParticle());
    }
    createParticle() {
      const maxR = Math.min(this.width, this.height) * 0.12;
      const minR = Math.min(this.width, this.height) * 0.015;
      return {
        x: Math.random() * this.width, y: Math.random() * this.height,
        vx: (Math.random() - 0.5) * 2, vy: (Math.random() - 0.5) * 2,
        radius: minR + Math.random() * (maxR - minR),
        spring: 0.02 + Math.random() * 0.03, friction: 0.90 + Math.random() * 0.06,
        phase: Math.random() * Math.PI * 2,
        color: this.neonColors[Math.floor(Math.random() * this.neonColors.length)],
      };
    }
    getInvertedColor(x, y) {
      const px = Math.round(x), py = Math.round(y);
      if (px < 0 || px >= this.width || py < 0 || py >= this.height) return null;
      const pixel = this.ctx.getImageData(px, py, 1, 1).data;
      if (pixel[3] === 0) return null;
      const inv = { r: 255 - pixel[0], g: 255 - pixel[1], b: 255 - pixel[2] };
      const bright = (inv.r * 299 + inv.g * 587 + inv.b * 114) / 1000;
      return bright < 60 ? null : inv;
    }
    updateParticles() {
      const tx = this.mouseX * this.width, ty = this.mouseY * this.height;
      for (const p of this.particles) {
        const dx = tx - p.x, dy = ty - p.y, dist = Math.sqrt(dx * dx + dy * dy);
        const force = Math.min(1, dist / 300) * 0.12;
        p.vx += dx * force * p.spring; p.vy += dy * force * p.spring;
        p.vx *= p.friction; p.vy *= p.friction;
        const spd = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
        if (spd > 10) { p.vx = (p.vx / spd) * 10; p.vy = (p.vy / spd) * 10; }
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) { p.x = 0; p.vx *= -0.5; } if (p.x > this.width) { p.x = this.width; p.vx *= -0.5; }
        if (p.y < 0) { p.y = 0; p.vy *= -0.5; } if (p.y > this.height) { p.y = this.height; p.vy *= -0.5; }
        p.phase += 0.02 + Math.random() * 0.01;
      }
    }
    drawParticles() {
      this.ctx.clearRect(0, 0, this.width, this.height);
      for (const p of this.particles) {
        const inv = this.getInvertedColor(p.x, p.y);
        const col = inv || p.color;
        const pulse = 1 + 0.15 * Math.sin(p.phase + performance.now() / 1800);
        const r = p.radius * pulse;
        const g = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r);
        g.addColorStop(0, `rgba(${col.r},${col.g},${col.b},0.9)`);
        g.addColorStop(0.3, `rgba(${col.r},${col.g},${col.b},0.6)`);
        g.addColorStop(0.7, `rgba(${col.r},${col.g},${col.b},0.25)`);
        g.addColorStop(1, `rgba(${col.r},${col.g},${col.b},0)`);
        this.ctx.beginPath(); this.ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        this.ctx.fillStyle = g; this.ctx.fill();
        const hr = r * 0.3;
        this.ctx.beginPath(); this.ctx.arc(p.x - r * 0.15, p.y - r * 0.15, hr, 0, Math.PI * 2);
        this.ctx.fillStyle = 'rgba(255,255,255,0.15)'; this.ctx.fill();
      }
    }
    animate() { this.updateParticles(); this.drawParticles(); requestAnimationFrame(() => this.animate()); }
  }

  function renderProfile() {
    if (!profile.name) return;
    document.title = `${profile.name.split(' ')[0]}.PORTFOLIO — ${profile.subject}`;
    const logo = document.querySelector('.logo');
    if (logo) logo.innerHTML = `${profile.name.split(' ')[0]}<span>.</span>PORTFOLIO`;
    const nameEl = document.querySelector('.h-name');
    if (nameEl) nameEl.textContent = profile.name;
    const tags = document.querySelector('.h-tags');
    if (tags) {
      const items = [profile.faculty?.split(' ')[0] || 'UTP', profile.subject, profile.year, profile.career?.split(' ')[0] || 'Ciberseguridad', 'GitHub Pages'];
      tags.innerHTML = items.map(t => `<span class="htag">${t}</span>`).join('');
    }
    const desc = document.querySelector('.h-desc');
    if (desc && profile.bio) desc.textContent = profile.bio;
    const slbl = document.querySelector('.h-sublbl');
    if (slbl) slbl.textContent = `${profile.subject} — ${profile.university}`.toUpperCase();
    const aboutText = document.querySelector('.about-text');
    if (aboutText && profile.bio) aboutText.textContent = profile.bio;
    const vals = document.querySelectorAll('.ic-val');
    if (vals[0]) vals[0].textContent = profile.university || '';
    if (vals[1]) vals[1].textContent = profile.subject || '';
    if (vals[2]) vals[2].textContent = profile.professor || '';
    if (vals[3]) vals[3].textContent = profile.career || '';
    const contactSub = document.querySelector('.contact-sub');
    if (contactSub) contactSub.textContent = `${profile.name} — ${profile.university} — ${profile.career}`;
    const emailLink = document.querySelector('.cl-email');
    if (emailLink && profile.email) { emailLink.href = `mailto:${profile.email}`; emailLink.querySelector('span:last-child').textContent = profile.email; }
    const liLink = document.querySelector('.cl-li');
    if (liLink && profile.social?.linkedin) liLink.href = profile.social.linkedin;
    const ytLink = document.querySelector('.cl-yt');
    if (ytLink && profile.social?.youtube) ytLink.href = profile.social.youtube;
    const ghLink = document.querySelector('.cl-gh');
    if (ghLink && profile.social?.github) ghLink.href = profile.social.github;
    const photoImg = document.querySelector('.photo-frame img');
    if (photoImg) photoImg.src = profile.photo || 'assets/img/profile/placeholder.jpg';
  }

  function renderActivities() {
    const grid = document.querySelector('.acts-grid');
    if (!grid) return;
    if (!activities.length) {
      grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📂</div><div class="empty-state-text">No hay actividades aún. El administrador las agregará pronto.</div></div>`;
      return;
    }
    grid.innerHTML = activities.map((act, i) => {
      const badgeClass = act.status === 'Devuelto' ? 'rc-done' : act.status === 'Entregado' ? 'rc-sent' : 'rc-pend';
      const gradeClass = act.grade === 100 ? 'perfect' : act.grade != null ? '' : 'pending';
      const gradeD = act.grade != null ? `${act.grade}<small>/100</small>` : '&mdash;<small>/100</small>';
      return `<article class="rcard reveal" style="--di:${i * 0.12}s">
        <div class="rcard-top">
          <div class="rcard-num">${String(i + 1).padStart(2, '0')}</div>
          <span class="rcbadge ${badgeClass}">${act.status || 'Pendiente'}</span>
        </div>
        <div class="rcard-body">
          <div class="rcard-img-wrap">
            <img src="${act.cover || ''}" alt="${act.title}" class="rcard-img" onerror="this.classList.add('error')" />
            <div class="rcard-img-fb">${act.title}</div>
          </div>
          <h3 class="rcard-title">${act.title}</h3>
          <dl class="rcard-meta">
            <div class="rmr"><dt>Fecha</dt><dd>${act.date || 'Por confirmar'}</dd></div>
            <div class="rmr"><dt>Calificación</dt><dd class="rcgrade ${gradeClass}">${gradeD}</dd></div>
          </dl>
          <div class="rcard-btns">
            <a href="${act.pdf || '#'}" target="_blank" rel="noopener" class="rc-btn">Abrir PDF &#8599;</a>
          </div>
        </div>
        <div class="rcard-speed"></div>
      </article>`;
    }).join('');
    observeReveal(grid);
  }

  function renderCertificates() {
    const grid = document.querySelector('.certs-grid');
    if (!grid) return;
    if (!certificates.length) {
      grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🏆</div><div class="empty-state-text">No hay certificados aún.</div></div>`;
      return;
    }
    grid.innerHTML = certificates.map((cert, i) =>
      `<div class="cert-card reveal" style="--di:${i * 0.12}s" data-lb-src="${cert.image || ''}" data-lb-alt="${cert.title}" role="button" tabindex="0">
        <div class="cert-img-wrap">
          <img src="${cert.image || ''}" alt="${cert.title}" class="cert-img" onerror="this.classList.add('error')" />
          <div class="cert-img-fb">${cert.title}</div>
          <div class="cert-hover-layer"><span class="cert-hover-txt">VER CERTIFICADO &#8599;</span></div>
        </div>
        <div class="cert-info"><h3 class="cert-title">${cert.title}</h3><p class="cert-desc">${cert.description || ''}</p></div>
      </div>`
    ).join('');
    observeReveal(grid);
    grid.querySelectorAll('.cert-card').forEach(el => {
      el.addEventListener('click', () => openLightbox(el.dataset.lbSrc, el.dataset.lbAlt));
    });
  }

  function renderSkills() {
    if (!skillsData) return;
    const barsC = document.querySelector('.sbars');
    if (barsC && skillsData.items) {
      barsC.innerHTML = skillsData.items.map((item, i) =>
        `<div class="sbar reveal" style="--di:${i * 0.08}s" data-pct="${item.percentage}">
          <div class="sbar-hd"><span>${item.name}</span><span class="sbar-n">0%</span></div>
          <div class="sbar-track"><div class="sbar-fill"></div></div>
        </div>`
      ).join('');
      barsC.querySelectorAll('.sbar').forEach(el => barObserver.observe(el));
      observeReveal(barsC);
    }
    const chipsC = document.querySelector('.schips');
    if (chipsC && skillsData.chips) {
      chipsC.innerHTML = skillsData.chips.map((c, i) => `<span class="schip reveal" style="--di:${i * 0.07}s">${c}</span>`).join('');
      observeReveal(chipsC);
    }
  }

  async function boot() {
    await loadData();
    renderProfile();
    renderActivities();
    renderCertificates();
    renderSkills();
    new LavaEffect('lavaCanvas');
    document.querySelectorAll('img').forEach(img => img.addEventListener('error', function () { this.classList.add('error'); }));
  }

  boot();
})();
