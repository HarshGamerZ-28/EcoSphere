/* =============================================
   ECOSPHERE — Main App JS
   Gemini AI Integration + App Logic
   ============================================= */

// ─── State ───────────────────────────────────────
const APP = {
  currentPage: 'home',
  listings: JSON.parse(localStorage.getItem('ecosphere_listings') || 'null') || getDefaultListings(),
  greenScores: JSON.parse(localStorage.getItem('ecosphere_scores') || 'null') || getDefaultScores(),
  userCompany: localStorage.getItem('ecosphere_company') || 'TechPlast Industries',
};

// ─── Toast System ──────────────────────────────────
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
      <span class="toast-msg">${message}</span>
    </div>
  `;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '1'; toast.style.transform = 'translateY(0)'; }, 10);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ─── Green Score State ─────────────────────────────
const scoreData = {
  criteria: [
    { name: 'Waste listed on platform', pts: 180, max: 200 },
    { name: 'Successful exchanges completed', pts: 240, max: 300 },
    { name: 'CO₂ emissions avoided', pts: 120, max: 200 },
    { name: 'Compliance documents uploaded', pts: 80, max: 100 },
    { name: 'Buyer/seller rating avg (4.2★)', pts: 84, max: 100 },
    { name: 'Zero-waste goal progress', pts: 16, max: 100 },
  ],
  activity: [
    { text: 'Listed 500kg HDPE Granules on marketplace', pts: '+45', date: 'Apr 13, 2026' },
    { text: 'Exchange completed with GreenMetal Inc — 1,200kg Aluminum', pts: '+120', date: 'Apr 10, 2026' },
    { text: 'GST & MSME compliance documents verified', pts: '+40', date: 'Apr 8, 2026' },
    { text: 'Received 5★ rating from FabricFirst Pvt Ltd', pts: '+20', date: 'Apr 6, 2026' },
    { text: 'Used AI Matcher — submitted 3 quote requests', pts: '+25', date: 'Apr 3, 2026' },
    { text: 'Company profile completed (100%)', pts: '+30', date: 'Mar 28, 2026' },
  ]
};

function awardGreenPoints(pts, reason) {
  if (!scoreData) return;
  scoreData.criteria[0].pts = Math.min(scoreData.criteria[0].pts + Math.floor(pts * 0.3), 200);
  scoreData.activity.unshift({ text: reason, pts: '+' + pts, date: 'Just now' });
  if (scoreData.activity.length > 10) scoreData.activity.pop();
  if (APP.currentPage === 'greenscore') renderGreenScore();
}


// ─── Router ──────────────────────────────────────
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  const el = document.getElementById('page-' + page);
  if (el) { el.classList.add('active'); APP.currentPage = page; }
  const navEl = document.querySelector(`[data-page="${page}"]`);
  if (navEl) navEl.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (page === 'marketplace') renderMarketplace();
  if (page === 'greenscore') renderGreenScore();
  if (page === 'leaderboard') renderLeaderboard();
  if (page === 'admin') renderAdmin();
}

// ─── Default Data ─────────────────────────────────
function getDefaultListings() {
  return [
    { id: 1, title: 'HDPE Granules', category: 'Plastic Scrap', qty: '500 kg', price: 45, unit: 'kg', location: 'Mumbai, Maharashtra', company: 'TechPlast Industries', desc: 'Food-grade HDPE granules from manufacturing process. High purity, clean material.', greenPts: 45, verified: true, date: '2026-04-13' },
    { id: 2, title: 'Aluminum Chips', category: 'Metal Waste', qty: '1,200 kg', price: 120, unit: 'kg', location: 'Pune, Maharashtra', company: 'MetalWorks Ltd.', desc: 'Aluminum machining chips from CNC operations. No coolant contamination.', greenPts: 92, verified: true, date: '2026-04-12' },
    { id: 3, title: 'Glycerin (Industrial)', category: 'Chemical Byproduct', qty: '800 L', price: 35, unit: 'kg', location: 'Chennai, Tamil Nadu', company: 'ChemSynth Corp', desc: 'Industrial glycerin byproduct from biodiesel production. 85% purity.', greenPts: 60, verified: true, date: '2026-04-11' },
    { id: 4, title: 'Cotton Scraps', category: 'Textile Waste', qty: '350 kg', price: 25, unit: 'kg', location: 'Surat, Gujarat', company: 'FabricFirst Pvt Ltd', desc: 'Cotton fabric offcuts from garment manufacturing. Mixed colors, clean material.', greenPts: 28, verified: true, date: '2026-04-10' },
    { id: 5, title: 'PCB Boards (Scrap)', category: 'Electronic Waste', qty: '200 kg', price: 180, unit: 'kg', location: 'Bangalore, Karnataka', company: 'CircuitTech', desc: 'End-of-life PCB boards with recoverable precious metals. CPCB compliant collection.', greenPts: 150, verified: true, date: '2026-04-09' },
    { id: 6, title: 'Cardboard Scrap', category: 'Paper Waste', qty: '2,000 kg', price: 12, unit: 'kg', location: 'Delhi NCR', company: 'PackRight Solutions', desc: 'Corrugated cardboard manufacturing waste. Dry, clean, baled and ready for pickup.', greenPts: 18, verified: false, date: '2026-04-08' },
  ];
}

function getDefaultScores() {
  return [
    { company: 'GreenMetal Inc', location: 'Pune', category: 'Metal Recycling', score: 980, tier: 'Gold', initials: 'GM' },
    { company: 'ChemSynth Corp', location: 'Chennai', category: 'Chemical', score: 910, tier: 'Gold', initials: 'CS' },
    { company: 'FabricFirst Pvt Ltd', location: 'Surat', category: 'Textile', score: 875, tier: 'Gold', initials: 'FF' },
    { company: 'CircuitTech', location: 'Bangalore', category: 'E-Waste', score: 820, tier: 'Gold', initials: 'CT' },
    { company: 'AgriLoop Biotech', location: 'Nashik', category: 'Organic', score: 790, tier: 'Silver', initials: 'AL' },
    { company: 'BioRefine Labs', location: 'Hyderabad', category: 'Chemical', score: 760, tier: 'Silver', initials: 'BL' },
    { company: 'PlasCycle India', location: 'Pune', category: 'Plastics', score: 740, tier: 'Silver', initials: 'PI' },
    { company: 'MetalWorks Ltd.', location: 'Pune', category: 'Metal', score: 730, tier: 'Silver', initials: 'MW' },
    { company: 'TyreRecycle India', location: 'Chennai', category: 'Rubber', score: 715, tier: 'Silver', initials: 'TR' },
    { company: 'AlloyWorks Ltd', location: 'Rajkot', category: 'Metal', score: 705, tier: 'Silver', initials: 'AW' },
    { company: 'PackRight Solutions', location: 'Delhi NCR', category: 'Packaging', score: 690, tier: 'Silver', initials: 'PR' },
    { company: localStorage.getItem('ecosphere_company') || 'TechPlast Industries', location: 'Mumbai', category: 'Plastics', score: 720, tier: 'Silver', initials: 'TP', isYou: true },
  ].sort((a, b) => b.score - a.score);
}

// ─── AI Functions ─────────────────────────────────
// (Moved to backend proxy in api.js)

// ─── Marketplace ──────────────────────────────────
let activeFilter = 'All';

function renderMarketplace(filter) {
  if (filter !== undefined) activeFilter = filter;
  const grid = document.getElementById('marketplace-grid');
  if (!grid) return;
  const filtered = activeFilter === 'All' ? APP.listings : APP.listings.filter(l => l.category === activeFilter);
  
  if (filtered.length === 0) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="empty-state-icon">📦</div><p>No listings in this category yet.</p><button class="btn btn-primary btn-md" style="margin-top:12px;" onclick="navigate('sell')">List Your Waste</button></div>`;
    return;
  }

  grid.innerHTML = filtered.map(l => `
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
          <div><div class="listing-price">₹${l.price}/${l.unit}</div><div class="listing-price-sub">${l.company}</div></div>
          <div class="green-pts-badge">🌿 +${l.greenPts} pts</div>
        </div>
        <button class="btn btn-primary btn-md" style="width:100%;margin-top:12px;" onclick="event.stopPropagation();requestQuote('${l.title}','${l.company}')">Request Quote</button>
      </div>
    </div>
  `).join('');
}

