(function () {
  'use strict'

  let credentials = { username: 'Sarita', password: '_2709_' }
  let data = {
    profile: {}, activities: [], certificates: [],
    skills: { items: [], chips: [], particleCount: 60 }
  }
  let pendingChanges = {}
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

  /* LOGIN */
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

  /* SIDEBAR */
  document.querySelectorAll('.admin-snav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.admin-snav-item').forEach(b => b.classList.remove('active'))
      document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'))
      btn.classList.add('active')
      const sec = document.getElementById('sec-' + btn.dataset.section)
      if (sec) sec.classList.add('active')
    })
  })

  /* POPULATE */
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
    const tags = p.heroTags
    document.getElementById('heroTags').value = Array.isArray(tags) ? tags.join(', ') : (tags || '')
  }

  function populateAboutForm() {
    document.getElementById('aboutBio').value = data.profile.bio || ''
  }

  function populateProfileForm() {
    const p = data.profile
    if (!p.name) return
    document.getElementById('profName').value = p.name || ''
    document.getElementById('profEmail').value = p.email || ''
    document.getElementById('profCareer').value = p.career || ''
    document.getElementById('profFaculty').value = p.faculty || ''
    document.getElementById('profUni').value = p.university || ''
    document.getElementById('profProfessor').value = p.professor || ''
    document.getElementById('profSubject').value = p.subject || ''
    document.getElementById('profYear').value = p.year || ''
    document.getElementById('profPhoto').value = p.photo || ''
  }

  function populateContactForm() {
    const p = data.profile
    document.getElementById('contEmail').value = p.email || ''
    document.getElementById('contLinkedin').value = (p.social && p.social.linkedin) || ''
    document.getElementById('contYoutube').value = (p.social && p.social.youtube) || ''
    document.getElementById('contGithub').value = (p.social && p.social.github) || ''
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
      `<div class="admin-list-item"><span>#${i+1} <strong>${a.title}</strong> (${a.status||'Pendiente'})</span>
        <button onclick="adminEditActivity(${i})">Editar</button>
        <button onclick="adminRemoveActivity(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateCertificatesList() {
    const c = document.getElementById('certificatesList')
    if (!data.certificates.length) { c.innerHTML = '<p style="color:var(--text2);font-size:13px;">No hay certificados.</p>'; return }
    c.innerHTML = data.certificates.map((cert, i) =>
      `<div class="admin-list-item"><span>#${i+1} <strong>${cert.title}</strong></span>
        <button onclick="adminEditCertificate(${i})">Editar</button>
        <button onclick="adminRemoveCertificate(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateSkillsList() {
    const c = document.getElementById('skillsList')
    if (!data.skills.items.length) { c.innerHTML = '<p style="color:var(--text2);font-size:13px;">No hay habilidades.</p>'; return }
    c.innerHTML = data.skills.items.map((item, i) =>
      `<div class="admin-list-item"><span><strong>${item.name}</strong> — ${item.percentage}%</span>
        <button onclick="adminEditSkill(${i})">Editar</button>
        <button onclick="adminRemoveSkill(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateChipsList() {
    const c = document.getElementById('chipsList')
    if (!data.skills.chips.length) { c.innerHTML = '<p style="color:var(--text2);font-size:13px;">No hay chips.</p>'; return }
    c.innerHTML = data.skills.chips.map((chip, i) =>
      `<div class="admin-list-item"><span><strong>${chip}</strong></span>
        <button onclick="adminEditChip(${i})">Editar</button>
        <button onclick="adminRemoveChip(${i})">Eliminar</button></div>`
    ).join('')
  }

  function populateParticleCount() {
    const el = document.getElementById('currentParticleCount')
    if (el) el.textContent = data.skills.particleCount || 60
    document.getElementById('particleCount').value = data.skills.particleCount || 60
  }

  /* HELPERS */
  function addToPending(key, value) { pendingChanges[key] = value }

  function saveAll() {
    localStorage.setItem('admin_data', JSON.stringify(data))
    localStorage.setItem('admin_pending', JSON.stringify(pendingChanges))
    localStorage.setItem('admin_credentials', JSON.stringify(credentials))
    console.log('✅ Datos guardados en localStorage:', JSON.stringify(data.profile).slice(0, 200))
  }

  async function commitToGitHub() {
    const token = localStorage.getItem('gh_token')
    if (!token) {
      alert('⚠️ No hay token de GitHub.\n\nLos cambios están guardados LOCALMENTE.\n\nPara subirlos:\n1. Crea un token en GitHub > Settings > Developer Settings > Personal Access Tokens > Fine-grained tokens\n2. Permiso: "contents: write" para tu repo\n3. En consola del navegador (F12):\n   localStorage.setItem("gh_token", "TU_TOKEN")\n4. Vuelve a hacer clic en "Subir a GitHub"')
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
      }
      if (pendingChanges.credentials) {
        files['data/credentials.json'] = JSON.stringify(credentials, null, 2)
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

      alert('✅ Cambios subidos a GitHub. La página se actualizará en ~1-2 min.')
      pendingChanges = {}
      localStorage.setItem('admin_pending', '{}')
    } catch (e) {
      alert('⚠️ Error: ' + e.message + '\n\nVerifica que el token tenga permisos "contents: write" para el repo.')
    }
  }

  /* ── FORM HANDLERS (siempre preservan datos existentes) ──── */

  document.getElementById('inicioForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const raw = document.getElementById('heroTags').value
    data.profile.heroTitleL1 = document.getElementById('heroTitleL1').value
    data.profile.heroTitleL2 = document.getElementById('heroTitleL2').value
    data.profile.heroSub = document.getElementById('heroSub').value
    data.profile.heroDesc = document.getElementById('heroDesc').value
    data.profile.heroTags = raw ? raw.split(',').map(t => t.trim()).filter(Boolean) : []
    addToPending('profile', data.profile)
    saveAll()
    alert('✅ Inicio guardado.')
  })

  document.getElementById('aboutForm').addEventListener('submit', (e) => {
    e.preventDefault()
    data.profile.bio = document.getElementById('aboutBio').value
    addToPending('profile', data.profile)
    saveAll()
    alert('✅ Sobre mí guardado.')
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
    data.profile.photo = document.getElementById('profPhoto').value
    addToPending('profile', data.profile)
    saveAll()
    alert('✅ Perfil guardado.')
  })

  document.getElementById('contactForm').addEventListener('submit', (e) => {
    e.preventDefault()
    if (!data.profile.social) data.profile.social = {}
    data.profile.email = document.getElementById('contEmail').value
    data.profile.social.linkedin = document.getElementById('contLinkedin').value
    data.profile.social.youtube = document.getElementById('contYoutube').value
    data.profile.social.github = document.getElementById('contGithub').value
    addToPending('profile', data.profile)
    saveAll()
    alert('✅ Contacto guardado.')
  })

  document.getElementById('activityForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const act = {
      title: document.getElementById('actTitle').value,
      date: document.getElementById('actDate').value,
      grade: document.getElementById('actGrade').value ? parseInt(document.getElementById('actGrade').value) : null,
      status: document.getElementById('actStatus').value,
      cover: document.getElementById('actCover').value,
      pdf: document.getElementById('actPdf').value,
    }
    if (editingIndex !== null && editingType === 'act') {
      data.activities[editingIndex] = act
      editingIndex = null; editingType = null
      document.getElementById('actSubmitBtn').textContent = 'Añadir Actividad'
      document.getElementById('actCancelBtn').style.display = 'none'
    } else {
      data.activities.push(act)
    }
    addToPending('activities', data.activities)
    populateActivitiesList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('certForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const cert = {
      title: document.getElementById('certTitle').value,
      description: document.getElementById('certDesc').value,
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
    addToPending('certificates', data.certificates)
    populateCertificatesList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('skillForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const skill = {
      name: document.getElementById('skillName').value,
      percentage: parseInt(document.getElementById('skillPct').value),
    }
    if (editingIndex !== null && editingType === 'skill') {
      data.skills.items[editingIndex] = skill
      editingIndex = null; editingType = null
      document.getElementById('skillSubmitBtn').textContent = 'Añadir Habilidad'
      document.getElementById('skillCancelBtn').style.display = 'none'
    } else {
      data.skills.items.push(skill)
    }
    addToPending('skills', data.skills)
    populateSkillsList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('chipForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const chip = document.getElementById('chipName').value
    if (editingIndex !== null && editingType === 'chip') {
      data.skills.chips[editingIndex] = chip
      editingIndex = null; editingType = null
      document.getElementById('chipSubmitBtn').textContent = 'Añadir Chip'
      document.getElementById('chipCancelBtn').style.display = 'none'
    } else {
      data.skills.chips.push(chip)
    }
    addToPending('skills', data.skills)
    populateChipsList()
    e.target.reset()
    saveAll()
  })

  document.getElementById('particleForm').addEventListener('submit', (e) => {
    e.preventDefault()
    const val = parseInt(document.getElementById('particleCount').value)
    if (val < 10 || val > 200 || isNaN(val)) { alert('Valor entre 10 y 200.'); return }
    data.skills.particleCount = val
    addToPending('skills', data.skills)
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
    addToPending('credentials', credentials)
    document.getElementById('credSuccess').style.display = 'block'
    document.getElementById('newUser').value = ''
    document.getElementById('newPass').value = ''
    document.getElementById('confirmPass').value = ''
    saveAll()
  })

  /* ── EDITAR ─────────────────────────────────────────────── */
  window.adminEditActivity = function(idx) {
    editingIndex = idx; editingType = 'act'
    const a = data.activities[idx]
    document.getElementById('actTitle').value = a.title || ''
    document.getElementById('actDate').value = a.date || ''
    document.getElementById('actGrade').value = a.grade != null ? a.grade : ''
    document.getElementById('actStatus').value = a.status || 'Pendiente'
    document.getElementById('actCover').value = a.cover || ''
    document.getElementById('actPdf').value = a.pdf || ''
    document.getElementById('actSubmitBtn').textContent = 'Actualizar Actividad'
    document.getElementById('actCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="activities"]').click()
  }
  window.adminEditCertificate = function(idx) {
    editingIndex = idx; editingType = 'cert'
    const c = data.certificates[idx]
    document.getElementById('certTitle').value = c.title || ''
    document.getElementById('certDesc').value = c.description || ''
    document.getElementById('certImage').value = c.image || ''
    document.getElementById('certSubmitBtn').textContent = 'Actualizar Certificado'
    document.getElementById('certCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="certificates"]').click()
  }
  window.adminEditSkill = function(idx) {
    editingIndex = idx; editingType = 'skill'
    const s = data.skills.items[idx]
    document.getElementById('skillName').value = s.name || ''
    document.getElementById('skillPct').value = s.percentage || ''
    document.getElementById('skillSubmitBtn').textContent = 'Actualizar Habilidad'
    document.getElementById('skillCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="skills"]').click()
  }
  window.adminEditChip = function(idx) {
    editingIndex = idx; editingType = 'chip'
    document.getElementById('chipName').value = data.skills.chips[idx] || ''
    document.getElementById('chipSubmitBtn').textContent = 'Actualizar Chip'
    document.getElementById('chipCancelBtn').style.display = 'inline-block'
    document.querySelector('[data-section="skills"]').click()
  }

  document.getElementById('actCancelBtn').addEventListener('click', () => cancelEdit('act'))
  document.getElementById('certCancelBtn').addEventListener('click', () => cancelEdit('cert'))
  document.getElementById('skillCancelBtn').addEventListener('click', () => cancelEdit('skill'))
  document.getElementById('chipCancelBtn').addEventListener('click', () => cancelEdit('chip'))

  /* ── ELIMINAR ───────────────────────────────────────────── */
  window.adminRemoveActivity = function(idx) {
    if (!confirm('¿Eliminar esta actividad?')) return
    data.activities.splice(idx, 1)
    addToPending('activities', data.activities)
    populateActivitiesList()
    saveAll()
  }
  window.adminRemoveCertificate = function(idx) {
    if (!confirm('¿Eliminar este certificado?')) return
    data.certificates.splice(idx, 1)
    addToPending('certificates', data.certificates)
    populateCertificatesList()
    saveAll()
  }
  window.adminRemoveSkill = function(idx) {
    if (!confirm('¿Eliminar esta habilidad?')) return
    data.skills.items.splice(idx, 1)
    addToPending('skills', data.skills)
    populateSkillsList()
    saveAll()
  }
  window.adminRemoveChip = function(idx) {
    if (!confirm('¿Eliminar este chip?')) return
    data.skills.chips.splice(idx, 1)
    addToPending('skills', data.skills)
    populateChipsList()
    saveAll()
  }

  /* ── BOTÓN SUBIR A GITHUB ───────────────────────────────── */
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

  /* ── INIT ───────────────────────────────────────────────── */
  async function init() {
    await loadCredentials()

    /* 1. Cargar datos frescos desde JSON */
    const fresh = await loadAllData()
    if (fresh) {
      data.profile = fresh.profile || {}
      data.activities = fresh.activities || []
      data.certificates = fresh.certificates || []
      data.skills = fresh.skills || { items: [], chips: [], particleCount: 60 }
    }

    /* 2. Si hay datos en localStorage, hacer merge (preservar todo) */
    try {
      const saved = localStorage.getItem('admin_data')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed.activities) {
          data.activities = parsed.activities
        }
        if (parsed.certificates) {
          data.certificates = parsed.certificates
        }
        if (parsed.skills) {
          data.skills = deepMerge(data.skills, parsed.skills)
        }
        if (parsed.profile && parsed.profile.name) {
          data.profile = deepMerge(data.profile, parsed.profile)
        }
      }
    } catch(e) {
      console.warn('Error parsing localStorage:', e)
    }

    addCommitButton()
  }

  init()
})()
