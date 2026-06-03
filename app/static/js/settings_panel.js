// Settings Panel — embedded in each portal dashboard
// Uses spGetToken() to avoid conflicts with existing token variables.

function spGetToken() { return localStorage.getItem('access_token'); }

let _spToastTimer;
function spToast(msg, ok = true) {
  const el = document.getElementById('spToastEl');
  if (!el) return;
  el.querySelector('.spt-msg').textContent  = msg;
  el.querySelector('.spt-icon').textContent = ok ? 'check_circle' : 'error';
  el.querySelector('.spt-inner').className  =
    `spt-inner flex items-center gap-3 px-5 py-4 rounded-2xl shadow-lg text-white font-semibold text-sm
    ${ok ? 'bg-[#2D5A27]' : 'bg-[#ba1a1a]'}`;
  el.classList.remove('hidden');
  clearTimeout(_spToastTimer);
  _spToastTimer = setTimeout(() => el.classList.add('hidden'), 3500);
}

function spSetBusy(btn, busy) {
  if (busy) {
    btn.disabled = true;
    btn.dataset.orig = btn.innerHTML;
    btn.innerHTML = '<span class="material-symbols-outlined text-[18px] sp-spin">refresh</span> Saving…';
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.orig;
  }
}

function spShowTab(name) {
  document.querySelectorAll('[id^="sp-tab-"]').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.sp-tab-btn').forEach(btn => {
    const active = btn.dataset.tab === name;
    btn.classList.toggle('bg-white',               active);
    btn.classList.toggle('shadow',                 active);
    btn.classList.toggle('text-primary',           active);
    btn.classList.toggle('text-on-surface-variant', !active);
  });
  const tab = document.getElementById(`sp-tab-${name}`);
  if (tab) tab.classList.remove('hidden');
}

// ── File uploads ────────────────────────────────────────────────────────────────
const _spUrls = {};

function spDragOver(e, el) { e.preventDefault(); el.classList.add('sp-drag-over'); }
function spDragLeave(e, el) { (el || e).classList.remove('sp-drag-over'); }
function spDropFile(e, el, inputId, slot) {
  e.preventDefault(); el.classList.remove('sp-drag-over');
  const inp = document.getElementById(inputId);
  if (inp && e.dataTransfer.files.length) {
    const dt = new DataTransfer();
    Array.from(e.dataTransfer.files).forEach(f => dt.items.add(f));
    inp.files = dt.files;
  }
  if (e.dataTransfer.files[0]) spPreviewDoc({ files: e.dataTransfer.files }, slot);
}

async function spPreviewDoc(input, slot) {
  const file = input.files[0];
  if (!file) return;
  const prev = document.getElementById(`sp-prev-${slot}`);
  if (!prev) return;
  prev.classList.remove('hidden', 'd-none');

  if (file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = e => { prev.innerHTML = `<img src="${e.target.result}" class="mx-auto max-h-36 rounded-xl object-contain"/><p class="text-xs text-gray-400 mt-1">Uploading…</p>`; };
    reader.readAsDataURL(file);
  } else {
    prev.innerHTML = `<span class="material-symbols-outlined text-[36px] text-[#2D5A27] block mb-1">picture_as_pdf</span><p class="text-sm">${file.name}</p><p class="text-xs text-gray-400">Uploading…</p>`;
  }

  try {
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch(`${API}/users/me/upload-document`, {
      method: 'POST', headers: { Authorization: `Bearer ${spGetToken()}` }, body: fd,
    });
    if (!res.ok) throw new Error('Upload failed');
    const { url } = await res.json();
    _spUrls[slot] = url;
    const done = `<span class="material-symbols-outlined text-[#2D5A27] text-[20px]" style="font-variation-settings:'FILL' 1;">check_circle</span><p class="text-xs text-[#2D5A27] mt-1">Uploaded</p>`;
    prev.innerHTML = file.type.startsWith('image/')
      ? `<img src="${url}" class="mx-auto max-h-36 rounded-xl object-contain"/>${done}`
      : `<span class="material-symbols-outlined text-[36px] text-[#2D5A27] block mb-1">picture_as_pdf</span><p class="text-sm">${file.name}</p>${done}`;
  } catch {
    prev.innerHTML = `<span class="material-symbols-outlined text-[#ba1a1a] text-[36px] block mb-1">error</span><p class="text-xs text-[#ba1a1a]">Upload failed. Try again.</p>`;
  }
}

