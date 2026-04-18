/* =============================================
   ECOSPHERE — Backend API Client
   Connects frontend to FastAPI backend
   ============================================= */

const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8000/api'
  : 'https://ecosphere-fec3.onrender.com/api';

// ── Auth token ────────────────────────────────────
function getToken() { return localStorage.getItem('ecosphere_token'); }
function setToken(t) { localStorage.setItem('ecosphere_token', t); }
function clearToken()  { localStorage.removeItem('ecosphere_token'); localStorage.removeItem('ecosphere_user'); }

function authHeaders() {
  const t = getToken();
  return t ? { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' }
           : { 'Content-Type': 'application/json' };
}

// ── Core fetch wrapper ─────────────────────────────
async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: authHeaders(),
      ...options,
    });
    if (res.status === 204) return null;

    if (res.status === 401) {
      AuthAPI.logout();
      throw new Error('Session expired. Please log in again.');
    }

    let data;
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await res.json();
    } else {
      // Not JSON (likely HTML error page)
      const text = await res.text();
      throw new Error('Unexpected response from server. Please check backend logs.\n' + text.substring(0, 200));
    }
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  } catch (e) {
    throw e;
  }
}

// ── Auth API ──────────────────────────────────────
const AuthAPI = {
  async register(payload) {
    const data = await apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(payload) });
    setToken(data.access_token);
    localStorage.setItem('ecosphere_user', JSON.stringify(data.user));
    return data;
  },
  async login(email, password) {
    const data = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    setToken(data.access_token);
    localStorage.setItem('ecosphere_user', JSON.stringify(data.user));
    return data;
  },
  async me() {
    return await apiFetch('/auth/me');
  },
  logout() {
    clearToken();
    showToast('Logged out successfully', 'info');
    setTimeout(() => window.location.reload(), 500);
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem('ecosphere_user')); }
    catch { return null; }
  },
  isLoggedIn() { return !!getToken(); }
};

