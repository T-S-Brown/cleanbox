// Cleanbox - Client application
let state = {
  sessionId: null,
  isDemo: false,
  provider: 'gmail',
  currentCategory: 'marketing',
  selectedEmailIds: new Set(),
  emails: [],
  stats: {},
  senders: [],
  presets: {},
  pollTimer: null,
  activeEmailDetails: null,
  lastDeletedBatchId: null,
  undoToastTimeout: null
};

// DOM Elements
const dom = {
  connectionSection: document.getElementById('connection-section'),
  dashboardSection: document.getElementById('dashboard-section'),
  headerStatus: document.getElementById('header-status'),
  connectedBadge: document.getElementById('connected-badge'),
  connectedEmailLabel: document.getElementById('connected-email-label'),
  btnDemoQuick: document.getElementById('btn-demo-quick'),
  btnDisconnect: document.getElementById('btn-disconnect'),
  btnOpenBinHistory: document.getElementById('btn-open-bin-history'),
  binBatchesBadge: document.getElementById('bin-batches-badge'),
  
  // Connection Form
  connectForm: document.getElementById('connect-form'),
  inputEmail: document.getElementById('input-email'),
  inputPassword: document.getElementById('input-password'),
  inputHost: document.getElementById('input-host'),
  inputPort: document.getElementById('input-port'),
  inputSsl: document.getElementById('input-ssl'),
  btnConnect: document.getElementById('btn-connect'),
  btnDemoMode: document.getElementById('btn-demo-mode'),
  btnTogglePw: document.getElementById('btn-toggle-pw'),
  connectError: document.getElementById('connect-error'),
  customServerFields: document.getElementById('custom-server-fields'),
  helpAppPwLink: document.getElementById('help-app-pw-link'),
  guideSteps: document.getElementById('guide-steps'),
  
  // Dashboard Bar
  currentUserEmail: document.getElementById('current-user-email'),
  badgeDemoTag: document.getElementById('badge-demo-tag'),
  userAvatar: document.getElementById('user-avatar'),
  selectFolder: document.getElementById('select-folder'),
  selectMaxEmails: document.getElementById('select-max-emails'),
  btnStartScan: document.getElementById('btn-start-scan'),
  
  // Progress Bar
  scanProgressBox: document.getElementById('scan-progress-box'),
  scanProgressBar: document.getElementById('scan-progress-bar'),
  scanStatusMessage: document.getElementById('scan-status-message'),
  scanStatusPercent: document.getElementById('scan-status-percent'),
  
  // Stats
  statTotalSize: document.getElementById('stat-total-size'),
  statTotalCount: document.getElementById('stat-total-count'),
  statMarketingSize: document.getElementById('stat-marketing-size'),
  statMarketingCount: document.getElementById('stat-marketing-count'),
  statLargeSize: document.getElementById('stat-large-size'),
  statLargeCount: document.getElementById('stat-large-count'),
  statProtectedCount: document.getElementById('stat-protected-count'),
  
  // Tab Counts
  tabCntMarketing: document.getElementById('tab-cnt-marketing'),
  tabCntLarge: document.getElementById('tab-cnt-large'),
  tabCntProtected: document.getElementById('tab-cnt-protected'),
  tabCntAll: document.getElementById('tab-cnt-all'),
  
  // Toolbar
  filterSearch: document.getElementById('filter-search'),
  filterMinSize: document.getElementById('filter-min-size'),
  sortSelector: document.getElementById('sort-selector'),
  btnSelectAll: document.getElementById('btn-select-all'),
  btnDeselectAll: document.getElementById('btn-deselect-all'),
  btnDryRun: document.getElementById('btn-dry-run'),
  btnDeleteSelected: document.getElementById('btn-delete-selected'),
  selectedCountBadge: document.getElementById('selected-count-badge'),
  checkAllTable: document.getElementById('check-all-table'),
  
  // Tables & Views
  emailListContainer: document.getElementById('email-list-container'),
  emailTableBody: document.getElementById('email-table-body'),
  emptyState: document.getElementById('empty-state'),
  senderViewContainer: document.getElementById('sender-view-container'),
  senderCardsGrid: document.getElementById('sender-cards-grid'),
  quickActionBar: document.getElementById('quick-action-bar'),
  
  // Modals & Notifications
  modalPreview: document.getElementById('modal-preview'),
  previewTargetCount: document.getElementById('preview-target-count'),
  previewSpaceFreed: document.getElementById('preview-space-freed'),
  previewActionMode: document.getElementById('preview-action-mode'),
  previewBlockedBox: document.getElementById('preview-blocked-box'),
  previewBlockedCount: document.getElementById('preview-blocked-count'),
  previewSendersSection: document.getElementById('preview-senders-section'),
  previewSendersList: document.getElementById('preview-senders-list'),
  previewEmailsTable: document.getElementById('preview-emails-table'),
  btnProceedFromPreview: document.getElementById('btn-proceed-from-preview'),
  
  modalConfirmDelete: document.getElementById('modal-confirm-delete'),
  confirmEmailCount: document.getElementById('confirm-email-count'),
  confirmEmailSize: document.getElementById('confirm-email-size'),
  btnExecuteDelete: document.getElementById('btn-execute-delete'),
  btnModalDryRun: document.getElementById('btn-modal-dry-run'),
  
  modalBinHistory: document.getElementById('modal-bin-history'),
  binHistoryList: document.getElementById('bin-history-list'),
  
  undoToast: document.getElementById('undo-toast'),
  undoToastText: document.getElementById('undo-toast-text'),
  btnToastUndo: document.getElementById('btn-toast-undo'),
  btnToastDismiss: document.getElementById('btn-toast-dismiss'),
  
  modalEmailDetail: document.getElementById('modal-email-detail'),
  detailSubject: document.getElementById('detail-subject'),
  detailSender: document.getElementById('detail-sender'),
  detailSize: document.getElementById('detail-size'),
  detailClassificationBox: document.getElementById('detail-classification-box'),
  detailCategoryBadge: document.getElementById('detail-category-badge'),
  detailReasonsList: document.getElementById('detail-reasons-list'),
  detailSnippet: document.getElementById('detail-snippet'),
  detailHeaders: document.getElementById('detail-headers')
};