function spToggleBackSide() {
  const type = document.getElementById('sp-docType')?.value;
  const wrap = document.getElementById('sp-backSideWrap');
  if (wrap) wrap.style.display = type === 'passport' ? 'none' : '';
}

async function spUploadAvatar(input) {
  const file = input.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const el = document.getElementById('sp-profileAvatar');
    if (el) el.innerHTML = `<img src="${e.target.result}" class="w-full h-full object-cover"/>`;
  };
  reader.readAsDataURL(file);
  try {
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch(`${API}/users/me/avatar`, { method:'POST', headers:{Authorization:`Bearer ${spGetToken()}`}, body:fd });
    spToast(res.ok ? 'Profile photo updated' : 'Avatar upload failed', res.ok);
  } catch { spToast('Avatar upload failed', false); }
}

// ── Save profile ────────────────────────────────────────────────────────────────
async function spSaveProfile(btn) {
  spSetBusy(btn, true);
  try {
    const res = await fetch(`${API}/users/me`, {
      method: 'PATCH',
      headers: { Authorization:`Bearer ${spGetToken()}`, 'Content-Type':'application/json' },
      body: JSON.stringify({
        full_name:          document.getElementById('sp-pName')?.value.trim() || undefined,
        phone_number:       document.getElementById('sp-pPhone')?.value.trim() || undefined,
        preferred_language: document.getElementById('sp-pLang')?.value || undefined,
      }),
    });
    if (!res.ok) { const e=await res.json(); throw new Error(e.detail||'Save failed'); }
    spToast('Profile saved successfully');
  } catch(e) { spToast(e.message, false); }
  finally { spSetBusy(btn, false); }
}

// ── KYC ─────────────────────────────────────────────────────────────────────────
async function spSubmitKYC() {
  const btn = document.getElementById('sp-kycSubmitBtn');
  const frontUrl = _spUrls['front'];
  if (!frontUrl) { spToast('Please upload the front of your document first', false); return; }
  const docNum = document.getElementById('sp-docNumber')?.value.trim();
  if (!docNum) { spToast('Please enter a document number', false); return; }
  spSetBusy(btn, true);
  try {
    const res = await fetch(`${API}/kyc/me/submit`, {
      method:'POST',
      headers:{ Authorization:`Bearer ${spGetToken()}`, 'Content-Type':'application/json' },
      body: JSON.stringify({
        document_type:   document.getElementById('sp-docType').value,
        document_number: docNum,
        document_front_url: frontUrl,
        document_back_url:  _spUrls['back'] || null,
        expiry_date: document.getElementById('sp-docExpiry')?.value || null,
      }),
    });
    if (!res.ok) { const e=await res.json(); throw new Error(e.detail||'Submission failed'); }
    spToast('Document submitted for verification');
    spShowKYCBanner('pending');
  } catch(e) { spToast(e.message, false); }
  finally { spSetBusy(btn, false); }
}

function spShowKYCBanner(status) {
  const cfg = {
    pending:       { cls:'bg-yellow-50 text-yellow-700 border-yellow-200',  icon:'pending',       title:'Verification Pending',     sub:'We\'re reviewing your document. 1–2 business days.' },
    approved:      { cls:'bg-green-50 text-green-700 border-green-200',     icon:'verified_user', title:'Identity Verified',         sub:'Your identity has been successfully verified.' },
    rejected:      { cls:'bg-red-50 text-red-700 border-red-200',           icon:'error',         title:'Verification Rejected',     sub:'Please resubmit with a clear, valid document.' },
    not_submitted: { cls:'bg-green-50 text-green-700 border-green-200',       icon:'info',          title:'Not Yet Verified',          sub:'Upload your ID to unlock full booking features.' },
  };
  const c = cfg[status] || cfg.not_submitted;
  const banner = document.getElementById('sp-kycBanner');
  if (!banner) return;
  banner.className = `rounded-2xl p-4 flex items-center gap-3 border ${c.cls}`;
  banner.innerHTML = `
    <span class="material-symbols-outlined text-[24px]" style="font-variation-settings:'FILL' 1;">${c.icon}</span>
    <div><p class="font-semibold">${c.title}</p><p class="text-sm opacity-80">${c.sub}</p></div>`;
  banner.classList.remove('hidden');
}