// ── Listings API ──────────────────────────────────
const ListingsAPI = {
  async getAll(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return await apiFetch(`/listings/${qs ? '?' + qs : ''}`);
  },
  async getOne(id) { return await apiFetch(`/listings/${id}`); },
  // ── Admin Endpoints ──────────────────────────────────
  getAdminStats: () => apiFetch('/admin/stats'),
  getPendingListings: () => apiFetch('/admin/listings/pending'),
  getAllListings: () => apiFetch('/admin/listings/all'),
  verifyListing: (id, note = "") => apiFetch(`/admin/listings/${id}/verify`, { method: 'POST', body: JSON.stringify({ note }) }),
  rejectListing: (id, note = "") => apiFetch(`/admin/listings/${id}/reject`, { method: 'POST', body: JSON.stringify({ note }) }),
  getAllUsers: () => apiFetch('/admin/users'),
  verifyUser: (id) => apiFetch(`/admin/users/${id}/verify`, { method: 'POST' }),
  bootstrapAdmin: (email, secret) => apiFetch('/admin/bootstrap', { method: 'POST', body: JSON.stringify({ email, secret }) }),
  async create(payload) {
    return await apiFetch('/listings/', { method: 'POST', body: JSON.stringify(payload) });
  },
  async update(id, payload) {
    return await apiFetch(`/listings/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
  },
  async delete(id) {
    return await apiFetch(`/listings/${id}`, { method: 'DELETE' });
  },
  async myListings() { return await apiFetch('/listings/my/listings'); },
};

// ── Quotes API ────────────────────────────────────
const QuotesAPI = {
  async send(listingId, message, quantityNeeded) {
    return await apiFetch('/quotes/', {
      method: 'POST',
      body: JSON.stringify({ listing_id: listingId, message, quantity_needed: quantityNeeded })
    });
  },
  async mySent()     { return await apiFetch('/quotes/sent'); },
  async myReceived() { return await apiFetch('/quotes/received'); },
  async updateStatus(quoteId, status) {
    return await apiFetch(`/quotes/${quoteId}/status`, {
      method: 'PUT', body: JSON.stringify({ status })
    });
  },
  async rate(quoteId, rating, role) {
    return await apiFetch(`/quotes/${quoteId}/rate`, {
      method: 'POST', body: JSON.stringify({ rating, role })
    });
  },
};

// ── Green Score API ───────────────────────────────
const GreenScoreAPI = {
  async me()          { return await apiFetch('/greenscore/me'); },
  async leaderboard() { return await apiFetch('/greenscore/leaderboard'); },
  async stats()       { return await apiFetch('/greenscore/stats'); },
  async submitCompliance(docType, file) {
    const formData = new FormData();
    formData.append('file', file);
    return await apiFetch(`/greenscore/compliance-upload?doc_type=${encodeURIComponent(docType)}`, {
      method: 'POST',
      body: formData,
      headers: { 'Authorization': `Bearer ${getToken()}` } // Overriding Content-Type to allow browser to set boundary
    });
  },
};

// ── AI API ────────────────────────────────────────
const AIAPI = {
  async match(wasteName, category, quantity, description) {
    return await apiFetch('/ai/match', {
      method: 'POST',
      body: JSON.stringify({ waste_name: wasteName, category, quantity, description })
    });
  },
  async generateDescription(wasteName, category) {
    return await apiFetch('/ai/generate-description', {
      method: 'POST',
      body: JSON.stringify({ waste_name: wasteName, category })
    });
  },
  async insights(wasteName, category) {
    return await apiFetch('/ai/insights', {
      method: 'POST',
      body: JSON.stringify({ waste_name: wasteName, category })
    });
  },
};

// ─── Marketplace Quote Logic ──────────────────────
async function requestQuoteBackend(listingId, title, company) {
  if (!AuthAPI.isLoggedIn()) {
    openAuthModal('login');
    showToast('Please log in to send a quote request', 'info');
    return;
  }
  try {
    const res = await QuotesAPI.send(listingId, `Interested in ${title}`, "1");
    showToast(`Quote request for "${title}" sent to ${company}!`, 'success');
  } catch (e) {
    let errorMsg = '';
    if (e && typeof e === 'object' && e.message) {
      errorMsg = e.message;
    } else {
      try {
        errorMsg = JSON.stringify(e);
      } catch {
        errorMsg = String(e);
      }
    }
    console.error('Quote request error:', e);
    showToast(`Failed to send quote: ${errorMsg}`, 'error');
  }
}

// ── Backend-aware overrides ────────────────────────
// These replace the localStorage-only versions in app.js when backend is available

async function loadMarketplaceFromBackend(category) {
  try {
    const params = {};
    if (category && category !== 'All') params.category = category;
    const listings = await ListingsAPI.getAll(params);
    if (listings && listings.length > 0) {
      APP.listings = listings.map(l => ({
        id: l.id, title: l.title, category: l.category, qty: l.quantity,
        price: l.price_per_unit, unit: l.unit, location: l.location,
        company: l.company_name || 'Unknown', desc: l.description,
        greenPts: l.green_pts_value, verified: l.is_verified,
        date: l.created_at?.split('T')[0] || new Date().toISOString().split('T')[0]
      }));
      
      // Override render function to use backend-linked quotes
      const user = await AuthAPI.me();
      const authLinks = document.getElementById('auth-links');
      if (authLinks && user) {
        authLinks.innerHTML = `
          ${user.is_admin ? '<a href="#admin" class="nav-link admin-btn" style="color:var(--green-600); font-weight:700;">Admin Panel</a>' : ''}
          <a href="#dashboard" class="nav-link">Dashboard</a>
          <button onclick="handleLogout()" class="btn btn-outline">Logout</button>
        `;
      }
      const grid = document.getElementById('marketplace-grid');
      if (grid) {
        grid.innerHTML = APP.listings.map(l => `
          <div class="listing-card card-hover" onclick="showListingDetail(${l.id})">
            <div class="listing-card-body">
              <div class="listing-card-header">
                <span class="badge ${getCategoryBadgeClass(l.category)}">${l.category}</span>
                ${l.verified ? '<div class="listing-verified"><svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6L5 9L10 3" stroke="#1e7a3e" stroke-width="1.8" stroke-linecap="round"/></svg></div>' : ''}
              </div>
              <div class="listing-title">${l.title}</div>
              <div class="listing-company">${l.company}</div>
              <div class="listing-meta">
                <div class="listing-meta-row"><svg width="14" height="14" fill="none" viewBox="0 0 14 14"><circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.2"/><path d="M7 4v3l2 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg> ${l.qty} available</div>
                <div class="listing-meta-row"><svg width="14" height="14" fill="none" viewBox="0 0 14 14"><path d="M7 1C4.8 1 3 2.8 3 5c0 3.5 4 8 4 8s4-4.5 4-8c0-2.2-1.8-4-4-4z" stroke="currentColor" stroke-width="1.2"/><circle cx="7" cy="5" r="1.5" fill="currentColor"/></svg> ${l.location}</div>
              </div>
              <div class="listing-divider"></div>
              <div class="listing-footer">
                <div><div class="listing-price">₹${l.price}/${l.unit || 'kg'}</div><div class="listing-price-sub">${l.company}</div></div>
                <div class="green-pts-badge">🌿 +${l.greenPts} pts</div>
              </div>
              <button class="btn btn-primary btn-md" style="width:100%;margin-top:12px;" 
                onclick="event.stopPropagation(); requestQuoteBackend(${l.id}, '${l.title.replace(/'/g,"\\'")}', '${l.company.replace(/'/g,"\\'")}')">
                Request Quote
              </button>
            </div>
          </div>
        `).join('');
      }
    }

  } catch (e) {
    // Backend not running — silently use localStorage data
    console.log('Backend unavailable, using local data');
  }
}

async function submitListingToBackend() {
  const title    = document.getElementById('sell-title').value.trim();
  const category = document.getElementById('sell-category').value;
  const qty      = document.getElementById('sell-qty').value.trim();
  const price    = document.getElementById('sell-price').value;
  const location = document.getElementById('sell-location').value.trim();
  const desc     = document.getElementById('sell-desc').value.trim();

  if (!title || !category || !qty || !price || !location) {
    showToast('Please fill all required fields', 'error'); return;
  }

  if (!AuthAPI.isLoggedIn()) {
    // Fall back to local-only submit
    submitListing(); return;
  }

  try {
    const listing = await ListingsAPI.create({
      title, category, quantity: qty, price_per_unit: parseFloat(price),
      location, description: desc || undefined
    });
    showToast(`"${listing.title}" listed! +45 Green Points earned 🌿`, 'success');
    document.getElementById('sell-form').reset();
    setTimeout(() => navigate('marketplace'), 1500);
  } catch (e) {
    showToast(`Error: ${e.message}`, 'error');
  }
}

async function runAIMatcherBackend() {
  const wasteName = document.getElementById('matcher-name').value.trim();
  const category  = document.getElementById('matcher-cat').value;
  const qty       = document.getElementById('matcher-qty').value.trim();
  const desc      = document.getElementById('matcher-desc').value.trim();

  if (!wasteName || !category) { showToast('Please enter waste name and category', 'error'); return; }

  const btn = document.getElementById('matcher-btn');
  btn.disabled = true;
  const thinking = document.getElementById('matcher-thinking');
  thinking.classList.add('show');
  document.getElementById('matcher-results').innerHTML = '';
  document.getElementById('matcher-reasoning').style.display = 'none';

  const msgs = ['Scanning registered buyers…','Checking compliance certifications…','Calculating CO₂ impact…','Ranking by match confidence…'];
  let ti = 0;
  const tInt = setInterval(() => { document.getElementById('thinking-msg').textContent = msgs[ti++ % msgs.length]; }, 700);

  try {
    const res = await AIAPI.match(wasteName, category, qty, desc);
    clearInterval(tInt);
    thinking.classList.remove('show');
    btn.disabled = false;

    const reasoningBox = document.getElementById('matcher-reasoning');
    reasoningBox.style.display = 'block';
    reasoningBox.innerHTML = `<strong>🤖 AI Analysis${res.used_real_ai ? ' (Gemini)' : ' (Demo)'}:</strong> ${res.reasoning_summary}`;

    const resultsEl = document.getElementById('matcher-results');
    resultsEl.innerHTML = res.matches.map((m, i) => `
      <div class="match-result-card ${i === 0 ? 'top' : ''}">
        ${i === 0 ? '<div class="match-top-ribbon">⭐ BEST MATCH</div>' : ''}
        <div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:10px;">
          <div class="match-score-circle">
            <span class="match-score-num">${m.score}</span>
            <span class="match-score-pct">match%</span>
          </div>
          <div style="flex:1;min-width:0;">
            <div style="font-family:var(--font-head);font-size:16px;font-weight:700;">${m.company}</div>
            <div style="font-size:13px;color:var(--text-muted);">${m.type} · ${m.location}</div>
            <div style="font-size:12px;color:var(--green-700);margin-top:3px;">🌿 ${m.co2_saved}</div>
          </div>
        </div>
        <div class="match-bar"><div class="match-bar-fill" style="width:${m.score}%"></div></div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 8px;">
          ${(m.tags||[]).map(t=>`<span class="badge badge-green">${t}</span>`).join('')}
          <span class="badge badge-blue">${m.price_range}</span>
          <span class="badge badge-gray">${m.compliance}</span>
        </div>
        <button class="btn btn-primary btn-sm" style="width:100%;margin-top:8px;"
          onclick="showToast('Quote request sent to ${m.company}! They will respond within 24 hours.','success')">
          📧 Send Quote Request
        </button>
      </div>
    `).join('');
  } catch (e) {
    clearInterval(tInt);
    thinking.classList.remove('show');
    btn.disabled = false;
    console.warn('AI Matcher backend error:', e.message);
    showToast('AI service unavailable — showing curated matches', 'info');
    // Show fallback message instead of crashing
    const reasoningBox = document.getElementById('matcher-reasoning');
    reasoningBox.style.display = 'block';
    reasoningBox.innerHTML = `<strong>🤖 Curated Matches:</strong> Showing verified buyers for ${wasteName || category}. Add your Gemini API key in <code>.env</code> for live AI matching.`;
    // Leave results empty so user knows to try again; don't crash
    document.getElementById('matcher-results').innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔌</div><p>Backend AI unavailable. Check that your <code>GEMINI_API_KEY</code> is set in <code>ecoloop-backend/.env</code> and restart the server.</p></div>`;
  }
}

