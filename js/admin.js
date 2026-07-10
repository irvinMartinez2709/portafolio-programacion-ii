(function () {
  'use strict'

  let credentials = { username: 'Sarita', password: '_2709_' }
  let data = {
    profile: {},
    activities: [],
    certificates: [],
    skills: { bars: [], chips: [], particleCount: 60 }
  }
  let editingIndex = null
  let editingType = null

  const loginScreen = document.getElementById('loginScreen')
  const dashScreen = document.getElementById('dashboardScreen')
  const loginForm = document.getElementById('loginForm')
  const loginUser = document.getElementById('loginUser')
  const loginPass = document.getElementById('loginPass')
  const loginError = document.getElementById('loginError')
  const logoutBtn = document.getElementById('logoutBtn')
  const dashUser = document.getElementById('dashUser')

  async function loadCredentials() {
    try {
      const saved = localStorage.getItem('admin_credentials')
      if (saved) { credentials = JSON.parse(saved); return }
    } catch(e) {}
    try {
      const r = await fetch('data/credentials.json')
      credentials = await r.json()
    } catch (e) {}
  }

  async function loadAllData() {
    try {
      const [p, a, c, s] = await Promise.all([
        fetch('data/profile.json').then(r => r.json()),
        fetch('data/activities.json').then(r => r.json()),
        fetch('data/certificates.json').then(r => r.json()),
        fetch('data/skills.json').then(r => r.json()),
      ])
      return { profile: p, activities: a, certificates: c, skills: s }
    } catch (err) {
      console.warn('Error loading data:', err)
      return null
    }
  }

  function deepMerge(target, source) {
    const result = { ...target }
    for (const key of Object.keys(source)) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(result[key] || {}, source[key])
      } else {
        if (result[key] === undefined || result[key] === null || result[key] === '') {
          result[key] = source[key]
        }
      }
    }
    return result
  }

  loginForm.addEventListener('submit', (e) => {
    e.preventDefault()
    const user = loginUser.value.trim()
    const pass = loginPass.value
    if (user === credentials.username && pass === credentials.password) {
      loginScreen.style.display = 'none'
      dashScreen.style.display = 'block'
      dashUser.textContent = credentials.username
      loginError.style.display = 'none'
      populateAll()
    } else {
      loginError.style.display = 'block'
    }
  })

  logoutBtn.addEventListener('click', () => {
    dashScreen.style.display = 'none'
    loginScreen.style.display = 'flex'
    loginForm.reset()
  })

  document.querySelectorAll('.admin-snav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.admin-snav-item').forEach(b => b.classList.remove('active'))
      document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'))
      btn.classList.add('active')
      const sec = document.getElementById('sec-' + btn.dataset.section)
      if (sec) sec.classList.add('active')
    })
  })

  function populateAll() {
    populateInicioForm()
    populateAboutForm()
    populateProfileForm()
    populateContactForm()
    populateActivitiesList()
    populateCertificatesList()
    populateSkillsList()
    populateChipsList()
    populateParticleCount()
  }

  function populateInicioForm() {
    const p = data.profile
    document.getElementById('heroTitleL1').value = p.heroTitleL1 || ''
    document.getElementById('heroTitleL2').value = p.heroTitleL2 || ''
    document.getElementById('heroSub').value = p.heroSub || ''
    document.getElementById('heroDesc').value = p.heroDesc || ''
  }

  function populateAboutForm() {
    document.getElementById('aboutBio').value = data.profile.bio || ''
  }

  function populateProfileForm() {
    const p = data.profile
    document.getElementById('profName').value = p.name || ''
    document.getElementById('profEmail').value = p.email || ''
    document.getElementById('profCareer').value = p.career || ''
    document.getElementById('profFaculty').value = p.faculty || ''
    document.getElementById('profUni').value = p.university || ''
    document.getElementById('profProfessor').value = p.professor || ''
    document.getElementById('profSubject').value = p.subject || ''
    document.getElementById('profYear').value = p.year || ''
    document.getElementById('profPhoto').value = p.heroPhoto || ''
  }

  function populateContactForm() {
    const p = data.profile
    document.getElementById('contEmail').value = p.email || ''
    document.getElementById('contLinkedin').value = p.linkedin || ''
    document.getElementById('contGithub').value = p.github || ''
  }

  function cancelEdit(type) {
    editingIndex = null; editingType = null
    const map = { act: 'Actividad', cert: 'Certificado', skill: 'Habilidad', chip: 'Chip' }
    document.getElementById(type + 'Form').reset()
    document.getElementById(type + 'SubmitBtn').textContent = 'Añadir ' + map[type]
    document.getElementById(type + 'CancelBtn').style.display = 'none'
  }

  function populateActivitiesList() {
    const c = document.getElementById('activitiesList')
    if (!data.activities.length) { c.innerHTML = '<p style="color:var(--text2);font-size:13px;">No hay actividades.</p>'; return }
    c.innerHTML = data.activities.map((a, i) =>
      `<div class="admin-list-item"><span>#${i+1} <strong>${a.name || a.title || 'Actividad'}</strong> (${a.status || 'pendiente'})</span>
        <button onclick="adminEditActivity(${i})">Editar</button>
        <button onclick="adminRemoveActivity(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateCertificatesList() {
    const c = document.getElementById('certificatesList')
    if (!data.certificates.length) { c.innerHTML = '<p style="color:var(--text2);font-size:13px;">No hay certificados.</p>'; return }
    c.innerHTML = data.certificates.map((cert, i) =>
      `<div class="admin-list-item"><span>#${i+1} <strong>${cert.name || cert.title || 'Certificado'}</strong></span>
        <button onclick="adminEditCertificate(${i})">Editar</button>
        <button onclick="adminRemoveCertificate(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateSkillsList() {
    const c = document.getElementById('skillsList')
    const items = data.skills.bars || []
    if (!items.length) { c.innerHTML = '<p style="color:var(--text2);font-size:13px;">No hay habilidades.</p>'; return }
    c.innerHTML = items.map((item, i) =>
      `<div class="admin-list-item"><span><strong>${item.name}</strong> — ${item.level}%</span>
        <button onclick="adminEditSkill(${i})">Editar</button>
        <button onclick="adminRemoveSkill(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateChipsList() {
    const c = document.getElementById('chipsList')
    const items = data.skills.chips || []
    if (!items.length) { c.innerHTML = '<p style="color:var(--text2);font-size:13px;">No hay chips.</p>'; return }
    c.innerHTML = items.map((chip, i) =>
      `<div class="admin-list-item"><span><strong>${chip}</strong></span>
        <button onclick="adminEditChip(${i})">Editar</button>
        <button onclick="adminRemoveChip(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateParticleCount() {
    const el = document.getElementById('currentLavaState')
    const enabled = data.skills.lavaEnabled !== false
    if (el) el.textContent = enabled ? 'Activo' : 'Desactivado'
    document.getElementById('lavaEnabled').value = enabled ? 'true' : 'false'
    document.getElementById('lavaSpeed').value = data.skills.lavaSpeed || 1
  }

  function saveAll() {
    localStorage.setItem('admin_data', JSON.stringify(data))
    localStorage.setItem('admin_credentials', JSON.stringify(credentials))
    // Also save to portfolio_ prefixed keys so main.js picks up changes
    localStorage.setItem('portfolio_profile', JSON.stringify(data.profile))
    localStorage.setItem('portfolio_activities', JSON.stringify(data.activities))
    localStorage.setItem('portfolio_certificates', JSON.stringify(data.certificates))
    localStorage.setItem('portfolio_skills', JSON.stringify(data.skills))
  }

  async function commitToGitHub() {
    const token = localStorage.getItem('gh_token')
    if (!token) {
      alert('\u26a0\ufe0f No hay token de GitHub.\n\nLos cambios est\u00e1n guardados LOCALMENTE.\n\nPara subirlos:\n1. Crea un token en GitHub > Settings > Developer Settings > Personal Access Tokens > Fine-grained tokens\n2. Permiso: "contents: write" para tu repo\n3. En consola del navegador (F12):\n   localStorage.setItem("gh_token", "TU_TOKEN")\n4. Vuelve a hacer clic en "Subir a GitHub"')
      return
    }
    const owner = 'irvinMartinez2709'
    const repo = 'portafolio-programacion-ii'
    const headers = { 'Authorization': `Bearer ${token}`, 'Accept': 'application/vnd.github.v3+json' }
    const j = (r) => r.json()
    try {
      const refUrl = `https://api.github.com/repos/${owner}/${repo}/git/refs/heads/main`
      const refRes = await fetch(refUrl, { headers })
      if (!refRes.ok) throw new Error(`Error al obtener rama (${refRes.status})`)
      const latestSha = (await j(refRes)).object.sha

      const commitRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/commits/${latestSha}`, { headers })
      const baseTreeSha = (await j(commitRes)).tree.sha

      const files = {
        'data/activities.json': JSON.stringify(data.activities, null, 2),
        'data/certificates.json': JSON.stringify(data.certificates, null, 2),
        'data/profile.json': JSON.stringify(data.profile, null, 2),
        'data/skills.json': JSON.stringify(data.skills, null, 2),
        'data/credentials.json': JSON.stringify(credentials, null, 2),
      }

      const treeItems = []
      for (const [path, content] of Object.entries(files)) {
        const blobRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/blobs`, {
          method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ content, encoding: 'utf-8' })
        })
        if (!blobRes.ok) throw new Error(`Error al crear blob para ${path}`)
        treeItems.push({ path, mode: '100644', type: 'blob', sha: (await j(blobRes)).sha })
      }

      const treeRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/trees`, {
        method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems })
      })
      if (!treeRes.ok) throw new Error('Error al crear tree')
      const newTreeSha = (await j(treeRes)).sha

      const commitRes2 = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/commits`, {
        method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'admin: actualizar portafolio', tree: newTreeSha, parents: [latestSha] })
      })
      if (!commitRes2.ok) throw new Error('Error al crear commit')
      const newCommitSha = (await j(commitRes2)).sha

      const updRes = await fetch(refUrl, {
        method: 'PATCH', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ sha: newCommitSha, force: false })
      })
      if (!updRes.ok) throw new Error('Error al actualizar rama')

      alert('\u2705 Cambios subidos a GitHub. La p\u00e1gina se actualizar\u00e1 en ~1-2 min.')
    } catch (e) {
      alert('\u26a0\ufe0f Error: ' + e.message + '\n\nVerifica que el token tenga permisos "contents: write" para el repo.')
    }
  }

  /* ── FORM HANDLERS ── */

  document.getElementById('inicioForm').addEventListener('submit', (e) => {
    e.preventDefault()
    data.profile.heroTitleL1 = document.getElementById('heroTitleL1').value
    data.profile.heroTitleL2 = document.getElementById('heroTitleL2').value
    data.profile.heroSub = document.getElementById('heroSub').value
    data.profile.heroDesc = document.getElementById('heroDesc').value
    saveAll()
    alert('\u2705 Inicio guardado.')
  })

  document.getElementById('aboutForm').addEventListener('submit', (e) => {
    e.preventDefault()
    data.profile.bio = document.getElementById('aboutBio').value
    saveAll()
    alert('\u2705 Sobre m\u00ed guardado.')
  })

  document.getElementById('profileForm').addEventListener('submit', (e) => {
    e.preventDefault()
    data.profile.name = document.getElementById('profName').value
    data.profile.email = document.getElementById('profEmail').value
    data.profile.career = document.getElementById('profCareer').value
    data.profile.faculty = document.getElementById('profFaculty').value
    data.profile.university = document.getElementById('profUni').value
    data.profile.professor = document.getElementById('profProfessor').value
    data.profile.subject = document.getElementById('profSubject').value
    data.profile.year = document.getElementById('profYear').value
    data.profile.heroPhoto = document.getElementById('profPhoto').value
    saveAll()
    alert('\u2705 Perfil guardado.')
  })

  document.getElementById('contactForm').addEventListener('submit', (e) => {
    e.preventDefault()
    data.profile.email = document.getElementById('contEmail').value
    data.profile.linkedin = document.getElementById('contLinkedin').value
    data.profile.github = document.getElementById('contGithub').value
    saveAll()
    alert('\u2705 Contacto guardado.')
  })

  document.getElementById('activityForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const act = {
      name: document.getElementById('actName').value,
      date: document.getElementById('actDate').value,
      score: document.getElementById('actScore').value,
      status: document.getElementById('actStatus').value,
      cover: document.getElementById('actCover').value,
      url: document.getElementById('actUrl').value,
    }
    if (editingIndex !== null && editingType === 'act') {
      data.activities[editingIndex] = act
      editingIndex = null; editingType = null
      document.getElementById('actSubmitBtn').textContent = 'Añadir Actividad'
      document.getElementById('actCancelBtn').style.display = 'none'
    } else {
      data.activities.push(act)
    }
    populateActivitiesList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('certForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const cert = {
      name: document.getElementById('certName').value,
      organization: document.getElementById('certOrg').value,
      image: document.getElementById('certImage').value,
    }
    if (editingIndex !== null && editingType === 'cert') {
      data.certificates[editingIndex] = cert
      editingIndex = null; editingType = null
      document.getElementById('certSubmitBtn').textContent = 'Añadir Certificado'
      document.getElementById('certCancelBtn').style.display = 'none'
    } else {
      data.certificates.push(cert)
    }
    populateCertificatesList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('skillForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const skill = {
      name: document.getElementById('skillName').value,
      level: parseInt(document.getElementById('skillLevel').value) || 0,
    }
    if (!data.skills.bars) data.skills.bars = []
    if (editingIndex !== null && editingType === 'skill') {
      data.skills.bars[editingIndex] = skill
      editingIndex = null; editingType = null
      document.getElementById('skillSubmitBtn').textContent = 'Añadir Habilidad'
      document.getElementById('skillCancelBtn').style.display = 'none'
    } else {
      data.skills.bars.push(skill)
    }
    populateSkillsList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('chipForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const chip = document.getElementById('chipName').value
    if (!data.skills.chips) data.skills.chips = []
    if (editingIndex !== null && editingType === 'chip') {
      data.skills.chips[editingIndex] = chip
      editingIndex = null; editingType = null
      document.getElementById('chipSubmitBtn').textContent = 'Añadir Chip'
      document.getElementById('chipCancelBtn').style.display = 'none'
    } else {
      data.skills.chips.push(chip)
    }
    populateChipsList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('particleForm').addEventListener('submit', (e) => {
    e.preventDefault()
    data.skills.lavaEnabled = document.getElementById('lavaEnabled').value === 'true'
    data.skills.lavaSpeed = parseFloat(document.getElementById('lavaSpeed').value) || 1
    populateParticleCount()
    saveAll()
  })

  document.getElementById('credForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const newUser = document.getElementById('newUser').value.trim()
    const newPass = document.getElementById('newPass').value
    const confirmPass = document.getElementById('confirmPass').value
    document.getElementById('credError').style.display = 'none'
    document.getElementById('credSuccess').style.display = 'none'
    if (newPass !== confirmPass) {
      document.getElementById('credError').style.display = 'block'
      return
    }
    credentials = { username: newUser, password: newPass }
    dashUser.textContent = newUser
    document.getElementById('credSuccess').style.display = 'block'
    document.getElementById('newUser').value = ''
    document.getElementById('newPass').value = ''
    document.getElementById('confirmPass').value = ''
    saveAll()
  })

  /* ── EDITAR ── */
  window.adminEditActivity = function(idx) {
    editingIndex = idx; editingType = 'act'
    const a = data.activities[idx]
    document.getElementById('actName').value = a.name || a.title || ''
    document.getElementById('actDate').value = a.date || ''
    document.getElementById('actScore').value = a.score || a.grade || ''
    document.getElementById('actStatus').value = a.status || 'pendiente'
    document.getElementById('actCover').value = a.cover || a.image || ''
    document.getElementById('actUrl').value = a.url || a.link || a.pdf || ''
    document.getElementById('actSubmitBtn').textContent = 'Actualizar Actividad'
    document.getElementById('actCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="activities"]').click()
  }
  window.adminEditCertificate = function(idx) {
    editingIndex = idx; editingType = 'cert'
    const c = data.certificates[idx]
    document.getElementById('certName').value = c.name || c.title || ''
    document.getElementById('certOrg').value = c.organization || c.org || c.description || ''
    document.getElementById('certImage').value = c.image || c.img || ''
    document.getElementById('certSubmitBtn').textContent = 'Actualizar Certificado'
    document.getElementById('certCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="certificates"]').click()
  }
  window.adminEditSkill = function(idx) {
    editingIndex = idx; editingType = 'skill'
    const s = (data.skills.bars || [])[idx]
    document.getElementById('skillName').value = s.name || ''
    document.getElementById('skillLevel').value = s.level || s.percentage || ''
    document.getElementById('skillSubmitBtn').textContent = 'Actualizar Habilidad'
    document.getElementById('skillCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="skills"]').click()
  }
  window.adminEditChip = function(idx) {
    editingIndex = idx; editingType = 'chip'
    document.getElementById('chipName').value = (data.skills.chips || [])[idx] || ''
    document.getElementById('chipSubmitBtn').textContent = 'Actualizar Chip'
    document.getElementById('chipCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="skills"]').click()
  }

  document.getElementById('actCancelBtn').addEventListener('click', () => cancelEdit('act'))
  document.getElementById('certCancelBtn').addEventListener('click', () => cancelEdit('cert'))
  document.getElementById('skillCancelBtn').addEventListener('click', () => cancelEdit('skill'))
  document.getElementById('chipCancelBtn').addEventListener('click', () => cancelEdit('chip'))

  /* ── ELIMINAR ── */
  window.adminRemoveActivity = function(idx) {
    if (!confirm('¿Eliminar esta actividad?')) return
    data.activities.splice(idx, 1)
    populateActivitiesList()
    saveAll()
  }
  window.adminRemoveCertificate = function(idx) {
    if (!confirm('¿Eliminar este certificado?')) return
    data.certificates.splice(idx, 1)
    populateCertificatesList()
    saveAll()
  }
  window.adminRemoveSkill = function(idx) {
    if (!confirm('¿Eliminar esta habilidad?')) return
    if (!data.skills.bars) data.skills.bars = []
    data.skills.bars.splice(idx, 1)
    populateSkillsList()
    saveAll()
  }
  window.adminRemoveChip = function(idx) {
    if (!confirm('¿Eliminar este chip?')) return
    if (!data.skills.chips) data.skills.chips = []
    data.skills.chips.splice(idx, 1)
    populateChipsList()
    saveAll()
  }

  /* ── BOTÓN SUBIR A GITHUB ── */
  function addCommitButton() {
    const sidebar = document.querySelector('.admin-sidenav')
    if (!sidebar) return
    const btn = document.createElement('button')
    btn.className = 'admin-snav-item'
    const token = localStorage.getItem('gh_token')
    btn.innerHTML = `<span class="asi-icon">${token ? '✅' : '⚠️'}</span> Subir a GitHub`
    btn.addEventListener('click', () => { saveAll(); commitToGitHub() })
    sidebar.appendChild(btn)
  }

  /* ── INIT ── */
  async function init() {
    await loadCredentials()

    const fresh = await loadAllData()
    if (fresh) {
      data.profile = fresh.profile || {}
      data.activities = fresh.activities || []
      data.certificates = fresh.certificates || []
      data.skills = fresh.skills || { bars: [], chips: [], particleCount: 60 }
    }

    // Merge saved data from localStorage
    try {
      const saved = localStorage.getItem('admin_data')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed.activities && parsed.activities.length) data.activities = parsed.activities
        if (parsed.certificates && parsed.certificates.length) data.certificates = parsed.certificates
        if (parsed.skills) data.skills = deepMerge(data.skills, parsed.skills)
        if (parsed.profile) data.profile = deepMerge(data.profile, parsed.profile)
      }
    } catch(e) {
      console.warn('Error parsing localStorage:', e)
    }

    // Ensure skills has bars array
    if (!data.skills.bars) data.skills.bars = data.skills.items || []
    if (!data.skills.chips) data.skills.chips = []
    // Delete old items key to avoid confusion
    delete data.skills.items

    // Migrate social sub-object to flat fields for profile
    if (data.profile.social) {
      if (!data.profile.linkedin && data.profile.social.linkedin) data.profile.linkedin = data.profile.social.linkedin
      if (!data.profile.github && data.profile.social.github) data.profile.github = data.profile.social.github
    }
    // Ensure heroPhoto from photo
    if (!data.profile.heroPhoto && data.profile.photo) data.profile.heroPhoto = data.profile.photo

    addCommitButton()
  }

  init()
})()