function getCategoryBadgeClass(cat) {
  const map = { 'Plastic Scrap': 'badge-blue', 'Metal Waste': 'badge-amber', 'Chemical Byproduct': 'badge-purple', 'Textile Waste': 'badge-pink', 'Electronic Waste': 'badge-red', 'Paper Waste': 'badge-gray', 'Organic Waste': 'badge-green', 'Rubber / Polymer': 'badge-amber' };
  return map[cat] || 'badge-green';
}

function filterMarketplace(btn, filter) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // If backend loader is available and logged in, use it; otherwise use local filter
  if (typeof loadMarketplaceFromBackend === 'function') {
    loadMarketplaceFromBackend(filter === 'All' ? null : filter);
  } else {
    renderMarketplace(filter);
  }
}

function requestQuote(title, company) {
  // Try backend version first (will check if logged in)
  if (typeof requestQuoteBackend === 'function') {
    requestQuoteBackend(null, title, company);
  } else {
    showToast(`Quote request for "${title}" sent to ${company}! They'll respond within 24 hours.`, 'success');
    awardGreenPoints(5, 'Sent quote request for ' + title);
  }
}

function showListingDetail(id) {
  const l = APP.listings.find(x => x.id === id);
  if (!l) return;
  showToast(`Viewing "${l.title}" — ₹${l.price}/${l.unit} from ${l.company}`, 'info');
}