// ── Driver profile ───────────────────────────────────────────────────────────────
async function spSaveDriverProfile(btn) {
  const licNum   = document.getElementById('sp-dLicNumber')?.value.trim();
  const licExp   = document.getElementById('sp-dLicExpiry')?.value;
  const licClass = document.getElementById('sp-dLicClass')?.value;
  if (!licNum || !licExp) { spToast('Licence number and expiry are required', false); return; }
  spSetBusy(btn, true);
  try {
    const licDocUrl = _spUrls['licence'] || window._spExistingLicUrl || undefined;
    const payload = {
      license_class:       licClass,
      license_expiry:      licExp,
      license_doc_url:     licDocUrl,
      years_experience:    parseInt(document.getElementById('sp-dYears')?.value)||undefined,
      languages_spoken:    document.getElementById('sp-dLangs')?.value.trim()||undefined,
      specialties:         document.getElementById('sp-dSpecialties')?.value.trim()||undefined,
      bio:                 document.getElementById('sp-dBio')?.value.trim()||undefined,
      has_first_aid:       document.getElementById('sp-dFirstAid')?.checked||false,
      police_clearance_url:_spUrls['police']||undefined,
      police_clearance_exp:document.getElementById('sp-dPoliceExp')?.value||undefined,
      first_aid_cert_url:  _spUrls['firstaid']||undefined,
    };
    let res = await fetch(`${API}/owners/me/profile`, {
      method:'PATCH', headers:{Authorization:`Bearer ${spGetToken()}`,'Content-Type':'application/json'}, body:JSON.stringify(payload),
    });
    if (res.status === 404) {
      res = await fetch(`${API}/owners/me/profile`, {
        method:'POST', headers:{Authorization:`Bearer ${spGetToken()}`,'Content-Type':'application/json'},
        body:JSON.stringify({...payload, license_number:licNum}),
      });
    }
    if (!res.ok) { const e=await res.json(); throw new Error(e.detail||'Save failed'); }
    spToast('Owner profile saved');
  } catch(e) { spToast(e.message, false); }
  finally { spSetBusy(btn, false); }
}

// ── Password ─────────────────────────────────────────────────────────────────────
async function spChangePassword(btn) {
  const cur = document.getElementById('sp-pwCurrent')?.value;
  const nw  = document.getElementById('sp-pwNew')?.value;
  const cfm = document.getElementById('sp-pwConfirm')?.value;
  if (!cur||!nw||!cfm)  { spToast('All password fields are required', false); return; }
  if (nw.length < 8)     { spToast('New password must be at least 8 characters', false); return; }
  if (nw !== cfm)        { spToast('New passwords do not match', false); return; }
  spSetBusy(btn, true);
  try {
    const res = await fetch(`${API}/users/me/change-password`, {
      method:'POST', headers:{Authorization:`Bearer ${spGetToken()}`,'Content-Type':'application/json'},
      body:JSON.stringify({current_password:cur, new_password:nw}),
    });
    if (!res.ok) { const e=await res.json(); throw new Error(e.detail||'Password change failed'); }
    spToast('Password updated successfully');
    ['sp-pwCurrent','sp-pwNew','sp-pwConfirm'].forEach(id => { const el=document.getElementById(id); if(el) el.value=''; });
  } catch(e) { spToast(e.message, false); }
  finally { spSetBusy(btn, false); }
}

function spTogglePw(id, btn) {
  const inp = document.getElementById(id);
  const showing = inp.type === 'text';
  inp.type = showing ? 'password' : 'text';
  btn.querySelector('.material-symbols-outlined').textContent = showing ? 'visibility' : 'visibility_off';
}