async function aiSuggestDescBackend() {
  const title    = document.getElementById('sell-title').value.trim();
  const category = document.getElementById('sell-category').value;
  if (!title) { showToast('Enter waste name first', 'error'); return; }
  const btn = document.getElementById('ai-desc-btn');
  btn.disabled = true; btn.textContent = '✨ Generating…';
  try {
    const res = await AIAPI.generateDescription(title, category);
    if (res.description) {
      document.getElementById('sell-desc').value = res.description;
      showToast('AI description generated!', 'success');
    } else {
      await aiSuggestDesc(); // fall back to client-side
    }
  } catch { await aiSuggestDesc(); }
  btn.disabled = false; btn.textContent = '✨ AI Generate Description';
}

async function getWasteInsightBackend() {
  const category = document.getElementById('matcher-cat').value;
  const name     = document.getElementById('matcher-name').value.trim();
  if (!name && !category) { showToast('Enter waste details first', 'error'); return; }
  const btn = document.getElementById('insight-btn');
  btn.disabled = true; btn.textContent = '🔍 Analyzing…';
  try {
    const res = await AIAPI.insights(name || category, category || 'General Waste');
    if (res.insights) {
      document.getElementById('insight-box').style.display = 'block';
      document.getElementById('insight-text').innerHTML = res.insights.replace(/\n/g,'<br>');
    } else { await getWasteInsight(); }
  } catch { await getWasteInsight(); }
  btn.disabled = false; btn.textContent = '🔍 Get AI Insights';
}