// Initialize app
window.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) lucide.createIcons();
  await loadPresets();
  setupEventListeners();
  updateProviderGuide('gmail');
});

async function loadPresets() {
  try {
    const res = await fetch('/api/presets');
    const data = await res.json();
    state.presets = data.presets || {};
  } catch (err) {
    console.error('Failed to load presets:', err);
  }
}

function updateProviderGuide(provider) {
  state.provider = provider;
  const p = state.presets[provider];
  if (!p) return;

  if (p.guide && p.guide.help_url) {
    dom.helpAppPwLink.href = p.guide.help_url;
    dom.helpAppPwLink.classList.remove('hidden');
  } else {
    dom.helpAppPwLink.classList.add('hidden');
  }

  if (p.guide && p.guide.steps) {
    dom.guideSteps.innerHTML = p.guide.steps.map(s => `<div>${s}</div>`).join('');
  }

  if (provider === 'custom') {
    dom.customServerFields.classList.remove('hidden');
    dom.inputEmail.placeholder = 'user@yourdomain.com';
  } else {
    dom.customServerFields.classList.add('hidden');
    dom.inputEmail.placeholder = provider === 'gmail' ? 'you@gmail.com' : 'you@outlook.com';
  }
}

function setupEventListeners() {
  // Provider tabs
  document.querySelectorAll('.provider-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      document.querySelectorAll('.provider-tab').forEach(t => {
        t.classList.remove('bg-white', 'shadow-sm', 'text-slate-900');
        t.classList.add('text-slate-600');
      });
      tab.classList.add('bg-white', 'shadow-sm', 'text-slate-900');
      tab.classList.remove('text-slate-600');
      updateProviderGuide(tab.dataset.provider);
    });
  });

  // Toggle password visibility
  dom.btnTogglePw.addEventListener('click', () => {
    const isPw = dom.inputPassword.type === 'password';
    dom.inputPassword.type = isPw ? 'text' : 'password';
  });

  // Connect submit
  dom.connectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await connect(false);
  });

  // Quick Demo Buttons
  dom.btnDemoQuick.addEventListener('click', () => connect(true));
  dom.btnDemoMode.addEventListener('click', () => connect(true));

  // Disconnect
  dom.btnDisconnect.addEventListener('click', disconnect);

  // Scan trigger
  dom.btnStartScan.addEventListener('click', startScan);

  // Category Tabs
  document.querySelectorAll('.cat-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.cat-tab').forEach(t => {
        t.classList.remove('border-emerald-600', 'text-emerald-700', 'bg-white', 'font-bold');
        t.classList.add('border-transparent', 'text-slate-600', 'font-medium');
      });
      btn.classList.remove('border-transparent', 'text-slate-600', 'font-medium');
      btn.classList.add('border-emerald-600', 'text-emerald-700', 'bg-white', 'font-bold');
      
      state.currentCategory = btn.dataset.cat;
      if (state.currentCategory === 'senders') {
        dom.emailListContainer.classList.add('hidden');
        dom.senderViewContainer.classList.remove('hidden');
        dom.quickActionBar.classList.add('hidden');
        renderSenders();
      } else {
        dom.emailListContainer.classList.remove('hidden');
        dom.senderViewContainer.classList.add('hidden');
        dom.quickActionBar.classList.remove('hidden');
        renderEmails();
      }
    });
  });

  // Search & Filter listeners
  dom.filterSearch.addEventListener('input', () => {
    if (state.currentCategory === 'senders') renderSenders();
    else renderEmails();
  });
  dom.filterMinSize.addEventListener('change', renderEmails);
  dom.sortSelector.addEventListener('change', renderEmails);

  // Selection controls
  dom.btnSelectAll.addEventListener('click', selectAllVisible);
  dom.btnDeselectAll.addEventListener('click', deselectAll);
  dom.checkAllTable.addEventListener('change', (e) => {
    if (e.target.checked) selectAllVisible();
    else deselectAll();
  });

  // Preview & Delete controls
  dom.btnDryRun.addEventListener('click', openPreviewModal);
  dom.btnDeleteSelected.addEventListener('click', openDeleteModal);
  dom.btnProceedFromPreview.addEventListener('click', () => {
    closeModal(dom.modalPreview);
    openDeleteModal();
  });
  dom.btnExecuteDelete.addEventListener('click', executeDelete);

  // Dry run from confirmation modal
  if (dom.btnModalDryRun) {
    dom.btnModalDryRun.addEventListener('click', () => {
      closeModal(dom.modalConfirmDelete);
      openPreviewModal();
    });
  }

  // Bin & Undo controls
  if (dom.btnOpenBinHistory) {
    dom.btnOpenBinHistory.addEventListener('click', () => {
      loadBinHistory();
      openModal(dom.modalBinHistory);
    });
  }
  if (dom.btnToastUndo) {
    dom.btnToastUndo.addEventListener('click', () => undoDelete());
  }
  if (dom.btnToastDismiss) {
    dom.btnToastDismiss.addEventListener('click', hideUndoToast);
  }

  // Modal dismiss buttons
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.fixed');
      if (modal) closeModal(modal);
    });
  });
}

