/**
 * BharatPath - Viva SQL Lab & NLP Workbench Scripts
 */

(function () {
  let vivaQueries = [];
  let selectedQueryId = 1;
  let samplePassages = [];

  document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadVivaQueries();
    initVakToSql();
    initNerWorkbench();
  });

  // 1. Tab Switching
  function initTabs() {
    const tabBtns = {
      viva: document.getElementById('tabBtnViva'),
      vak: document.getElementById('tabBtnVak'),
      ner: document.getElementById('tabBtnNer')
    };

    const tabContents = {
      viva: document.getElementById('tabContentViva'),
      vak: document.getElementById('tabContentVak'),
      ner: document.getElementById('tabContentNer')
    };

    function switchTab(activeKey) {
      Object.keys(tabBtns).forEach(key => {
        if (key === activeKey) {
          tabBtns[key].classList.replace('text-amber-950', 'text-white');
          tabBtns[key].classList.add('bg-amber-800', 'shadow-sm');
          tabContents[key].classList.remove('hidden');
        } else {
          tabBtns[key].classList.replace('text-white', 'text-amber-950');
          tabBtns[key].classList.remove('bg-amber-800', 'shadow-sm');
          tabContents[key].classList.add('hidden');
        }
      });
    }

    if (tabBtns.viva) tabBtns.viva.addEventListener('click', () => switchTab('viva'));
    if (tabBtns.vak) tabBtns.vak.addEventListener('click', () => switchTab('vak'));
    if (tabBtns.ner) tabBtns.ner.addEventListener('click', () => switchTab('ner'));
  }

  // 2. Viva Queries Runner
  async function loadVivaQueries() {
    try {
      const res = await fetch('/api/viva/queries');
      const data = await res.json();
      vivaQueries = data.queries || [];

      document.getElementById('vivaQueriesCount').textContent = `${vivaQueries.length} Queries`;
      renderVivaQueryList();

      if (vivaQueries.length > 0) {
        selectVivaQuery(vivaQueries[0].query_id);
      }

      document.getElementById('runSelectedVivaQueryBtn').addEventListener('click', () => {
        executeVivaQuery(selectedQueryId);
      });

    } catch (e) {
      console.error('Error fetching viva queries:', e);
    }
  }

  function renderVivaQueryList() {
    const container = document.getElementById('vivaQueriesList');
    container.innerHTML = vivaQueries.map(q => `
      <div onclick="window.selectVivaQuery(${q.query_id})" 
           id="vivaCard_${q.query_id}"
           class="manuscript-card rounded-lg p-3 border cursor-pointer hover:border-amber-600 transition text-xs">
        <div class="flex items-center justify-between mb-1">
          <span class="px-2 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
            Q${q.query_id} &bull; ${q.category}
          </span>
        </div>
        <h4 class="font-heading font-bold text-amber-950 text-xs leading-snug">${q.name}</h4>
      </div>
    `).join('');
  }

  window.selectVivaQuery = function (queryId) {
    selectedQueryId = queryId;
    const q = vivaQueries.find(item => item.query_id === queryId);
    if (!q) return;

    document.querySelectorAll('[id^="vivaCard_"]').forEach(el => {
      el.classList.remove('border-amber-700', 'bg-amber-100/70', 'ring-2', 'ring-amber-500');
    });
    const active = document.getElementById(`vivaCard_${queryId}`);
    if (active) active.classList.add('border-amber-700', 'bg-amber-100/70', 'ring-2', 'ring-amber-500');

    document.getElementById('activeQueryCategory').textContent = `Query ${q.query_id}: ${q.category}`;
    document.getElementById('activeQueryTitle').textContent = q.name;
    document.getElementById('activeQueryDesc').textContent = q.description;
    document.getElementById('activeQuerySql').textContent = q.sql;

    document.getElementById('vivaExecutionMetrics').classList.add('hidden');
    document.getElementById('vivaResultsTableContainer').innerHTML = `
      <div class="p-8 text-center text-stone-400 text-xs">
        Click <strong>"Execute Live"</strong> to run this SQL query against PostgreSQL.
      </div>`;
  };

  async function executeVivaQuery(queryId) {
    const tableContainer = document.getElementById('vivaResultsTableContainer');
    const metricsBox = document.getElementById('vivaExecutionMetrics');

    tableContainer.innerHTML = `
      <div class="p-6 text-center text-amber-800 text-xs">
        <i class="fa-solid fa-spinner fa-spin mr-1"></i> Executing query against PostgreSQL...
      </div>`;

    try {
      const res = await fetch(`/api/viva/run/${queryId}`, { method: 'POST' });
      const data = await res.json();

      if (data.error) {
        tableContainer.innerHTML = `<div class="p-4 text-xs text-red-700">Error executing query: ${data.error}</div>`;
        return;
      }

      // Show metrics
      metricsBox.classList.remove('hidden');
      document.getElementById('vivaExecTime').textContent = `${data.sql_meta.execution_ms} ms`;
      document.getElementById('vivaExecRows').textContent = `${data.sql_meta.row_count} rows`;

      renderTable(tableContainer, data.columns, data.rows);
    } catch (e) {
      tableContainer.innerHTML = `<div class="p-4 text-xs text-red-700">Execution failed: ${e.message}</div>`;
    }
  }

  // 3. Vāk-to-SQL
  function initVakToSql() {
    const form = document.getElementById('vakToSqlForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = document.getElementById('vakQuestionInput').value.trim();
        if (!question) return;
        runVakQuery(question);
      });
    }
  }

  window.setVakQuestion = function (question) {
    document.getElementById('vakQuestionInput').value = question;
    runVakQuery(question);
  };

  async function runVakQuery(question) {
    const resultsBox = document.getElementById('vakResultsBox');
    const sqlEl = document.getElementById('vakGeneratedSql');
    const timingEl = document.getElementById('vakExecutionTiming');
    const tableContainer = document.getElementById('vakTableContainer');

    resultsBox.classList.remove('hidden');
    tableContainer.innerHTML = `
      <div class="p-6 text-center text-amber-800 text-xs">
        <i class="fa-solid fa-spinner fa-spin mr-1"></i> Translating question and executing SQL...
      </div>`;

    try {
      const res = await fetch('/api/nlp/vak-to-sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await res.json();

      if (data.error) {
        tableContainer.innerHTML = `<div class="p-4 text-xs text-red-700 font-mono">${data.details || data.error}</div>`;
        sqlEl.textContent = data.generated_sql || '-- SQL Generation failed';
        return;
      }

      sqlEl.textContent = data.generated_sql;
      timingEl.textContent = `${data.sql_meta.execution_ms} ms (${data.sql_meta.row_count} rows)`;
      renderTable(tableContainer, data.columns, data.rows);

    } catch (e) {
      tableContainer.innerHTML = `<div class="p-4 text-xs text-red-700 font-mono">Execution failed: ${e.message}</div>`;
    }
  }

  // 4. Historical Text-to-Entity Extractor
  async function initNerWorkbench() {
    try {
      const res = await fetch('/api/nlp/sample-passages');
      const data = await res.json();
      samplePassages = data.passages || [];

      const buttonsContainer = document.getElementById('samplePassagesButtons');
      buttonsContainer.innerHTML = samplePassages.map(p => `
        <button onclick="window.loadSamplePassage(${p.id})" class="px-2.5 py-1 rounded bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 transition text-[11px] font-semibold">
          <i class="fa-solid fa-scroll text-amber-700 mr-1"></i> ${p.title}
        </button>
      `).join('');

      if (samplePassages.length > 0) {
        window.loadSamplePassage(1);
      }

      document.getElementById('extractEntitiesBtn').addEventListener('click', extractEntities);

    } catch (e) {
      console.error('Error fetching sample passages:', e);
    }
  }

  window.loadSamplePassage = function (id) {
    const passage = samplePassages.find(p => p.id === id);
    if (!passage) return;
    document.getElementById('nerTextInput').value = passage.text;
    extractEntities();
  };

  async function extractEntities() {
    const text = document.getElementById('nerTextInput').value.trim();
    if (!text) return;

    const resultsBox = document.getElementById('nerResultsBox');
    const passageContainer = document.getElementById('nerHighlightedPassage');
    const badgesContainer = document.getElementById('nerCategoryBadges');
    const cardsGrid = document.getElementById('nerEntityCardsGrid');

    resultsBox.classList.remove('hidden');
    passageContainer.innerHTML = `<div class="text-center p-4 text-amber-800 text-xs"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Cross-referencing against normalized 3NF tables...</div>`;

    try {
      const res = await fetch('/api/nlp/extract-entities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await res.json();

      // Render category badges
      const counts = data.counts_by_type || {};
      badgesContainer.innerHTML = Object.entries(counts).map(([cat, count]) => `
        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold border ${getCategoryColor(cat)}">
          ${cat}: ${count}
        </span>
      `).join('') + `<span class="text-stone-500 font-mono text-[11px] ml-auto">Extracted ${data.total_extracted} Entities</span>`;

      // Render highlighted passage
      const segments = data.highlighted_segments || [];
      passageContainer.innerHTML = segments.map(seg => {
        if (seg.type === 'text') {
          return escapeHtml(seg.content);
        } else {
          return `<mark class="px-1.5 py-0.5 rounded font-bold cursor-pointer transition ${getCategoryHighlight(seg.category)}" title="${seg.category}: ${seg.summary}">
            ${escapeHtml(seg.content)}
          </mark>`;
        }
      }).join('');

      // Render entity cards
      const entities = data.entities || [];
      cardsGrid.innerHTML = entities.map(ent => `
        <div class="bg-white/90 p-3 rounded-lg border border-amber-200 text-xs shadow-sm">
          <div class="flex items-center justify-between mb-1">
            <span class="px-1.5 py-0.2 rounded text-[9px] font-bold uppercase border ${getCategoryColor(ent.category)}">
              ${ent.category}
            </span>
            <span class="font-mono text-[9px] text-stone-400">ID #${ent.db_id}</span>
          </div>
          <h5 class="font-heading font-black text-amber-950 text-xs">${ent.matched_text}</h5>
          <p class="text-[11px] text-stone-600 mt-1">${ent.summary}</p>
        </div>
      `).join('');

    } catch (e) {
      passageContainer.innerHTML = `<div class="p-3 text-red-700 text-xs">Failed to extract entities: ${e.message}</div>`;
    }
  }

  function getCategoryColor(cat) {
    const map = {
      'City': 'bg-amber-100 text-amber-900 border-amber-300',
      'Port': 'bg-sky-100 text-sky-900 border-sky-300',
      'Kingdom': 'bg-amber-200 text-amber-950 border-amber-400',
      'Route': 'bg-orange-100 text-orange-950 border-orange-300',
      'Commodity': 'bg-emerald-100 text-emerald-950 border-emerald-300',
      'Currency': 'bg-yellow-100 text-yellow-950 border-yellow-400',
      'Traveller': 'bg-purple-100 text-purple-950 border-purple-300'
    };
    return map[cat] || 'bg-stone-100 text-stone-800 border-stone-300';
  }

  function getCategoryHighlight(cat) {
    const map = {
      'City': 'bg-amber-200 text-amber-950 hover:bg-amber-300',
      'Port': 'bg-sky-200 text-sky-950 hover:bg-sky-300',
      'Kingdom': 'bg-amber-300 text-amber-950 hover:bg-amber-400',
      'Route': 'bg-orange-200 text-orange-950 hover:bg-orange-300',
      'Commodity': 'bg-emerald-200 text-emerald-950 hover:bg-emerald-300',
      'Currency': 'bg-yellow-200 text-yellow-950 hover:bg-yellow-300',
      'Traveller': 'bg-purple-200 text-purple-950 hover:bg-purple-300'
    };
    return map[cat] || 'bg-stone-200 text-stone-900';
  }

  function renderTable(container, columns, rows) {
    if (!columns || columns.length === 0 || !rows || rows.length === 0) {
      container.innerHTML = `<div class="p-6 text-center text-stone-500 text-xs">Query executed successfully (0 rows returned).</div>`;
      return;
    }

    container.innerHTML = `
      <table class="min-w-full text-xs text-left divide-y divide-amber-200 bg-white">
        <thead class="bg-amber-100/70 text-amber-950 font-bold sticky top-0">
          <tr>
            ${columns.map(col => `<th class="px-3 py-2 whitespace-nowrap border-r border-amber-200 last:border-r-0">${col}</th>`).join('')}
          </tr>
        </thead>
        <tbody class="divide-y divide-amber-100 font-mono text-[11px] text-stone-800">
          ${rows.map(row => `
            <tr class="hover:bg-amber-50/50">
              ${columns.map(col => {
                const val = row[col];
                const displayVal = (typeof val === 'object' && val !== null) ? JSON.stringify(val) : (val === null ? '<span class="text-stone-300">NULL</span>' : escapeHtml(val));
                return `<td class="px-3 py-1.5 whitespace-nowrap border-r border-amber-50 last:border-r-0">${displayVal}</td>`;
              }).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, s => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[s]));
  }

})();