// ── Load settings data ───────────────────────────────────────────────────────────
async function spLoadSettings() {
  try {
    const res = await fetch(`${API}/users/me`, { headers:{Authorization:`Bearer ${spGetToken()}`} });
    if (!res.ok) return;
    const user = await res.json();

    const pa = document.getElementById('sp-profileAvatar');
    if (pa) {
      pa.innerHTML = user.profile_photo_url
        ? `<img src="${user.profile_photo_url}" class="w-full h-full object-cover"/>`
        : (user.full_name ? user.full_name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() : '?');
    }

    if (document.getElementById('sp-pName'))  document.getElementById('sp-pName').value  = user.full_name || '';
    if (document.getElementById('sp-pEmail')) document.getElementById('sp-pEmail').value = user.email || '';
    if (document.getElementById('sp-pPhone')) document.getElementById('sp-pPhone').value = user.phone_number || '';
    if (document.getElementById('sp-pLang'))  document.getElementById('sp-pLang').value  = user.preferred_language || '';

    if (document.getElementById('sp-secRole'))    document.getElementById('sp-secRole').textContent    = user.role;
    if (document.getElementById('sp-secType'))    document.getElementById('sp-secType').textContent    = user.account_type;
    if (document.getElementById('sp-secJoined'))  document.getElementById('sp-secJoined').textContent  = user.created_at ? new Date(user.created_at).toLocaleDateString('en-UG',{day:'numeric',month:'short',year:'numeric'}) : '—';

    // Show driver profile tab for owners (owner IS the driver)
    const driverTabBtn = document.getElementById('sp-driverTabBtn');
    if (driverTabBtn) {
      if (user.role === 'owner') {
        driverTabBtn.classList.remove('hidden');
        spLoadDriverProfile();
      } else {
        driverTabBtn.classList.add('hidden');
      }
    }

    // Load KYC for customers/owners
    const kycWrap = document.getElementById('sp-tab-documents');
    if (kycWrap) {
      try {
        const kRes = await fetch(`${API}/kyc/me`, { headers:{Authorization:`Bearer ${spGetToken()}`} });
        if (kRes.ok) {
          const kyc = await kRes.json();
          if (kyc.status && kyc.status !== 'not_submitted') {
            spShowKYCBanner(kyc.status);
            if (kyc.document_type && document.getElementById('sp-docType'))   document.getElementById('sp-docType').value   = kyc.document_type;
            if (kyc.document_number && document.getElementById('sp-docNumber')) document.getElementById('sp-docNumber').value = kyc.document_number;
            if (kyc.expiry_date && document.getElementById('sp-docExpiry'))   document.getElementById('sp-docExpiry').value = kyc.expiry_date;
            if (kyc.document_front_url) {
              _spUrls['front'] = kyc.document_front_url;
              const fp = document.getElementById('sp-prev-front');
              if (fp) fp.innerHTML = `<img src="${kyc.document_front_url}" class="mx-auto max-h-36 rounded-xl object-contain"/><span class="material-symbols-outlined text-[#2D5A27] text-[20px]" style="font-variation-settings:'FILL' 1;">check_circle</span>`;
            }
          } else {
            spShowKYCBanner('not_submitted');
          }
        }
      } catch {}
    }

    spToggleBackSide();
  } catch {}
}

async function spLoadDriverProfile() {
  try {
    const res = await fetch(`${API}/owners/me/profile`, { headers:{Authorization:`Bearer ${spGetToken()}`} });
    if (!res.ok) return;
    const p = await res.json();
    if (document.getElementById('sp-dLicNumber'))   document.getElementById('sp-dLicNumber').value   = p.license_number || '';
    if (document.getElementById('sp-dLicClass'))    document.getElementById('sp-dLicClass').value    = p.license_class  || 'B';
    if (document.getElementById('sp-dLicExpiry'))   document.getElementById('sp-dLicExpiry').value   = p.license_expiry ? p.license_expiry.slice(0,10) : '';
    if (document.getElementById('sp-dYears'))       document.getElementById('sp-dYears').value       = p.years_experience || '';
    if (document.getElementById('sp-dLangs'))       document.getElementById('sp-dLangs').value       = p.languages_spoken || '';
    if (document.getElementById('sp-dSpecialties')) document.getElementById('sp-dSpecialties').value = p.specialties || '';
    if (document.getElementById('sp-dBio'))         document.getElementById('sp-dBio').value         = p.bio || '';
    if (document.getElementById('sp-dFirstAid'))    document.getElementById('sp-dFirstAid').checked  = p.has_first_aid || false;
    if (p.license_doc_url) { window._spExistingLicUrl = p.license_doc_url; }
  } catch {}
}