async function connect(isDemo = false) {
  dom.connectError.classList.add('hidden');
  const btn = isDemo ? dom.btnDemoMode : dom.btnConnect;
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="flex items-center gap-2"><svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Connecting...</span>`;

  try {
    const payload = {
      provider: state.provider,
      email: isDemo ? "demo.user@sandbox.com" : dom.inputEmail.value.trim(),
      password: isDemo ? "" : dom.inputPassword.value.trim(),
      host: dom.inputHost.value.trim() || null,
      port: parseInt(dom.inputPort.value) || 993,
      ssl: dom.inputSsl.checked,
      is_demo: isDemo
    };

    const res = await fetch('/api/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Connection failed');
    }

    state.sessionId = data.session_id;
    state.isDemo = isDemo;

    // Transition UI to connected
    dom.connectionSection.classList.add('hidden');
    dom.dashboardSection.classList.remove('hidden');
    dom.connectedBadge.classList.remove('hidden');
    dom.connectedBadge.classList.add('flex');
    dom.btnDemoQuick.classList.add('hidden');

    const emailDisplay = isDemo ? 'demo.user@sandbox.com' : payload.email;
    dom.connectedEmailLabel.textContent = emailDisplay;
    dom.currentUserEmail.textContent = emailDisplay;
    dom.userAvatar.textContent = emailDisplay.charAt(0).toUpperCase();

    if (isDemo) {
      dom.badgeDemoTag.classList.remove('hidden');
    } else {
      dom.badgeDemoTag.classList.add('hidden');
    }

    // Populate folders
    dom.selectFolder.innerHTML = (data.folders || ['INBOX']).map(f => 
      `<option value="${f}">${f}</option>`
    ).join('');

    // Update bin history badge
    updateBinHistoryBadge();

    // Trigger initial scan automatically
    startScan();

  } catch (err) {
    dom.connectError.textContent = err.message;
    dom.connectError.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
    if (window.lucide) lucide.createIcons();
  }
}

async function disconnect() {
  if (state.sessionId) {
    try {
      await fetch(`/api/disconnect?session_id=${state.sessionId}`, { method: 'POST' });
    } catch (_) {}
  }
  state.sessionId = null;
  state.emails = [];
  state.selectedEmailIds.clear();
  clearInterval(state.pollTimer);
  hideUndoToast();

  if (dom.btnOpenBinHistory) {
    dom.btnOpenBinHistory.classList.add('hidden');
    dom.btnOpenBinHistory.classList.remove('flex');
  }

  dom.connectionSection.classList.remove('hidden');
  dom.dashboardSection.classList.add('hidden');
  dom.connectedBadge.classList.add('hidden');
  dom.connectedBadge.classList.remove('flex');
  dom.btnDemoQuick.classList.remove('hidden');
}

async function startScan() {
  if (!state.sessionId) return;
  
  dom.btnStartScan.disabled = true;
  dom.scanProgressBox.classList.remove('hidden');
  dom.scanProgressBar.style.width = '10%';
  dom.scanStatusPercent.textContent = '10%';
  dom.scanStatusMessage.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-sky-600"></i> Initializing scan...`;
  if (window.lucide) lucide.createIcons();

  const val = dom.selectMaxEmails.value;
  let maxEmails = 500;
  let order = 'newest';
  let scanEntire = false;

  if (val.startsWith('all')) {
    maxEmails = 0;
    scanEntire = true;
    order = val.endsWith('oldest') ? 'oldest' : 'newest';
  } else if (val.includes('_')) {
    const parts = val.split('_');
    maxEmails = parseInt(parts[0]) || 500;
    order = parts[1] || 'newest';
  } else {
    maxEmails = parseInt(val) || 500;
  }

  try {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        folder: dom.selectFolder.value,
        max_emails: maxEmails,
        order: order,
        scan_entire: scanEntire
      })
    });

    if (!res.ok) throw new Error('Failed to initiate scan');

    // Poll status
    clearInterval(state.pollTimer);
    state.pollTimer = setInterval(pollScanStatus, 600);

  } catch (err) {
    alert('Error scanning: ' + err.message);
    dom.scanProgressBox.classList.add('hidden');
    dom.btnStartScan.disabled = false;
  }
}