// ─── Sell Waste Form ───────────────────────────────
function submitListing() {
  const title = document.getElementById('sell-title').value.trim();
  const category = document.getElementById('sell-category').value;
  const qty = document.getElementById('sell-qty').value.trim();
  const price = document.getElementById('sell-price').value;
  const location = document.getElementById('sell-location').value.trim();
  const desc = document.getElementById('sell-desc').value.trim();

  if (!title || !category || !qty || !price || !location) {
    showToast('Please fill all required fields', 'error'); return;
  }

  const newListing = {
    id: Date.now(),
    title, category, qty, price: parseFloat(price), unit: 'kg',
    location, company: APP.userCompany,
    desc: desc || 'Industrial waste material available for circular economy use.',
    greenPts: Math.floor(parseFloat(price) * 0.8 + 20),
    verified: false,
    date: new Date().toISOString().split('T')[0]
  };

  APP.listings.unshift(newListing);
  localStorage.setItem('ecosphere_listings', JSON.stringify(APP.listings));

  awardGreenPoints(45, 'Listed "' + title + '" on marketplace');
  showToast(`"${title}" listed successfully! You earned 45 Green Points 🌿`, 'success');

  document.getElementById('sell-form').reset();
  setTimeout(() => navigate('marketplace'), 1500);
}

async function aiSuggestDesc() {
  const title = document.getElementById('sell-title').value.trim();
  const category = document.getElementById('sell-category').value;
  if (!title) { showToast('Enter waste name first', 'error'); return; }
  
  const descEl = document.getElementById('sell-desc');
  descEl.placeholder = "AI is thinking...";
  showToast('Generating professional description...', 'info');

  // Generic fallback if AI fails
  const fallback = `High-quality ${title} sourced from industrial ${category.toLowerCase() || 'processes'}. This material is clean, sorted, and ready for reuse in manufacturing or upcycling. Ideal for companies looking to improve their circular economy footprint through verified secondary raw materials.`;
  
  // This will be overridden by aiSuggestDescBackend if api.js is loaded
  setTimeout(() => {
    if (!descEl.value) {
      descEl.value = fallback;
      showToast('Generated professional template!', 'success');
    }
  }, 2000);
}