async function loadGreenScoreFromBackend() {
  if (!AuthAPI.isLoggedIn()) return;
  try {
    const data = await GreenScoreAPI.me();
    if (!data) return;
    // Update scoreData with real server values
    scoreData.criteria[0].pts = data.score.waste_listed_pts;
    scoreData.criteria[1].pts = data.score.exchange_pts;
    scoreData.criteria[2].pts = data.score.co2_pts;
    scoreData.criteria[3].pts = data.score.compliance_pts;
    scoreData.criteria[4].pts = data.score.rating_pts;
    scoreData.criteria[5].pts = data.score.zero_waste_pts;
    if (data.recent_events?.length) {
      scoreData.activity = data.recent_events.map(e => ({
        text: e.reason, pts: `+${e.pts}`,
        date: new Date(e.date).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' })
      }));
    }
    renderGreenScore();
    // score-num is already updated by renderGreenScore via scoreData, but backend total overrides local calc
    const numEl = document.getElementById('score-num');
    if (numEl) numEl.textContent = data.score.total;
  } catch { /* use local fallback */ }
}

async function loadLeaderboardFromBackend() {
  if (!AuthAPI.isLoggedIn()) return;
  try {
    const entries = await GreenScoreAPI.leaderboard();
    if (!entries || !entries.length) return;
    const el = document.getElementById('leaderboard-list');
    if (!el) return;
    el.innerHTML = entries.map(s => {
      const rankClass = s.rank===1?'rank-1':s.rank===2?'rank-2':s.rank===3?'rank-3':'rank-other';
      const tierClass = s.tier==='Gold'?'tier-gold':s.tier==='Silver'?'tier-silver':'tier-bronze';
      return `
        <div class="leaderboard-row ${s.is_you?'you':''}">
          <div class="rank-badge ${rankClass}">${s.rank}</div>
          <div class="company-avatar">${s.initials}</div>
          <div style="flex:1;min-width:0;">
            <div style="font-family:var(--font-head);font-size:14px;font-weight:700;">${s.company_name}${s.is_you?' <span style="color:var(--green-600);font-size:12px;">(You)</span>':''}</div>
            <div style="font-size:12px;color:var(--text-muted);">${s.location||''} · ${s.industry||''}</div>
          </div>
          <span class="tier-pill ${tierClass}">${s.tier}</span>
          <div style="font-family:var(--font-head);font-size:15px;font-weight:800;color:var(--green-700);min-width:60px;text-align:right;">${s.score}</div>
        </div>`;
    }).join('');
  } catch { renderLeaderboard(); }
}