async function pollScanStatus() {
  if (!state.sessionId) return;

  try {
    const res = await fetch(`/api/scan/status?session_id=${state.sessionId}`);
    const data = await res.json();
    const st = data.status || {};

    if (st.progress !== undefined) {
      dom.scanProgressBar.style.width = `${st.progress}%`;
      dom.scanStatusPercent.textContent = `${st.progress}%`;
      dom.scanStatusMessage.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-sky-600"></i> ${st.message || 'Scanning...'}`;
      if (window.lucide) lucide.createIcons();
    }

    if (st.state === 'complete') {
      clearInterval(state.pollTimer);
      dom.scanProgressBar.style.width = '100%';
      dom.scanStatusPercent.textContent = '100%';
      dom.scanStatusMessage.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 text-emerald-600"></i> Scan complete!`;
      if (window.lucide) lucide.createIcons();

      setTimeout(() => {
        dom.scanProgressBox.classList.add('hidden');
        dom.btnStartScan.disabled = false;
      }, 1000);

      // Update stats, fetch emails, and refresh bin history badge
      updateStats(data.stats);
      await fetchEmails();
      await fetchSenders();
      await updateBinHistoryBadge();
    } else if (st.state === 'error') {
      clearInterval(state.pollTimer);
      alert('Scanning failed: ' + st.message);
      dom.scanProgressBox.classList.add('hidden');
      dom.btnStartScan.disabled = false;
    }
  } catch (err) {
    console.error('Poll status error:', err);
  }
}

function updateStats(stats) {
  if (!stats) return;
  state.stats = stats;

  dom.statTotalSize.textContent = stats.total_size_formatted || '0 MB';
  dom.statTotalCount.textContent = `${stats.total_count || 0} emails scanned`;

  dom.statMarketingSize.textContent = stats.marketing_size_formatted || '0 MB';
  dom.statMarketingCount.textContent = `${stats.marketing_count || 0} marketing emails found`;

  dom.statLargeSize.textContent = stats.large_size_formatted || '0 MB';
  dom.statLargeCount.textContent = `${stats.large_count || 0} emails > 1 MB`;

  dom.statProtectedCount.textContent = `${stats.protected_count || 0}`;

  dom.tabCntMarketing.textContent = stats.marketing_count || 0;
  dom.tabCntLarge.textContent = stats.large_count || 0;
  dom.tabCntProtected.textContent = stats.protected_count || 0;
  dom.tabCntAll.textContent = stats.total_count || 0;
}

async function fetchEmails() {
  if (!state.sessionId) return;

  try {
    const res = await fetch(`/api/emails?session_id=${state.sessionId}&limit=1000`);
    const data = await res.json();
    state.emails = data.emails || [];
    renderEmails();
  } catch (err) {
    console.error('Fetch emails error:', err);
  }
}

async function fetchSenders() {
  if (!state.sessionId) return;
  try {
    const res = await fetch(`/api/senders?session_id=${state.sessionId}`);
    const data = await res.json();
    state.senders = data.senders || [];
  } catch (err) {
    console.error('Fetch senders error:', err);
  }
}

