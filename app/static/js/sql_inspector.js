/**
 * BharatPath - Global Under-the-Hood SQL Inspector & Pramana Modal Handler
 */

window.BharatPath = window.BharatPath || {};

(function () {
  const queryHistory = [];
  let queryCount = 0;

  // Initialize SQL Drawer and Hooks
  document.addEventListener('DOMContentLoaded', () => {
    setupSqlDrawer();
    setupPramanaModal();
  });

  function setupSqlDrawer() {
    const toggleBtn = document.getElementById('toggleSqlDrawerBtn');
    const drawer = document.getElementById('sqlDrawer');
    const clearBtn = document.getElementById('clearSqlHistoryBtn');

    if (toggleBtn && drawer) {
      toggleBtn.addEventListener('click', () => {
        drawer.classList.toggle('collapsed');
        const icon = toggleBtn.querySelector('i');
        if (icon) {
          icon.classList.toggle('fa-chevron-up');
          icon.classList.toggle('fa-chevron-down');
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        queryHistory.length = 0;
        queryCount = 0;
        updateQueryBadge();
        renderQueryList();
      });
    }
  }

  // Hook into native fetch to automatically capture `sql_meta`
  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await originalFetch.apply(this, args);
    const clone = response.clone();

    // Check if JSON response has sql_meta
    const contentType = clone.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      clone.json().then(data => {
        if (data && data.sql_meta) {
          logSqlQuery(data.sql_meta, args[0]);
        }
      }).catch(() => {});
    }

    return response;
  };

  function logSqlQuery(meta, url) {
    if (!meta || !meta.query) return;

    queryCount++;
    const entry = {
      id: queryCount,
      timestamp: new Date().toLocaleTimeString(),
      query: meta.query,
      duration: meta.execution_ms || 0,
      rows: meta.row_count || 0,
      endpoint: typeof url === 'string' ? url.split('?')[0] : 'API'
    };

    queryHistory.unshift(entry);
    if (queryHistory.length > 30) queryHistory.pop();

    updateQueryBadge();
    renderQueryList();
  }

  function updateQueryBadge() {
    const badge = document.getElementById('sqlQueryCountBadge');
    if (badge) {
      badge.textContent = `${queryCount} Queries`;
      badge.classList.remove('hidden');
    }
  }

  function renderQueryList() {
    const container = document.getElementById('sqlLogContainer');
    if (!container) return;

    if (queryHistory.length === 0) {
      container.innerHTML = `
        <div class="p-6 text-center text-amber-800/70 text-sm">
          No SQL queries executed yet. Interact with the map, filters, or pathfinder to view live PostgreSQL telemetry.
        </div>`;
      return;
    }

    container.innerHTML = queryHistory.map(item => `
      <div class="border-b border-amber-900/10 p-3 hover:bg-amber-50/70 transition-colors">
        <div class="flex items-center justify-between text-xs mb-1.5">
          <div class="flex items-center gap-2">
            <span class="px-1.5 py-0.5 rounded bg-amber-800 text-amber-100 font-mono font-bold">#${item.id}</span>
            <span class="font-medium text-amber-900">${item.endpoint}</span>
            <span class="text-stone-500">${item.timestamp}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-emerald-700 font-medium font-mono">${item.duration} ms</span>
            <span class="text-amber-800 font-mono font-medium">${item.rows} rows</span>
            <button onclick="navigator.clipboard.writeText(\`${item.query.replace(/`/g, '\\`').replace(/\\/g, '\\\\')}\`); this.textContent='Copied!'; setTimeout(() => this.textContent='Copy', 1500);" 
                    class="text-xs px-2 py-0.5 rounded bg-amber-200/60 hover:bg-amber-300 text-amber-900 transition">
              Copy
            </button>
          </div>
        </div>
        <pre class="bg-stone-900 text-amber-300 p-2.5 rounded text-xs overflow-x-auto font-mono leading-relaxed select-all">${escapeHtml(item.query)}</pre>
      </div>
    `).join('');
  }

  function escapeHtml(string) {
    const entityMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    };
    return String(string).replace(/[&<>"']/g, s => entityMap[s]);
  }

  // Global Pramana Citation Modal
  function setupPramanaModal() {
    const modal = document.getElementById('pramanaCitationModal');
    const closeBtn = document.getElementById('closePramanaModalBtn');
    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
      });
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
      });
    }
  }

  window.openPramanaModal = async function (entityType, entityId) {
    const modal = document.getElementById('pramanaCitationModal');
    const content = document.getElementById('pramanaModalContent');
    if (!modal || !content) return;

    modal.classList.remove('hidden');
    content.innerHTML = `
      <div class="p-8 text-center text-amber-900">
        <i class="fa-solid fa-compass fa-spin text-3xl mb-3 text-amber-600"></i>
        <p>Consulting classical Indian texts & epigraphic archives...</p>
      </div>`;

    try {
      const res = await originalFetch(`/api/pramana/${entityType}/${entityId}`);
      const data = await res.json();
      const citations = data.citations || [];

      if (citations.length === 0) {
        content.innerHTML = `
          <div class="p-6 text-center text-stone-600">
            <i class="fa-solid fa-scroll text-3xl text-amber-700/50 mb-2"></i>
            <p class="font-heading text-lg font-bold">No direct citations recorded</p>
            <p class="text-sm">Referenced across broader archaeological reports and epigraphic corpora.</p>
          </div>`;
        return;
      }

      content.innerHTML = citations.map(c => `
        <div class="mb-5 last:mb-0 border border-amber-300 bg-amber-50/50 rounded-lg p-5">
          <div class="flex items-start justify-between gap-4 mb-2">
            <div>
              <span class="inline-block px-2 py-0.5 rounded text-xs font-bold uppercase bg-amber-200 text-amber-900 mb-1">
                ${c.source_type || 'Classical Source'}
              </span>
              <h4 class="font-heading text-lg font-bold text-amber-950">${c.source_title}</h4>
              <p class="text-xs text-stone-600">
                <strong>Author / Tradition:</strong> ${c.author_or_tradition} &bull; 
                <strong>Language:</strong> ${c.language} &bull; 
                <strong>Era:</strong> ${c.approximate_century}
              </p>
            </div>
            <i class="fa-solid fa-feather-pointed text-amber-600 text-2xl"></i>
          </div>

          ${c.citation_excerpt ? `
            <blockquote class="border-l-4 border-amber-600 pl-3 italic text-sm text-stone-800 my-3 font-serif-sub">
              "${c.citation_excerpt}"
            </blockquote>
          ` : ''}

          ${c.artefact_metadata && Object.keys(c.artefact_metadata).length > 0 ? `
            <div class="mt-3 pt-3 border-t border-amber-200/80">
              <span class="text-xs font-bold text-amber-900 block mb-1">Epigraphic & Manuscript Context:</span>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-stone-700 bg-white/80 p-2.5 rounded border border-amber-200/60 font-mono">
                ${Object.entries(c.artefact_metadata).map(([k, v]) => `
                  <div><strong class="text-amber-800">${k}:</strong> ${typeof v === 'object' ? JSON.stringify(v) : v}</div>
                `).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      `).join('');
    } catch (err) {
      content.innerHTML = `
        <div class="p-6 text-center text-red-700">
          <p>Failed to retrieve Pramana citation records: ${err.message}</p>
        </div>`;
    }
  };

  // Expose logger
  window.BharatPath.logSqlQuery = logSqlQuery;
})();