// ─── Green Score Rendering ──────────────────────────

function renderGreenScore() {
  const totalPts = scoreData.criteria.reduce((s, c) => s + c.pts, 0);
  const maxPts = 1000;
  const pct = Math.round((totalPts / maxPts) * 100);
  const dash = 263;
  const offset = dash - (dash * totalPts / maxPts);

  const ringEl = document.getElementById('score-ring-fill');
  if (ringEl) { ringEl.style.strokeDashoffset = offset; }
  const numEl = document.getElementById('score-num');
  if (numEl) numEl.textContent = totalPts;
  const pctEl = document.getElementById('score-pct-bar');
  if (pctEl) pctEl.style.width = pct + '%';

  const critEl = document.getElementById('criteria-list');
  if (critEl) {
    critEl.innerHTML = scoreData.criteria.map(c => `
      <div class="criteria-item">
        <div class="criteria-label">${c.name}</div>
        <div class="criteria-progress"><div class="criteria-fill" style="width:${Math.round(c.pts/c.max*100)}%"></div></div>
        <div class="criteria-pts">${c.pts} / ${c.max}</div>
      </div>
    `).join('');
  }

  const actEl = document.getElementById('activity-list');
  if (actEl) {
    actEl.innerHTML = scoreData.activity.map(a => `
      <div class="activity-item">
        <div class="activity-dot"></div>
        <div style="flex:1"><div class="activity-text">${a.text}</div><div class="activity-date">${a.date}</div></div>
        <div class="activity-pts">${a.pts} pts</div>
      </div>
    `).join('');
  }
}



// ─── Leaderboard ──────────────────────────────────
function renderLeaderboard() {
  const scores = getDefaultScores().sort((a, b) => b.score - a.score);
  const el = document.getElementById('leaderboard-list');
  if (!el) return;

  el.innerHTML = scores.map((s, i) => {
    const rankClass = i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : i === 2 ? 'rank-3' : 'rank-other';
    const tierClass = s.tier === 'Gold' ? 'tier-gold' : s.tier === 'Silver' ? 'tier-silver' : 'tier-bronze';
    return `
      <div class="leaderboard-row ${s.isYou ? 'you' : ''}">
        <div class="rank-badge ${rankClass}">${i + 1}</div>
        <div class="company-avatar">${s.initials}</div>
        <div style="flex:1;min-width:0;">
          <div style="font-family:var(--font-head);font-size:14px;font-weight:700;">${s.company}${s.isYou ? ' <span style="color:var(--green-600);font-size:12px;">(You)</span>' : ''}</div>
          <div style="font-size:12px;color:var(--text-muted);">${s.location} · ${s.category}</div>
        </div>
        <span class="tier-pill ${tierClass}">${s.tier}</span>
        <div style="font-family:var(--font-head);font-size:15px;font-weight:800;color:var(--green-700);min-width:60px;text-align:right;">${s.score}</div>
      </div>
    `;
  }).join('');
}

// ─── AI Modal logic removed ──────────────────────

// ─── AI Insights ──────────────────────────────────
async function getWasteInsight() {
  const category = document.getElementById('matcher-cat').value;
  const name = document.getElementById('matcher-name').value.trim();
  if (!name && !category) { showToast('Enter waste details first', 'error'); return; }
  showToast('Connecting to AI insights service...', 'info');
}

// ─── Circular Economy Section ─────────────────────
function initEconomyAnimation() {
  const items = document.querySelectorAll('.economy-node');
  items.forEach((node, i) => {
    node.style.animationDelay = `${i * 0.15}s`;
  });
}