function renderEmails() {
  const searchQuery = dom.filterSearch.value.toLowerCase().trim();
  const minSizeMb = parseFloat(dom.filterMinSize.value) || 0;
  const minBytes = minSizeMb * 1024 * 1024;
  const sortBy = dom.sortSelector.value;

  let filtered = state.emails.filter(m => {
    // Category filtering
    if (state.currentCategory === 'marketing' && !m.is_marketing) return false;
    if (state.currentCategory === 'large' && !m.is_large) return false;
    if (state.currentCategory === 'protected' && !m.is_protected) return false;

    // Size filter
    if (minBytes > 0 && m.size_bytes < minBytes) return false;

    // Search filter
    if (searchQuery) {
      const match = m.subject.toLowerCase().includes(searchQuery) ||
                    m.sender.toLowerCase().includes(searchQuery) ||
                    (m.body_snippet && m.body_snippet.toLowerCase().includes(searchQuery));
      if (!match) return false;
    }
    return true;
  });

  // Sort
  if (sortBy === 'size_desc') {
    filtered.sort((a, b) => b.size_bytes - a.size_bytes);
  } else if (sortBy === 'size_asc') {
    filtered.sort((a, b) => a.size_bytes - b.size_bytes);
  } else if (sortBy === 'score_desc') {
    filtered.sort((a, b) => (b.marketing_score || 0) - (a.marketing_score || 0));
  }

  dom.emailTableBody.innerHTML = '';
  if (filtered.length === 0) {
    dom.emptyState.classList.remove('hidden');
  } else {
    dom.emptyState.classList.add('hidden');
  }

  filtered.forEach(m => {
    const isSelected = state.selectedEmailIds.has(m.id);
    const tr = document.createElement('tr');
    tr.className = `border-b border-slate-100 hover:bg-slate-50/80 transition cursor-pointer ${isSelected ? 'table-row-selected' : ''} ${m.is_protected ? 'table-row-protected' : ''}`;
    
    // Status badges
    let statusBadge = '';
    if (m.is_protected) {
      statusBadge = `
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-200" title="${m.protection_reasons ? m.protection_reasons.join(', ') : 'Protected receipt/booking'}">
          <i data-lucide="shield-check" class="w-3 h-3 text-sky-600"></i>
          Protected
        </span>
      `;
    } else if (m.is_marketing) {
      statusBadge = `
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
          <i data-lucide="tag" class="w-3 h-3 text-emerald-600"></i>
          Marketing
        </span>
      `;
    } else {
      statusBadge = `
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700">
          General
        </span>
      `;
    }

    // Size Flag Badge
    let sizeBadgeClass = 'text-slate-600 font-medium';
    let sizePill = '';
    if (m.size_category === 'huge') {
      sizeBadgeClass = 'text-red-700 font-extrabold';
      sizePill = '<span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-red-100 text-red-700 ml-1">HUGE</span>';
    } else if (m.size_category === 'very_large') {
      sizeBadgeClass = 'text-amber-700 font-bold';
      sizePill = '<span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-100 text-amber-800 ml-1">LARGE</span>';
    } else if (m.size_category === 'large') {
      sizeBadgeClass = 'text-amber-600 font-bold';
      sizePill = '<span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-50 text-amber-700 ml-1">&gt;1MB</span>';
    }

    // Checkbox: Disabled if protected to safeguard receipts and bookings
    const checkboxDisabled = m.is_protected ? 'disabled title="Protected email: Cannot be deleted with marketing emails"' : '';

    tr.innerHTML = `
      <td class="p-3 text-center align-middle" onclick="event.stopPropagation()">
        <input type="checkbox" data-id="${m.id}" ${checkboxDisabled} ${isSelected ? 'checked' : ''} class="email-select-cb rounded border-slate-300 text-sky-600 focus:ring-sky-500" />
      </td>
      <td class="p-3 align-middle">
        ${statusBadge}
      </td>
      <td class="p-3 align-middle max-w-md">
        <div class="font-bold text-slate-900 truncate" title="${escapeHtml(m.subject)}">${escapeHtml(m.subject)}</div>
        <div class="text-[11px] text-slate-400 truncate mt-0.5">${escapeHtml(m.body_snippet || m.date || '')}</div>
      </td>
      <td class="p-3 align-middle truncate font-mono text-[11px] text-slate-600 max-w-[180px]" title="${escapeHtml(m.sender)}">
        ${escapeHtml(m.sender)}
      </td>
      <td class="p-3 align-middle text-right whitespace-nowrap">
        <span class="${sizeBadgeClass}">${m.size_formatted}</span>
        ${sizePill}
      </td>
      <td class="p-3 align-middle text-center" onclick="event.stopPropagation()">
        <button class="btn-inspect-email p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition" title="Inspect details & reasons">
          <i data-lucide="info" class="w-4 h-4"></i>
        </button>
      </td>
    `;

    // Row click selects checkbox (if not protected) or shows details
    tr.addEventListener('click', () => {
      if (!m.is_protected) {
        toggleSelect(m.id);
      } else {
        openEmailDetail(m);
      }
    });

    // Checkbox toggle
    const cb = tr.querySelector('.email-select-cb');
    if (cb && !m.is_protected) {
      cb.addEventListener('change', () => toggleSelect(m.id));
    }

    // Inspect button
    tr.querySelector('.btn-inspect-email').addEventListener('click', () => {
      openEmailDetail(m);
    });

    dom.emailTableBody.appendChild(tr);
  });

  updateSelectedCount();
  if (window.lucide) lucide.createIcons();
}