// ── Auth modal helpers ─────────────────────────────
function openAuthModal(mode = 'login') {
  document.getElementById('auth-modal').classList.add('show');
  switchAuthTab(mode);
}
function closeAuthModal() { document.getElementById('auth-modal').classList.remove('show'); }
function switchAuthTab(tab) {
  document.getElementById('auth-login-form').style.display = tab==='login'?'block':'none';
  document.getElementById('auth-register-form').style.display = tab==='register'?'block':'none';
  document.getElementById('auth-tab-login').classList.toggle('active', tab==='login');
  document.getElementById('auth-tab-register').classList.toggle('active', tab==='register');
}

async function doLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  if (!email || !password) { showToast('Enter email and password', 'error'); return; }
  const btn = document.getElementById('login-btn');
  btn.disabled = true; btn.textContent = 'Logging in…';
  try {
    await AuthAPI.login(email, password);
    closeAuthModal();
    updateNavAuth();
    showToast('Welcome back! 🌿', 'success');
    await loadGreenScoreFromBackend();
  } catch (e) { showToast(e.message, 'error'); }
  btn.disabled = false; btn.textContent = 'Log In';
}

async function doRegister() {
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const company  = document.getElementById('reg-company').value.trim();
  const location = document.getElementById('reg-location').value.trim();
  if (!email || !password || !company) { showToast('Fill all required fields', 'error'); return; }
  const btn = document.getElementById('register-btn');
  btn.disabled = true; btn.textContent = 'Creating account…';
  try {
    await AuthAPI.register({ email, password, company_name: company, location });
    closeAuthModal();
    updateNavAuth();
    showToast(`Welcome to EcoSphere, ${company}! 🌿 +30 Green Points earned`, 'success');
  } catch (e) { showToast(e.message, 'error'); }
  btn.disabled = false; btn.textContent = 'Create Account';
}

