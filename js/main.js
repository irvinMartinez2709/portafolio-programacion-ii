(function () {
  'use strict'

  const header = document.getElementById('header')
  const burger = document.getElementById('burger')
  const mnav = document.getElementById('mnav')
  const navLinks = document.querySelectorAll('.nav a, .mnav a')
  const lb = document.getElementById('lb')
  const lbImg = document.getElementById('lbImg')
  const lbBg = document.getElementById('lbBg')
  const lbClose = document.getElementById('lbClose')
  const curDot = document.getElementById('curDot')
  const curRing = document.getElementById('curRing')

  let profile = {}
  let activities = []
  let certificates = []
  let skillsData = { items: [], chips: [], particleCount: 60 }

  async function loadData() {
    try {
      const [p, a, c, s] = await Promise.all([
        fetch('data/profile.json').then(r => r.json()),
        fetch('data/activities.json').then(r => r.json()),
        fetch('data/certificates.json').then(r => r.json()),
        fetch('data/skills.json').then(r => r.json()),
      ])
      profile = p; activities = a; certificates = c; skillsData = s
    } catch (err) {
      console.warn('Error loading data:', err)
    }
  }

  /* CURSOR */
  document.addEventListener('mousemove', (e) => {
    curDot.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`
    curRing.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`
  })
  document.addEventListener('mouseleave', () => { curDot.style.opacity = '0'; curRing.style.opacity = '0' })
  document.addEventListener('mouseenter', () => { curDot.style.opacity = '1'; curRing.style.opacity = '1' })
  document.querySelectorAll('a, button, .cert-card').forEach(el => {
    el.addEventListener('mouseenter', () => curRing.classList.add('hover'))
    el.addEventListener('mouseleave', () => curRing.classList.remove('hover'))
  })

  /* HEADER SCROLL */
  window.addEventListener('scroll', () => header.classList.toggle('scrolled', window.scrollY > 60))

  /* BURGER */
  burger.addEventListener('click', () => {
    const open = burger.classList.toggle('open')
    mnav.classList.toggle('open')
    burger.setAttribute('aria-expanded', open)
  })
  navLinks.forEach(link => link.addEventListener('click', () => {
    burger.classList.remove('open'); mnav.classList.remove('open')
    burger.setAttribute('aria-expanded', 'false')
  }))

  /* ACTIVE NAV */
  const sections = document.querySelectorAll('section[id]')
  function updateActiveNav() {
    let current = ''
    sections.forEach(s => { if (window.scrollY >= s.offsetTop - 150) current = s.id })
    navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === `#${current}`))
  }
  window.addEventListener('scroll', updateActiveNav)

  /* REVEAL */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); revealObserver.unobserve(e.target) }})
  }, { threshold: 0.15 })
  function observeReveal(parent) { parent.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el)) }

  /* LIGHTBOX */
  function openLightbox(src, alt) {
    if (!src) return
    lbImg.src = src; lbImg.alt = alt || ''
    lb.classList.add('open'); lb.setAttribute('aria-hidden', 'false')
    document.body.style.overflow = 'hidden'
  }
  function closeLightbox() {
    lb.classList.remove('open'); lb.setAttribute('aria-hidden', 'true')
    document.body.style.overflow = ''
  }
  lbBg.addEventListener('click', closeLightbox)
  lbClose.addEventListener('click', closeLightbox)
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox() })

  /* BAR ANIMATION */
  const barObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const pct = parseInt(e.target.dataset.pct)
        const fill = e.target.querySelector('.sbar-fill')
        const num = e.target.querySelector('.sbar-n')
        if (fill) fill.style.width = pct + '%'
        if (num) { let c = 0; const iv = setInterval(() => { c++; num.textContent = c + '%'; if (c >= pct) clearInterval(iv) }, 15) }
        barObserver.unobserve(e.target)
      }
    })
  }, { threshold: 0.3 })

  /* LAVA EFFECT */
  class LavaEffect {
    constructor(canvasId) {
      this.canvas = document.getElementById(canvasId)
      if (!this.canvas) return
      this.ctx = this.canvas.getContext('2d')
      this.particles = []
      this.mouseX = 0.5; this.mouseY = 0.5
      this.container = this.canvas.parentElement
      this.w = 0; this.h = 0
      this.count = skillsData?.particleCount || 60
      this.colors = [
        { r: 57, g: 255, b: 20 }, { r: 0, g: 255, b: 255 },
        { r: 255, g: 0, b: 255 }, { r: 255, g: 106, b: 0 },
      ]
      this.resize()
      window.addEventListener('resize', () => this.resize())
      this.container.addEventListener('mousemove', (e) => {
        const rect = this.container.getBoundingClientRect()
        this.mouseX = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
        this.mouseY = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height))
      })
      this.container.addEventListener('mouseleave', () => { this.mouseX = 0.5; this.mouseY = 0.5 })
      this.animate()
    }
    resize() {
      const rect = this.container.getBoundingClientRect()
      this.w = rect.width; this.h = rect.height
      this.canvas.width = this.w; this.canvas.height = this.h
      this.particles = []
      for (let i = 0; i < this.count; i++) this.particles.push(this.createParticle())
    }
    createParticle() {
      const maxR = Math.min(this.w, this.h) * 0.12
      const minR = Math.min(this.w, this.h) * 0.015
      return {
        x: Math.random() * this.w, y: Math.random() * this.h,
        vx: (Math.random() - 0.5) * 2, vy: (Math.random() - 0.5) * 2,
        r: minR + Math.random() * (maxR - minR),
        s: 0.02 + Math.random() * 0.03, f: 0.90 + Math.random() * 0.06,
        p: Math.random() * Math.PI * 2,
        c: this.colors[Math.floor(Math.random() * this.colors.length)],
      }
    }
    update() {
      const tx = this.mouseX * this.w, ty = this.mouseY * this.h
      for (const p of this.particles) {
        const dx = tx - p.x, dy = ty - p.y, dist = Math.sqrt(dx * dx + dy * dy)
        const force = Math.min(1, dist / 300) * 0.12
        p.vx += dx * force * p.s; p.vy += dy * force * p.s
        p.vx *= p.f; p.vy *= p.f
        const spd = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
        if (spd > 10) { p.vx = (p.vx / spd) * 10; p.vy = (p.vy / spd) * 10 }
        p.x += p.vx; p.y += p.vy
        if (p.x < 0) { p.x = 0; p.vx *= -0.5 } if (p.x > this.w) { p.x = this.w; p.vx *= -0.5 }
        if (p.y < 0) { p.y = 0; p.vy *= -0.5 } if (p.y > this.h) { p.y = this.h; p.vy *= -0.5 }
        p.p += 0.02 + Math.random() * 0.01
      }
    }
    draw() {
      this.ctx.clearRect(0, 0, this.w, this.h)
      for (const p of this.particles) {
        const px = Math.round(p.x), py = Math.round(p.y)
        let col = p.c
        if (px >= 0 && px < this.w && py >= 0 && py < this.h) {
          const pixel = this.ctx.getImageData(px, py, 1, 1).data
          if (pixel[3] !== 0) {
            const inv = { r: 255 - pixel[0], g: 255 - pixel[1], b: 255 - pixel[2] }
            const bright = (inv.r * 299 + inv.g * 587 + inv.b * 114) / 1000
            if (bright >= 60) col = inv
          }
        }
        const pulse = 1 + 0.15 * Math.sin(p.p + performance.now() / 1800)
        const radius = p.r * pulse
        const g = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, radius)
        g.addColorStop(0, `rgba(${col.r},${col.g},${col.b},0.9)`)
        g.addColorStop(0.3, `rgba(${col.r},${col.g},${col.b},0.6)`)
        g.addColorStop(0.7, `rgba(${col.r},${col.g},${col.b},0.25)`)
        g.addColorStop(1, `rgba(${col.r},${col.g},${col.b},0)`)
        this.ctx.beginPath(); this.ctx.arc(p.x, p.y, radius, 0, Math.PI * 2)
        this.ctx.fillStyle = g; this.ctx.fill()
      }
    }
    animate() { this.update(); this.draw(); requestAnimationFrame(() => this.animate()) }
  }

  /* RENDER PROFILE / HERO */
  function renderHero() {
    const p = profile
    if (!p.name) return

    /* head line */
    const hl = document.getElementById('heroHeadline')
    if (hl) {
      const l1 = p.heroTitleL1 || 'PROGRAMACIÓN'
      const l2 = p.heroTitleL2 || 'II'
      hl.innerHTML = `<span class="hh-line">${l1}</span><span class="hh-line hl-glow">${l2}</span>`
    }

    /* sub */
    const sub = document.getElementById('heroSub')
    if (sub) sub.textContent = p.heroSub || `${p.university || 'Universidad Tecnológica de Panamá'}`

    /* desc */
    const desc = document.getElementById('heroDesc')
    if (desc) desc.textContent = p.heroDesc || (p.bio ? p.bio.slice(0, 60) + '...' : 'Portafolio académico del semestre')

    /* tags */
    const tagsEl = document.getElementById('heroTags')
    if (tagsEl) {
      const raw = p.heroTags || [p.faculty?.split(' ')[0] || 'UTP', p.subject, p.year, p.career?.split(' ')[0] || 'Ciberseguridad']
      const items = typeof raw === 'string' ? raw.split(',').map(t => t.trim()) : raw
      tagsEl.innerHTML = items.map(t => `<span class="ht">${t}</span>`).join('')
    }

    /* photo */
    const photo = document.getElementById('heroPhoto')
    if (photo) photo.src = p.photo || 'assets/img/profile/placeholder.jpg'
  }

  /* RENDER ABOUT */
  function renderAbout() {
    const p = profile
    if (!p.name) return
    const bio = document.getElementById('aboutBio')
    if (bio && p.bio) bio.textContent = p.bio
    const uni = document.getElementById('aboutUni')
    if (uni) uni.textContent = p.university || ''
    const subj = document.getElementById('aboutSubject')
    if (subj) subj.textContent = p.subject || ''
    const prof = document.getElementById('aboutProfessor')
    if (prof) prof.textContent = p.professor || ''
    const car = document.getElementById('aboutCareer')
    if (car) car.textContent = p.career || ''
  }

  /* RENDER ACTIVITIES */
  function renderActivities() {
    const grid = document.querySelector('.acts-grid')
    if (!grid) return
    if (!activities.length) {
      grid.innerHTML = '<div class="empty-state"><div class="empty-icon">📂</div><div>No hay actividades aún.</div></div>'
      return
    }
    grid.innerHTML = activities.map((act, i) => {
      const badge = act.status === 'Devuelto' ? 'badge-done' : act.status === 'Entregado' ? 'badge-sent' : 'badge-pend'
      const gd = act.grade != null ? `${act.grade}<small>/100</small>` : '&mdash;<small>/100</small>'
      return `<div class="act-card reveal" style="--di:${i * 0.1}s">
        <div class="act-card-head">
          <span class="act-num">${String(i + 1).padStart(2, '0')}</span>
          <span class="act-badge ${badge}">${act.status || 'Pendiente'}</span>
        </div>
        <div class="act-card-body">
          <div class="act-cover">
            <img src="${act.cover || ''}" alt="${act.title}" onerror="this.classList.add('err')" />
            <div class="act-cover-fb">${act.title}</div>
          </div>
          <h3 class="act-title">${act.title}</h3>
          <div class="act-meta">
            <span>📅 ${act.date || 'Por confirmar'}</span>
            <span>📊 ${gd}</span>
          </div>
          <a href="${act.pdf || '#'}" target="_blank" rel="noopener" class="act-btn">Ver PDF ↗</a>
        </div>
      </div>`
    }).join('')
    observeReveal(grid)
  }

  /* RENDER CERTIFICATES */
  function renderCertificates() {
    const grid = document.querySelector('.certs-grid')
    if (!grid) return
    if (!certificates.length) {
      grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🏆</div><div>No hay certificados aún.</div></div>'
      return
    }
    grid.innerHTML = certificates.map((cert, i) =>
      `<div class="cert-card reveal" style="--di:${i * 0.1}s" data-src="${cert.image || ''}" data-alt="${cert.title}" role="button" tabindex="0">
        <div class="cert-img-wrap">
          <img src="${cert.image || ''}" alt="${cert.title}" onerror="this.classList.add('err')" />
          <div class="cert-img-fb">${cert.title}</div>
          <div class="cert-hover"><span>Ver ↗</span></div>
        </div>
        <div class="cert-body">
          <h3>${cert.title}</h3>
          <p>${cert.description || ''}</p>
        </div>
      </div>`
    ).join('')
    observeReveal(grid)
    grid.querySelectorAll('.cert-card').forEach(el => {
      el.addEventListener('click', () => openLightbox(el.dataset.src, el.dataset.alt))
    })
  }

  /* RENDER SKILLS */
  function renderSkills() {
    if (!skillsData) return
    const barsC = document.querySelector('.sbars')
    if (barsC && skillsData.items) {
      barsC.innerHTML = skillsData.items.map((item, i) =>
        `<div class="sbar reveal" style="--di:${i * 0.08}s" data-pct="${item.percentage}">
          <div class="sbar-hd"><span>${item.name}</span><span class="sbar-n">0%</span></div>
          <div class="sbar-track"><div class="sbar-fill"></div></div>
        </div>`
      ).join('')
      barsC.querySelectorAll('.sbar').forEach(el => barObserver.observe(el))
      observeReveal(barsC)
    }
    const chipsC = document.querySelector('.schips')
    if (chipsC && skillsData.chips) {
      chipsC.innerHTML = skillsData.chips.map((c, i) => `<span class="schip reveal" style="--di:${i * 0.07}s">${c}</span>`).join('')
      observeReveal(chipsC)
    }
  }

  /* RENDER CONTACT */
  function renderContact() {
    const p = profile
    if (!p.name) return
    const intro = document.getElementById('contactIntro')
    if (intro) intro.textContent = `${p.name} — ${p.university || 'UTP'}`
    const email = document.getElementById('cEmail')
    if (email && p.email) { email.href = `mailto:${p.email}`; email.querySelector('.cl-text').textContent = p.email }
    const li = document.getElementById('cLinkedin')
    if (li && p.social?.linkedin) li.href = p.social.linkedin
    const yt = document.getElementById('cYoutube')
    if (yt && p.social?.youtube) yt.href = p.social.youtube
    const gh = document.getElementById('cGithub')
    if (gh && p.social?.github) gh.href = p.social.github
  }

  async function boot() {
    await loadData()
    renderHero()
    renderAbout()
    renderActivities()
    renderCertificates()
    renderSkills()
    renderContact()
    new LavaEffect('lavaCanvas')
    document.querySelectorAll('img').forEach(img => img.addEventListener('error', function () { this.classList.add('err') }))
  }

  boot()
})()