// ─── Newsletter ───────────────────────────────────
function subscribeNewsletter(inputId) {
  const email = document.getElementById(inputId)?.value?.trim();
  if (!email || !email.includes('@')) { showToast('Enter a valid email address', 'error'); return; }
  showToast('Subscribed! You\'ll get the latest listings and industry news 📬', 'success');
  if (document.getElementById(inputId)) document.getElementById(inputId).value = '';
}

// ─── Admin Dashboard ──────────────────────────────
async function renderAdmin() {
  const statsGrid = document.getElementById('admin-stats');
  const listEl = document.getElementById('admin-listings');
  const userEl = document.getElementById('admin-users');
  
  if (!statsGrid || !listEl) return;
  
  try {
    const stats = await ListingsAPI.getAdminStats();
    statsGrid.innerHTML = `
      <div class="stat-card"><h3>${stats.pending_verification || 0}</h3><p>Pending Verifications</p></div>
      <div class="stat-card"><h3>${stats.total_users || 0}</h3><p>Total Companies</p></div>
      <div class="stat-card"><h3>${stats.total_quotes || 0}</h3><p>Quote Requests</p></div>
      <div class="stat-card"><h3>₹${((stats.revenue_paise || 0) / 100).toLocaleString()}</h3><p>Total Revenue</p></div>
    `;

    const pending = await ListingsAPI.getPendingListings();
    listEl.innerHTML = pending && pending.length ? pending.map(l => `
      <div class="admin-item" style="padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong style="display:block;">${l.title}</strong>
          <small>${l.owner_company} | ${l.category}</small>
        </div>
        <div style="display:flex; gap:10px;">
          <button class="btn btn-sm btn-primary" onclick="handleVerifyListing(${l.id})">Verify</button>
          <button class="btn btn-sm btn-outline" style="color:red;" onclick="handleRejectListing(${l.id})">Reject</button>
        </div>
      </div>
    `).join('') : '<p style="padding:20px; color:#666;">No pending listings! 🎉</p>';

    const users = await ListingsAPI.getAllUsers();
    userEl.innerHTML = users && users.length ? users.slice(0, 10).map(u => `
      <div class="admin-item" style="padding:10px; border-bottom:1px solid #eee; font-size:13px;">
        <strong>${u.company_name}</strong><br>
        <span style="color:#666;">${u.email}</span>
      </div>
    `).join('') : '<p style="padding:10px;">No users yet.</p>';

  } catch (err) {
    console.error('Admin Panel Error:', err);
    statsGrid.innerHTML = `<p style="color:red; padding:20px;">Error loading admin data. Make sure you are an admin.</p>`;
  }
}

async function handleVerifyListing(id) {
  if (confirm('Verify this listing?')) {
    try {
      await ListingsAPI.verifyListing(id, "Content verified by EcoSphere Admin Team.");
      showToast('Listing verified!', 'success');
      renderAdmin();
    } catch (e) { showToast(e.message, 'error'); }
  }
}

async function handleRejectListing(id) {
  if (confirm('Deactivate this listing?')) {
    try {
      await ListingsAPI.rejectListing(id, "Does not meet platform quality standards.");
      showToast('Listing rejected.', 'info');
      renderAdmin();
    } catch (e) { showToast(e.message, 'error'); }
  }
}

// ─── Init ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  navigate('home');
  renderMarketplace();
  initEconomyAnimation();

  // Close auth modal on Escape or overlay click
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.getElementById('auth-modal')?.classList.remove('show');
    }
  });
  
  const modal = document.getElementById('auth-modal');
  if (modal) {
    modal.addEventListener('click', e => {
      if (e.target === modal) modal.classList.remove('show');
    });
  }

  // Animate hero stats counter
  document.querySelectorAll('.hero-stat-num').forEach(el => {
    const target = el.textContent;
    el.textContent = '0';
    setTimeout(() => { el.textContent = target; el.style.transition = 'all 0.4s'; }, 400);
  });
});
