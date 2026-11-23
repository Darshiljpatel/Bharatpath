/**
 * BharatPath - Vis.js Trade & Cultural Diffusion Network Graph Handler
 */

(function () {
  let network = null;
  let nodesDataSet = null;
  let edgesDataSet = null;
  let physicsEnabled = true;

  document.addEventListener('DOMContentLoaded', () => {
    initNetwork();
    setupControls();
  });

  function setupControls() {
    const toggleBtn = document.getElementById('togglePhysicsBtn');
    const resetBtn = document.getElementById('resetGraphZoomBtn');

    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        physicsEnabled = !physicsEnabled;
        if (network) {
          network.setOptions({ physics: { enabled: physicsEnabled } });
        }
        toggleBtn.innerHTML = physicsEnabled 
          ? '<i class="fa-solid fa-pause text-[10px]"></i> Freeze Physics'
          : '<i class="fa-solid fa-play text-[10px]"></i> Resume Physics';
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        if (network) network.fit({ animation: { duration: 800, easingFunction: 'easeInOutQuad' } });
      });
    }
  }

  async function initNetwork() {
    const container = document.getElementById('networkGraphContainer');
    if (!container) return;

    try {
      const res = await fetch('/api/analytics/network');
      const data = await res.json();

      // Update KPI counters
      if (data.kpis) {
        document.getElementById('kpiCities').textContent = data.kpis.total_cities || 0;
        document.getElementById('kpiPorts').textContent = data.kpis.total_ports || 0;
        document.getElementById('kpiKingdoms').textContent = data.kpis.total_kingdoms || 0;
        document.getElementById('kpiCommodities').textContent = data.kpis.total_commodities || 0;
        document.getElementById('kpiExchanges').textContent = data.kpis.total_cultural_exchanges || 0;
      }

      nodesDataSet = new vis.DataSet(data.nodes || []);
      edgesDataSet = new vis.DataSet(data.edges || []);

      const graphData = {
        nodes: nodesDataSet,
        edges: edgesDataSet
      };

      const options = {
        nodes: {
          font: {
            face: 'Inter',
            size: 12,
            color: '#1E293B',
            strokeWidth: 2,
            strokeColor: '#FFFFFF'
          },
          borderWidth: 2,
          shadow: true
        },
        edges: {
          font: {
            size: 10,
            face: 'Inter',
            align: 'middle',
            background: 'rgba(255, 253, 247, 0.85)',
            strokeWidth: 0
          },
          smooth: {
            type: 'continuous',
            roundness: 0.2
          }
        },
        physics: {
          enabled: true,
          solver: 'forceAtlas2Based',
          forceAtlas2Based: {
            gravitationalConstant: -40,
            centralGravity: 0.015,
            springLength: 90,
            springConstant: 0.08
          },
          stabilization: {
            iterations: 150
          }
        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
          zoomView: true
        }
      };

      network = new vis.Network(container, graphData, options);

      // Handle Node Selection / Inspection
      network.on('click', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = nodesDataSet.get(nodeId);
          showNodeDetails(node, params.edges);
        }
      });

    } catch (e) {
      console.error('Failed to initialize network graph:', e);
    }
  }

  function showNodeDetails(node, connectedEdgeIds) {
    const box = document.getElementById('nodeDetailsBox');
    if (!box || !node) return;

    const connectedEdges = edgesDataSet.get(connectedEdgeIds);
    const connectionList = connectedEdges.map(edge => {
      const isSource = edge.from === node.id;
      const otherId = isSource ? edge.to : edge.from;
      const otherNode = nodesDataSet.get(otherId);
      const otherLabel = otherNode ? otherNode.label : otherId;
      return `<li class="flex items-center justify-between py-1 border-b border-amber-100 last:border-b-0 text-[11px]">
        <span><strong class="text-amber-900">${isSource ? '➔' : '⬅'} ${edge.label || 'Connected'}:</strong> ${otherLabel}</span>
      </li>`;
    }).join('');

    box.innerHTML = `
      <div class="bg-amber-50 p-3.5 rounded-lg border border-amber-300">
        <div class="flex items-center justify-between mb-2">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-200 text-amber-900">
            ${node.group || 'Node'}
          </span>
          <span class="font-mono text-[10px] text-stone-500">${node.id}</span>
        </div>
        <h4 class="font-heading font-black text-amber-950 text-base mb-1">${node.label}</h4>
        <p class="text-stone-700 text-xs mb-3 font-serif-sub italic">${node.title || 'Historical asset in the trade topology.'}</p>

        <div class="border-t border-amber-200 pt-2">
          <span class="font-bold text-amber-950 text-xs block mb-1">Direct Network Linkages (${connectedEdges.length}):</span>
          <ul class="space-y-0.5 max-h-[220px] overflow-y-auto">
            ${connectionList || '<li class="text-stone-400 text-xs">No direct edges detected</li>'}
          </ul>
        </div>
      </div>
    `;
  }

})();
