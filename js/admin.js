(function () {
  'use strict';

  let credentials = { username: 'Sarita', password: '_2709_' };
  let data = {
    profile: {}, activities: [], certificates: [],
    skills: { items: [], chips: [], particleCount: 60 },
    evidences: {}
  };
  let pendingChanges = {};

  const loginScreen = document.getElementById('loginScreen');
  const dashScreen = document.getElementById('dashboardScreen');
  const loginForm = document.getElementById('loginForm');
  const loginUser = document.getElementById('loginUser');
  const loginPass = document.getElementById('loginPass');
  const loginError = document.getElementById('loginError');
  const logoutBtn = document.getElementById('logoutBtn');
  const dashUser = document.getElementById('dashUser');

  async function loadCredentials() {
    try {
      const saved = localStorage.getItem('admin_credentials');
      if (saved) { credentials = JSON.parse(saved); return; }
    } catch(e) {}
    try {
      const r = await fetch('data/credentials.json');
      credentials = await r.json();
    } catch (e) {
      console.warn('No credentials file, using defaults');
    }
  }

  async function loadAllData() {
    try {
      const [p, a, c, s, e] = await Promise.all([
        fetch('data/profile.json').then(r => r.json()),
        fetch('data/activities.json').then(r => r.json()),
        fetch('data/certificates.json').then(r => r.json()),
        fetch('data/skills.json').then(r => r.json()),
        fetch('data/evidences.json').then(r => r.json()),
      ]);
      data.profile = p;
      data.activities = a;
      data.certificates = c;
      data.skills = s;
      data.evidences = e;
    } catch (err) {
      console.warn('Error loading data:', err);
    }
  }

  /* ── LOGIN ─────────────────────────────────────────────────── */
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const user = loginUser.value.trim();
    const pass = loginPass.value;
    if (user === credentials.username && pass === credentials.password) {
      loginScreen.style.display = 'none';
      dashScreen.style.display = 'block';
      dashUser.textContent = credentials.username;
      loginError.style.display = 'none';
      populateAll();
    } else {
      loginError.style.display = 'block';
    }
  });

  logoutBtn.addEventListener('click', () => {
    dashScreen.style.display = 'none';
    loginScreen.style.display = 'flex';
    loginForm.reset();
  });

  /* ── SIDEBAR NAV ──────────────────────────────────────────── */
  document.querySelectorAll('.admin-snav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.admin-snav-item').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'));
      btn.classList.add('active');
      const sec = document.getElementById('sec-' + btn.dataset.section);
      if (sec) sec.classList.add('active');
    });
  });

  /* ── POPULATE FORMS ────────────────────────────────────────── */
  function populateAll() {
    populateProfileForm();
    populateActivitiesList();
    populateCertificatesList();
    populateSkillsList();
    populateChipsList();
    populateEvidencesList();
    populateEvSelect();
    populateParticleCount();
  }

  function populateProfileForm() {
    const p = data.profile;
    if (!p.name) return;
    document.getElementById('profName').value = p.name || '';
    document.getElementById('profEmail').value = p.email || '';
    document.getElementById('profCareer').value = p.career || '';
    document.getElementById('profFaculty').value = p.faculty || '';
    document.getElementById('profUni').value = p.university || '';
    document.getElementById('profProfessor').value = p.professor || '';
    document.getElementById('profSubject').value = p.subject || '';
    document.getElementById('profYear').value = p.year || '';
    document.getElementById('profPhoto').value = p.photo || '';
    document.getElementById('profBio').value = p.bio || '';
    document.getElementById('profLinkedin').value = (p.social && p.social.linkedin) || '';
    document.getElementById('profYoutube').value = (p.social && p.social.youtube) || '';
  }

  function populateActivitiesList() {
    const container = document.getElementById('activitiesList');
    if (!data.activities.length) { container.innerHTML = '<p style="color:var(--text-secondary);font-size:13px;">No hay actividades aún.</p>'; return; }
    container.innerHTML = data.activities.map((act, i) =>
      `<div class="admin-list-item"><span>#${i + 1} — <strong>${act.title}</strong> (${act.status || 'Pendiente'})</span><button onclick="adminRemoveActivity(${i})">Eliminar</button></div>`
    ).join('');
  }

  function populateCertificatesList() {
    const container = document.getElementById('certificatesList');
    if (!data.certificates.length) { container.innerHTML = '<p style="color:var(--text-secondary);font-size:13px;">No hay certificados aún.</p>'; return; }
    container.innerHTML = data.certificates.map((cert, i) =>
      `<div class="admin-list-item"><span>#${i+1} - <strong>${cert.title}</strong></span><button onclick="adminRemoveCertificate(${i})">Eliminar</button></div>`
    ).join('');
  }

  function populateSkillsList() {
    const container = document.getElementById('skillsList');
    if (!data.skills.items.length) { container.innerHTML = '<p style="color:var(--text-secondary);font-size:13px;">No hay habilidades aún.</p>'; return; }
    container.innerHTML = data.skills.items.map((item, i) =>
      `<div class="admin-list-item"><span><strong>${item.name}</strong> — ${item.percentage}%</span><button onclick="adminRemoveSkill(${i})">Eliminar</button></div>`
    ).join('');
  }

  function populateChipsList() {
    const container = document.getElementById('chipsList');
    if (!data.skills.chips.length) { container.innerHTML = '<p style="color:var(--text-secondary);font-size:13px;">No hay chips aún.</p>'; return; }
    container.innerHTML = data.skills.chips.map((chip, i) =>
      `<div class="admin-list-item"><span><strong>${chip}</strong></span><button onclick="adminRemoveChip(${i})">Eliminar</button></div>`
    ).join('');
  }

  function populateEvSelect() {
    const sel = document.getElementById('evActSelect');
    sel.innerHTML = data.activities.map((act, i) =>
      `<option value="${i}">${act.title}</option>`
    ).join('');
  }

  function populateEvidencesList() {
    const container = document.getElementById('evidencesList');
    let html = '';
    data.activities.forEach((act, idx) => {
      const key = `act-${idx}`;
      const evs = data.evidences[key] || [];
      if (!evs.length) return;
      html += `<div class="admin-list-item" style="flex-wrap:wrap;"><span><strong>${act.title}</strong>: ${evs.length} evidencia(s)</span>`;
      evs.forEach((ev, j) => {
        html += `<button onclick="adminRemoveEvidence(${idx}, ${j})" style="margin-left:4px;">✕ ${ev.label || j+1}</button>`;
      });
      html += `</div>`;
    });
    if (!html) html = '<p style="color:var(--text-secondary);font-size:13px;">No hay evidencias aún.</p>';
    container.innerHTML = html;
  }

  function populateParticleCount() {
    const el = document.getElementById('currentParticleCount');
    if (el) el.textContent = data.skills.particleCount || 60;
    document.getElementById('particleCount').value = data.skills.particleCount || 60;
  }

  /* ── CRUD HELPERS ──────────────────────────────────────────── */
  function addToPending(key, value) {
    pendingChanges[key] = value;
  }

  async function commitAll() {
    const token = localStorage.getItem('gh_token');
    if (!token) {
      const msg = '⚠️ No hay token de GitHub.\n\nLos cambios están guardados LOCALMENTE (en localStorage).\nPara subirlos al repositorio:\n\n1. Ve a GitHub > Settings > Developer Settings > Personal Access Tokens > Fine-grained tokens\n2. Crea un token con permisos "contents: write" para tu repo\n3. En la consola del navegador (F12 > Console), escribe:\n   localStorage.setItem("gh_token", "TU_TOKEN_AQUI")\n4. Vuelve a hacer clic en "Subir a GitHub"';
      alert(msg);
      return;
    }
    const owner = 'irvinMartinez2709';
    const repo = 'portafolio-programacion-ii';
    const auth = { 'Authorization': `Bearer ${token}`, 'Accept': 'application/vnd.github.v3+json' };
    const json = (r) => r.json();
    try {
      /* 1. Obtener el commit actual de la rama main */
      const refUrl = `https://api.github.com/repos/${owner}/${repo}/git/refs/heads/main`;
      const refRes = await fetch(refUrl, { headers: auth });
      if (!refRes.ok) throw new Error(`No se pudo obtener la rama (${refRes.status}): asegúrate de que el token tenga permisos de escritura en el repo.`);
      const latestSha = (await json(refRes)).object.sha;

      /* 2. Obtener el tree SHA del commit actual */
      const commitRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/commits/${latestSha}`, { headers: auth });
      const baseTreeSha = (await json(commitRes)).tree.sha;

      /* 3. Preparar archivos a actualizar */
      const files = {
        'data/activities.json': JSON.stringify(data.activities, null, 2),
        'data/certificates.json': JSON.stringify(data.certificates, null, 2),
        'data/profile.json': JSON.stringify(data.profile, null, 2),
        'data/skills.json': JSON.stringify(data.skills, null, 2),
        'data/evidences.json': JSON.stringify(data.evidences, null, 2),
      };
      if (pendingChanges.credentials) {
        files['data/credentials.json'] = JSON.stringify(credentials, null, 2);
      }

      /* 4. Crear blobs para cada archivo */
      const treeItems = [];
      for (const [path, content] of Object.entries(files)) {
        const blobRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/blobs`, {
          method: 'POST',
          headers: { ...auth, 'Content-Type': 'application/json' },
          body: JSON.stringify({ content, encoding: 'utf-8' })
        });
        if (!blobRes.ok) throw new Error(`Error al crear blob para ${path}`);
        treeItems.push({ path, mode: '100644', type: 'blob', sha: (await json(blobRes)).sha });
      }

      /* 5. Crear un nuevo tree basado en el actual + cambios */
      const treeRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/trees`, {
        method: 'POST',
        headers: { ...auth, 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems })
      });
      if (!treeRes.ok) throw new Error('Error al crear el tree');

      /* 6. Crear un commit apuntando al nuevo tree */
      const newTreeSha = (await json(treeRes)).sha;
      const commitRes2 = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/commits`, {
        method: 'POST',
        headers: { ...auth, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'admin: actualizar contenido del portafolio',
          tree: newTreeSha,
          parents: [latestSha]
        })
      });
      if (!commitRes2.ok) throw new Error('Error al crear el commit');

      /* 7. Mover la rama main al nuevo commit */
      const newCommitSha = (await json(commitRes2)).sha;
      const updateRes = await fetch(refUrl, {
        method: 'PATCH',
        headers: { ...auth, 'Content-Type': 'application/json' },
        body: JSON.stringify({ sha: newCommitSha, force: false })
      });
      if (!updateRes.ok) throw new Error('Error al actualizar la rama');

      alert('✅ Cambios subidos a GitHub. La página se actualizará en ~1-2 minutos.');
      pendingChanges = {};
      localStorage.setItem('admin_pending', '{}');
    } catch (e) {
      alert('⚠️ Error: ' + e.message);
    }
  }

  /* ── FORM HANDLERS ─────────────────────────────────────────── */
  document.getElementById('activityForm').addEventListener('submit', (e) => {
    e.preventDefault();
    data.activities.push({
      title: document.getElementById('actTitle').value,
      date: document.getElementById('actDate').value,
      grade: document.getElementById('actGrade').value ? parseInt(document.getElementById('actGrade').value) : null,
      status: document.getElementById('actStatus').value,
      cover: document.getElementById('actCover').value,
      pdf: document.getElementById('actPdf').value,
    });
    addToPending('activities', data.activities);
    populateActivitiesList();
    populateEvSelect();
    e.target.reset();
    saveAll();
  });

  document.getElementById('certForm').addEventListener('submit', (e) => {
    e.preventDefault();
    data.certificates.push({
      title: document.getElementById('certTitle').value,
      description: document.getElementById('certDesc').value,
      image: document.getElementById('certImage').value,
    });
    addToPending('certificates', data.certificates);
    populateCertificatesList();
    e.target.reset();
    saveAll();
  });

  document.getElementById('evidenceForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const actIdx = parseInt(document.getElementById('evActSelect').value);
    const key = `act-${actIdx}`;
    if (!data.evidences[key]) data.evidences[key] = [];
    data.evidences[key].push({
      src: document.getElementById('evidSrc').value,
      label: document.getElementById('evidLabel').value || `Captura ${data.evidences[key].length + 1}`,
    });
    addToPending('evidences', data.evidences);
    populateEvidencesList();
    e.target.reset();
    saveAll();
  });

  document.getElementById('profileForm').addEventListener('submit', (e) => {
    e.preventDefault();
    data.profile = {
      name: document.getElementById('profName').value,
      email: document.getElementById('profEmail').value,
      career: document.getElementById('profCareer').value,
      faculty: document.getElementById('profFaculty').value,
      university: document.getElementById('profUni').value,
      professor: document.getElementById('profProfessor').value,
      subject: document.getElementById('profSubject').value,
      year: document.getElementById('profYear').value,
      photo: document.getElementById('profPhoto').value,
      bio: document.getElementById('profBio').value,
      social: {
        linkedin: document.getElementById('profLinkedin').value,
        youtube: document.getElementById('profYoutube').value,
        github: 'https://github.com/irvinMartinez2709',
      }
    };
    addToPending('profile', data.profile);
    saveAll();
    alert('Perfil guardado.');
  });

  document.getElementById('skillForm').addEventListener('submit', (e) => {
    e.preventDefault();
    data.skills.items.push({
      name: document.getElementById('skillName').value,
      percentage: parseInt(document.getElementById('skillPct').value),
    });
    addToPending('skills', data.skills);
    populateSkillsList();
    e.target.reset();
    saveAll();
  });

  document.getElementById('chipForm').addEventListener('submit', (e) => {
    e.preventDefault();
    data.skills.chips.push(document.getElementById('chipName').value);
    addToPending('skills', data.skills);
    populateChipsList();
    e.target.reset();
    saveAll();
  });

  document.getElementById('particleForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const val = parseInt(document.getElementById('particleCount').value);
    if (val < 10 || val > 200 || isNaN(val)) { alert('Ingresa un valor entre 10 y 200.'); return; }
    data.skills.particleCount = val;
    addToPending('skills', data.skills);
    populateParticleCount();
    saveAll();
  });

  document.getElementById('credForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const newUser = document.getElementById('newUser').value.trim();
    const newPass = document.getElementById('newPass').value;
    const confirmPass = document.getElementById('confirmPass').value;
    const errorEl = document.getElementById('credError');
    const successEl = document.getElementById('credSuccess');
    errorEl.style.display = 'none';
    successEl.style.display = 'none';
    if (newPass !== confirmPass) {
      errorEl.style.display = 'block';
      return;
    }
    credentials = { username: newUser, password: newPass };
    dashUser.textContent = newUser;
    addToPending('credentials', credentials);
    successEl.style.display = 'block';
    document.getElementById('newUser').value = '';
    document.getElementById('newPass').value = '';
    document.getElementById('confirmPass').value = '';
    saveAll();
  });

  /* ── REMOVE FUNCTIONS (globally accessible for onclick) ────── */
  window.adminRemoveActivity = function(idx) {
    data.activities.splice(idx, 1);
    addToPending('activities', data.activities);
    populateActivitiesList();
    populateEvSelect();
    saveAll();
  };
  window.adminRemoveCertificate = function(idx) {
    data.certificates.splice(idx, 1);
    addToPending('certificates', data.certificates);
    populateCertificatesList();
    saveAll();
  };
  window.adminRemoveSkill = function(idx) {
    data.skills.items.splice(idx, 1);
    addToPending('skills', data.skills);
    populateSkillsList();
    saveAll();
  };
  window.adminRemoveChip = function(idx) {
    data.skills.chips.splice(idx, 1);
    addToPending('skills', data.skills);
    populateChipsList();
    saveAll();
  };
  window.adminRemoveEvidence = function(actIdx, evIdx) {
    const key = `act-${actIdx}`;
    if (data.evidences[key]) data.evidences[key].splice(evIdx, 1);
    if (data.evidences[key] && !data.evidences[key].length) delete data.evidences[key];
    addToPending('evidences', data.evidences);
    populateEvidencesList();
    saveAll();
  };

  function saveAll() {
    localStorage.setItem('admin_data', JSON.stringify(data));
    localStorage.setItem('admin_pending', JSON.stringify(pendingChanges));
    localStorage.setItem('admin_credentials', JSON.stringify(credentials));
  }

  // Add a "Commit to GitHub" button in the sidebar or dashboard
  function addCommitButton() {
    const sidebar = document.querySelector('.admin-sidenav');
    if (!sidebar) return;
    const btn = document.createElement('button');
    btn.className = 'admin-snav-item';
    const token = localStorage.getItem('gh_token');
    const statusIcon = token ? '\u2705' : '\u26A0\uFE0F';
    btn.innerHTML = `<span class="asi-icon">${statusIcon}</span> Subir a GitHub`;
    if (!token) {
      btn.title = 'Token no configurado. Haz clic para instrucciones.';
    }
    btn.addEventListener('click', () => {
      saveAll();
      commitAll();
    });
    sidebar.appendChild(btn);
  }

  /* ── INIT ──────────────────────────────────────────────────── */
  async function init() {
    await loadCredentials();
    await loadAllData();
    try {
      const saved = localStorage.getItem('admin_data');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.activities) data = parsed;
      }
    } catch(e) {}
    addCommitButton();
  }

  init();
})();