function renderSenders() {
  const grid = dom.senderCardsGrid;
  grid.innerHTML = '';

  const searchQuery = dom.filterSearch.value.toLowerCase().trim();
  const senders = state.senders.filter(s => {
    if (!searchQuery) return true;
    return s.sender.toLowerCase().includes(searchQuery);
  });

  if (senders.length === 0) {
    grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400">No senders found</div>`;
    return;
  }

  senders.forEach(s => {
    const card = document.createElement('div');
    card.className = "bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-slate-300 transition";
    
    const isPromoOnly = s.is_primarily_marketing;
    const badge = isPromoOnly ? 
      `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Marketing Sender</span>` :
      (s.protected_count > 0 ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800">Contains Protected</span>` : `<span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700">Mixed</span>`);

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2">
          ${badge}
          <span class="text-xs font-bold text-slate-900">${s.total_size_formatted}</span>
        </div>
        <p class="font-mono text-xs font-bold text-slate-800 truncate" title="${escapeHtml(s.sender)}">${escapeHtml(s.sender)}</p>
        <p class="text-[11px] text-slate-500 mt-1">${s.count} email${s.count > 1 ? 's' : ''} (${s.marketing_count} marketing, ${s.protected_count} protected)</p>
      </div>
      <div class="mt-4 pt-3 border-t border-slate-100 flex justify-between items-center">
        <button class="btn-select-sender-emails text-xs text-sky-600 hover:text-sky-800 font-semibold">
          Select Marketing Emails
        </button>
      </div>
    `;

    card.querySelector('.btn-select-sender-emails').addEventListener('click', () => {
      // Select all marketing emails from this sender (excluding any protected)
      const marketingIds = state.emails
        .filter(m => m.sender === s.sender && m.is_marketing && !m.is_protected)
        .map(m => m.id);
      
      marketingIds.forEach(id => state.selectedEmailIds.add(id));
      updateSelectedCount();
      
      // Switch to marketing tab and filter by sender
      document.querySelector('[data-cat="marketing"]').click();
      dom.filterSearch.value = s.sender;
      renderEmails();
    });

    grid.appendChild(card);
  });
}

function toggleSelect(id) {
  if (state.selectedEmailIds.has(id)) {
    state.selectedEmailIds.delete(id);
  } else {
    state.selectedEmailIds.add(id);
  }
  updateSelectedCount();
  renderEmails();
}

function selectAllVisible() {
  const searchQuery = dom.filterSearch.value.toLowerCase().trim();
  const minSizeMb = parseFloat(dom.filterMinSize.value) || 0;
  const minBytes = minSizeMb * 1024 * 1024;

  state.emails.forEach(m => {
    // NEVER auto-select protected emails
    if (m.is_protected) return;

    if (state.currentCategory === 'marketing' && !m.is_marketing) return;
    if (state.currentCategory === 'large' && !m.is_large) return;

    if (minBytes > 0 && m.size_bytes < minBytes) return;

    if (searchQuery) {
      const match = m.subject.toLowerCase().includes(searchQuery) ||
                    m.sender.toLowerCase().includes(searchQuery);
      if (!match) return;
    }

    state.selectedEmailIds.add(m.id);
  });

  updateSelectedCount();
  renderEmails();
}

function deselectAll() {
  state.selectedEmailIds.clear();
  updateSelectedCount();
  renderEmails();
}

function updateSelectedCount() {
  const count = state.selectedEmailIds.size;
  dom.selectedCountBadge.textContent = count;
  dom.btnDeleteSelected.disabled = count === 0;
  dom.btnDryRun.disabled = count === 0;
}

async function openPreviewModal() {
  if (state.selectedEmailIds.size === 0) {
    alert("Please select at least one marketing email first.");
    return;
  }

  try {
    const res = await fetch('/api/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        email_ids: Array.from(state.selectedEmailIds),
        dry_run: true
      })
    });

    const data = await res.json();
    dom.previewTargetCount.textContent = data.target_count;
    dom.previewSpaceFreed.textContent = data.space_to_free_formatted;
    dom.previewActionMode.textContent = data.mode;

    if (data.blocked_protected_count > 0) {
      dom.previewBlockedBox.classList.remove('hidden');
      dom.previewBlockedCount.textContent = data.blocked_protected_count;
    } else {
      dom.previewBlockedBox.classList.add('hidden');
    }

    // Populate Senders Breakdown
    if (data.senders_summary && data.senders_summary.length > 0) {
      dom.previewSendersSection.classList.remove('hidden');
      dom.previewSendersList.innerHTML = data.senders_summary.map(s => `
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono font-medium">
          <span class="font-bold text-slate-900">${escapeHtml(s.sender)}:</span>
          <span>${s.count} email${s.count > 1 ? 's' : ''} (${escapeHtml(s.size_formatted)})</span>
        </span>
      `).join('');
    } else {
      dom.previewSendersSection.classList.add('hidden');
    }

    // Populate Sample Emails Table
    if (data.targets_sample && data.targets_sample.length > 0) {
      dom.previewEmailsTable.innerHTML = data.targets_sample.map(m => `
        <div class="p-2.5 flex items-center justify-between gap-3 hover:bg-white transition">
          <div class="min-w-0 flex-1">
            <p class="font-bold text-slate-800 truncate">${escapeHtml(m.subject)}</p>
            <p class="text-[10px] font-mono text-slate-500 truncate">${escapeHtml(m.sender)} &bull; ${escapeHtml(m.date || '')}</p>
          </div>
          <span class="text-xs font-bold text-slate-700 whitespace-nowrap">${escapeHtml(m.size_formatted)}</span>
        </div>
      `).join('');
    } else {
      dom.previewEmailsTable.innerHTML = `<div class="p-4 text-center text-slate-400">No email details available</div>`;
    }

    openModal(dom.modalPreview);
  } catch (err) {
    alert('Dry Run Preview error: ' + err.message);
  }
}