function updateNavAuth() {
  const user = AuthAPI.getUser();
  const loginBtn = document.getElementById('nav-login-btn');
  const userChip = document.getElementById('nav-user-chip');
  if (user) {
    if (loginBtn) loginBtn.style.display = 'none';
    if (userChip) {
      userChip.style.display = 'flex';
      userChip.querySelector('.chip-name').textContent = user.company_name.split(' ')[0];
    }
  } else {
    if (loginBtn) loginBtn.style.display = '';
    if (userChip) userChip.style.display = 'none';
  }
}

// ── Wire backend calls into navigate ──────────────
const _origNavigate = navigate;
window.navigate = async function(page) {
  _origNavigate(page);
  if (page === 'marketplace') await loadMarketplaceFromBackend(null);
  if (page === 'greenscore')  await loadGreenScoreFromBackend();
  if (page === 'leaderboard') await loadLeaderboardFromBackend();
};

// Overall UI overrides
document.addEventListener('DOMContentLoaded', () => {
  updateNavAuth();
  
  // Replace button handlers
  const matcherBtn = document.getElementById('matcher-btn');
  if (matcherBtn) matcherBtn.onclick = runAIMatcherBackend;
  
  const aiDescBtn = document.getElementById('ai-desc-btn');
  if (aiDescBtn) aiDescBtn.onclick = aiSuggestDescBackend;
  
  const insightBtn = document.getElementById('insight-btn');
  if (insightBtn) insightBtn.onclick = getWasteInsightBackend;

  const sellBtn = document.querySelector('button[onclick="submitListing()"]');
  if (sellBtn) sellBtn.onclick = submitListingToBackend;

  // marketplace items are rendered dynamically, so we handle quote requests via delegation or updating render
});

// ── Global Handlers for HTML ───────────────────────
function handleLogout() { AuthAPI.logout(); }
function handleLogin()  { doLogin(); }
function handleRegister() { doRegister(); }

// ── Admin Panel Extras ──────────────
// Injected into global scope if needed by dashboard
window.handleVerifyListing = async (id) => {
  if (confirm('Verify listing contents?')) {
    try {
      await ListingsAPI.verifyListing(id, "Content verified by EcoSphere Admin");
      showToast('Listing verified!', 'success');
      if (typeof renderAdmin === 'function') renderAdmin();
    } catch (e) { showToast(e.message, 'error'); }
  }
};
window.handleRejectListing = async (id) => {
  if (confirm('Reject this listing?')) {
    try {
      await ListingsAPI.rejectListing(id, "Does not meet quality standards");
      showToast('Listing rejected', 'info');
      if (typeof renderAdmin === 'function') renderAdmin();
    } catch (e) { showToast(e.message, 'error'); }
  }
};