function openDeleteModal() {
  if (state.selectedEmailIds.size === 0) {
    alert("Please select at least one marketing email first.");
    return;
  }

  const selectedList = state.emails.filter(m => state.selectedEmailIds.has(m.id));
  const totalBytes = selectedList.reduce((acc, m) => acc + m.size_bytes, 0);

  dom.confirmEmailCount.textContent = `${state.selectedEmailIds.size} emails`;
  dom.confirmEmailSize.textContent = formatBytesJs(totalBytes);

  openModal(dom.modalConfirmDelete);
}

async function executeDelete() {
  const permanent = document.querySelector('input[name="delete-mode"]:checked').value === 'permanent';
  
  dom.btnExecuteDelete.disabled = true;
  dom.btnExecuteDelete.innerHTML = `<span class="flex items-center gap-2"><svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Cleaning...</span>`;

  try {
    const res = await fetch('/api/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        email_ids: Array.from(state.selectedEmailIds),
        permanent: permanent,
        dry_run: false
      })
    });

    const data = await res.json();
    closeModal(dom.modalConfirmDelete);

    if (data.success) {
      state.selectedEmailIds.clear();
      await fetchEmails();
      await fetchSenders();
      
      // Update stats from backend
      const stRes = await fetch(`/api/scan/status?session_id=${state.sessionId}`);
      const stData = await stRes.json();
      updateStats(stData.stats);
      await updateBinHistoryBadge();

      // Show Undo Toast if moved to bin
      if (data.can_undo && data.batch_id) {
        showUndoToast(`Moved ${data.deleted_count} email${data.deleted_count > 1 ? 's' : ''} (${data.freed_formatted}) to Bin.`, data.batch_id);
      } else {
        alert(`🎉 Successfully freed ${data.freed_formatted}!\nPermanently removed ${data.deleted_count} emails.`);
      }
    } else {
      alert('Deletion error: ' + (data.errors ? data.errors.join(', ') : 'Unknown'));
    }
  } catch (err) {
    alert('Deletion error: ' + err.message);
  } finally {
    dom.btnExecuteDelete.disabled = false;
    dom.btnExecuteDelete.innerHTML = `<i data-lucide="check" class="w-4 h-4"></i> Confirm & Clean Now`;
    if (window.lucide) lucide.createIcons();
  }
}

function showUndoToast(message, batchId) {
  state.lastDeletedBatchId = batchId;
  dom.undoToastText.textContent = message;
  dom.undoToast.classList.remove('hidden');
  dom.undoToast.classList.add('flex');
  if (window.lucide) lucide.createIcons();

  if (state.undoToastTimeout) clearTimeout(state.undoToastTimeout);
  state.undoToastTimeout = setTimeout(() => {
    hideUndoToast();
  }, 25000);
}

function hideUndoToast() {
  dom.undoToast.classList.add('hidden');
  dom.undoToast.classList.remove('flex');
  if (state.undoToastTimeout) clearTimeout(state.undoToastTimeout);
}

async function undoDelete(batchId = null) {
  if (!state.sessionId) return;
  const targetBatch = batchId || state.lastDeletedBatchId;

  dom.btnToastUndo.disabled = true;
  dom.btnToastUndo.innerHTML = `<span class="flex items-center gap-1.5"><svg class="animate-spin h-3.5 w-3.5 text-slate-900" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Restoring...</span>`;

  try {
    const res = await fetch('/api/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        batch_id: targetBatch
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Undo failed');

    hideUndoToast();
    alert(`🎉 ${data.message || 'Successfully restored emails back to INBOX!'}`);

    // Refresh email list, senders, stats, and bin badge
    await fetchEmails();
    await fetchSenders();
    const stRes = await fetch(`/api/scan/status?session_id=${state.sessionId}`);
    const stData = await stRes.json();
    updateStats(stData.stats);
    await updateBinHistoryBadge();

    // If history modal is open, refresh it
    if (!dom.modalBinHistory.classList.contains('hidden')) {
      await loadBinHistory();
    }
  } catch (err) {
    alert('Failed to undo delete: ' + err.message);
  } finally {
    dom.btnToastUndo.disabled = false;
    dom.btnToastUndo.innerHTML = `<i data-lucide="undo-2" class="w-3.5 h-3.5"></i> <span>Undo Delete</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

async function updateBinHistoryBadge() {
  if (!state.sessionId) return;
  try {
    const res = await fetch(`/api/undo/history?session_id=${state.sessionId}`);
    const data = await res.json();
    const count = data.active_bin_count || 0;
    dom.binBatchesBadge.textContent = count;
    if (data.history && data.history.length > 0) {
      dom.btnOpenBinHistory.classList.remove('hidden');
      dom.btnOpenBinHistory.classList.add('flex');
    } else {
      dom.btnOpenBinHistory.classList.add('hidden');
      dom.btnOpenBinHistory.classList.remove('flex');
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Failed to update bin badge:', err);
  }
}

async function loadBinHistory() {
  if (!state.sessionId) return;
  dom.binHistoryList.innerHTML = `<div class="py-8 text-center text-slate-400">Loading history...</div>`;

  try {
    const res = await fetch(`/api/undo/history?session_id=${state.sessionId}`);
    const data = await res.json();
    const history = data.history || [];

    if (history.length === 0) {
      dom.binHistoryList.innerHTML = `
        <div class="py-12 text-center text-slate-400">
          <i data-lucide="inbox" class="w-8 h-8 mx-auto text-slate-300 mb-2"></i>
          <p class="font-medium text-slate-600">No emails currently in Bin</p>
          <p class="text-[11px] text-slate-400">When you clean emails using 'Move to Bin', you can review and undo them here.</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    dom.binHistoryList.innerHTML = '';
    history.forEach(b => {
      const card = document.createElement('div');
      card.className = "p-4 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white transition space-y-2.5";

      let statusBadge = '';
      let actionBtn = '';

      if (b.status === 'in_bin') {
        statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">In Bin (Recoverable)</span>`;
        actionBtn = `
          <button data-batch-id="${b.batch_id}" class="btn-restore-batch px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white transition flex items-center gap-1.5 shadow-sm">
            <i data-lucide="undo-2" class="w-3.5 h-3.5"></i>
            Restore to ${escapeHtml(b.source_folder || 'INBOX')}
          </button>
        `;
      } else if (b.status === 'restored') {
        statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">Restored to ${escapeHtml(b.source_folder || 'INBOX')}</span>`;
        actionBtn = `<span class="text-xs text-slate-400 font-medium">✓ Restored</span>`;
      } else {
        statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">Permanently Expunged</span>`;
        actionBtn = `<span class="text-xs text-slate-400 italic">Cannot undo</span>`;
      }

      card.innerHTML = `
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            ${statusBadge}
            <span class="text-xs text-slate-500">${b.timestamp}</span>
          </div>
          <span class="font-extrabold text-xs text-slate-800">${b.freed_formatted} (${b.count} email${b.count > 1 ? 's' : ''})</span>
        </div>
        <div class="text-[11px] text-slate-600">
          <p class="font-semibold text-slate-700">Sample emails:</p>
          <ul class="list-disc pl-4 space-y-0.5 mt-0.5 text-slate-500">
            ${(b.sample_subjects || []).map(s => `<li class="truncate">${escapeHtml(s)}</li>`).join('')}
          </ul>
        </div>
        <div class="flex justify-between items-center pt-2 border-t border-slate-200/60">
          <span class="text-[10px] text-slate-400">Target: ${escapeHtml(b.trash_folder || 'Trash')} &rarr; ${escapeHtml(b.source_folder || 'INBOX')}</span>
          ${actionBtn}
        </div>
      `;

      const restoreBtn = card.querySelector('.btn-restore-batch');
      if (restoreBtn) {
        restoreBtn.addEventListener('click', async () => {
          await undoDelete(b.batch_id);
        });
      }

      dom.binHistoryList.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    dom.binHistoryList.innerHTML = `<div class="py-4 text-red-500 text-center">Error loading history: ${err.message}</div>`;
  }
}

function openEmailDetail(email) {
  state.activeEmailDetails = email;
  dom.detailSubject.textContent = email.subject;
  dom.detailSender.textContent = email.sender;
  dom.detailSize.textContent = `${email.size_formatted} (${email.size_bytes.toLocaleString()} bytes)`;
  dom.detailSnippet.textContent = email.body_snippet || "(No plain text snippet available)";

  const box = dom.detailClassificationBox;
  const badge = dom.detailCategoryBadge;
  const list = dom.detailReasonsList;
  list.innerHTML = '';

  if (email.is_protected) {
    box.className = "p-3.5 rounded-xl border border-sky-200 bg-sky-50";
    badge.innerHTML = `<i data-lucide="shield-check" class="w-4 h-4 text-sky-700"></i> <span class="text-sky-900">SAFEGUARDED: Protected Transactional Email</span>`;
    (email.protection_reasons || ["Important purchase or booking match"]).forEach(r => {
      const li = document.createElement('li');
      li.textContent = r;
      list.appendChild(li);
    });
  } else if (email.is_marketing) {
    box.className = "p-3.5 rounded-xl border border-emerald-200 bg-emerald-50";
    badge.innerHTML = `<i data-lucide="tag" class="w-4 h-4 text-emerald-700"></i> <span class="text-emerald-900">MARKETING EMAIL (Confidence: ${email.marketing_score}%)</span>`;
    (email.marketing_reasons || ["Recognized marketing campaign or newsletter"]).forEach(r => {
      const li = document.createElement('li');
      li.textContent = r;
      list.appendChild(li);
    });
  } else {
    box.className = "p-3.5 rounded-xl border border-slate-200 bg-slate-50";
    badge.innerHTML = `<i data-lucide="info" class="w-4 h-4 text-slate-700"></i> <span class="text-slate-900">GENERAL EMAIL</span>`;
    const li = document.createElement('li');
    li.textContent = "Neither identified as promotional marketing nor critical purchase/booking.";
    list.appendChild(li);
  }

  dom.detailHeaders.textContent = JSON.stringify(email.headers || {}, null, 2);
  openModal(dom.modalEmailDetail);
}

function openModal(modal) {
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  if (window.lucide) lucide.createIcons();
}

function closeModal(modal) {
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

function formatBytesJs(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
