/**
 * Bharata-Manchitra Interactive Historical Map & Multi-Hop Path Finder
 */

(function () {
  let map;
  let cityMarkersLayer;
  let routeLinesLayer;
  let pathfinderHighlightLayer;
  let isPlaying = false;
  let playInterval = null;
  let allCitiesData = [];

  document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initControls();
    loadCitiesForDropdown();
    loadMapData();
  });

  function initMap() {
    // Center on Indian Subcontinent
    map = L.map('manchitraMap', {
      center: [22.8, 79.5],
      zoom: 5,
      minZoom: 4,
      maxZoom: 10
    });

    // 100% Free OpenStreetMap public raster tiles (Zero API key required, no watermark)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors | BharatPath IKS',
      maxZoom: 19
    }).addTo(map);

    cityMarkersLayer = L.layerGroup().addTo(map);
    routeLinesLayer = L.layerGroup().addTo(map);
    pathfinderHighlightLayer = L.layerGroup().addTo(map);
  }

  function initControls() {
    const slider = document.getElementById('eraSlider');
    const display = document.getElementById('currentYearDisplay');
    const resetBtn = document.getElementById('resetEraBtn');
    const playBtn = document.getElementById('playTimelineBtn');
    const routeSelect = document.getElementById('routeTypeSelect');
    const pathForm = document.getElementById('routeFinderForm');
    const vivaPresetBtn = document.getElementById('quickTaxilaMuzirisBtn');

    if (slider) {
      slider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        display.textContent = formatYear(val);
        loadMapData(val, routeSelect ? routeSelect.value : 'All');
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        stopPlayback();
        display.textContent = 'All Antiquity';
        loadMapData(null, routeSelect ? routeSelect.value : 'All');
      });
    }

    if (playBtn) {
      playBtn.addEventListener('click', () => {
        if (isPlaying) {
          stopPlayback();
        } else {
          startPlayback();
        }
      });
    }

    if (routeSelect) {
      routeSelect.addEventListener('change', () => {
        const year = display.textContent === 'All Antiquity' ? null : parseInt(slider.value);
        loadMapData(year, routeSelect.value);
      });
    }

    if (pathForm) {
      pathForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const fromId = document.getElementById('originCitySelect').value;
        const toId = document.getElementById('destCitySelect').value;
        if (!fromId || !toId) {
          alert('Please select both Origin and Destination cities.');
          return;
        }
        computeTradeRoute(fromId, toId);
      });
    }

    if (vivaPresetBtn) {
      vivaPresetBtn.addEventListener('click', () => {
        const originSelect = document.getElementById('originCitySelect');
        const destSelect = document.getElementById('destCitySelect');
        
        let taxilaOption = Array.from(originSelect.options).find(o => o.text.includes('Taxila') || o.text.includes('Takshashila') || o.value === 'CT005');
        let muzirisOption = Array.from(destSelect.options).find(o => o.text.includes('Muziris') || o.text.includes('Muciri') || o.value === 'CT051');
        
        if (taxilaOption) originSelect.value = taxilaOption.value;
        if (muzirisOption) destSelect.value = muzirisOption.value;
        
        if (originSelect.value && destSelect.value) {
          computeTradeRoute(originSelect.value, destSelect.value);
        }
      });
    }
  }

  function formatYear(year) {
    if (year < 0) return `${Math.abs(year)} BCE`;
    if (year === 0) return `1 CE`;
    return `${year} CE`;
  }

  function startPlayback() {
    isPlaying = true;
    const playBtn = document.getElementById('playTimelineBtn');
    playBtn.innerHTML = '<i class="fa-solid fa-pause text-[10px]"></i> Pause';
    playBtn.classList.replace('bg-amber-700', 'bg-red-700');

    const slider = document.getElementById('eraSlider');
    playInterval = setInterval(() => {
      let current = parseInt(slider.value);
      if (current >= 1200) current = -600;
      else current += 100;
      slider.value = current;
      slider.dispatchEvent(new Event('input'));
    }, 1600);
  }

  function stopPlayback() {
    isPlaying = false;
    clearInterval(playInterval);
    const playBtn = document.getElementById('playTimelineBtn');
    if (playBtn) {
      playBtn.innerHTML = '<i class="fa-solid fa-play text-[10px]"></i> Play Era';
      playBtn.classList.replace('bg-red-700', 'bg-amber-700');
    }
  }

  async function loadCitiesForDropdown() {
    try {
      const res = await fetch('/api/cities/list');
      const data = await res.json();
      allCitiesData = data.data || [];

      const originSelect = document.getElementById('originCitySelect');
      const destSelect = document.getElementById('destCitySelect');

      allCitiesData.forEach(c => {
        const opt1 = new Option(`${c.classical_name} (${c.modern_name})`, c.city_id);
        const opt2 = new Option(`${c.classical_name} (${c.modern_name})`, c.city_id);
        originSelect.add(opt1);
        destSelect.add(opt2);
      });
    } catch (e) {
      console.error('Error loading cities list:', e);
    }
  }

  async function loadMapData(year = null, routeType = 'All') {
    let url = '/api/map-data?';
    if (year !== null) url += `year=${year}&`;
    if (routeType && routeType !== 'All') url += `route_type=${routeType}&`;

    try {
      const res = await fetch(url);
      const data = await res.json();

      renderCities(data.cities || []);
      renderRoutes(data.routes || []);
      updatePills(data);
    } catch (e) {
      console.error('Failed to load map data:', e);
    }
  }

  function updatePills(data) {
    const cities = data.cities || [];
    const routes = data.routes || [];
    const kingdoms = data.kingdoms || [];

    const portCount = cities.filter(c => c.is_port).length;
    const inlandCount = cities.length - portCount;

    document.getElementById('cityCountPill').textContent = cities.length;
    document.getElementById('portCountPill').textContent = portCount;
    document.getElementById('routeCountPill').textContent = routes.length;
    document.getElementById('kingdomCountPill').textContent = kingdoms.length;
  }

  function renderCities(cities) {
    cityMarkersLayer.clearLayers();

    cities.forEach(city => {
      const isPort = city.is_port;
      const markerHtml = `
        <div class="custom-city-marker ${isPort ? 'marker-port' : 'marker-inland'}" style="width: 26px; height: 26px; font-size: 11px;">
          <i class="${isPort ? 'fa-solid fa-anchor' : 'fa-solid fa-landmark'}"></i>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'city-div-icon',
        html: markerHtml,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
        popupAnchor: [0, -14]
      });

      const marker = L.marker([parseFloat(city.latitude), parseFloat(city.longitude)], { icon: customIcon });

      // Build Rich IKS Popup
      const rulingKingdoms = (city.controlling_kingdoms && city.controlling_kingdoms.length > 0)
        ? city.controlling_kingdoms.map(k => k.kingdom_name).join(', ')
        : 'Autonomous / Regional Confederacy';

      let metaExcerpt = '';
      if (city.artefact_metadata) {
        if (city.artefact_metadata.unesco_site_id) {
          metaExcerpt += `<div class="text-[11px] text-amber-800"><strong>UNESCO Site ID:</strong> #${city.artefact_metadata.unesco_site_id}</div>`;
        }
        if (city.artefact_metadata.greek_name) {
          metaExcerpt += `<div class="text-[11px] text-stone-600"><strong>Greco-Roman Name:</strong> ${city.artefact_metadata.greek_name}</div>`;
        }
        if (city.artefact_metadata.astronomy_meridian) {
          metaExcerpt += `<div class="text-[11px] text-stone-600"><strong>Astronomical Note:</strong> ${city.artefact_metadata.astronomy_meridian}</div>`;
        }
      }

      const popupHtml = `
        <div class="p-1 max-w-[270px]">
          <div class="flex items-center justify-between border-b border-amber-300 pb-1.5 mb-2">
            <div>
              <h4 class="font-heading font-black text-amber-950 text-base leading-tight">${city.classical_name}</h4>
              <p class="text-xs text-stone-600 font-semibold">${city.modern_name} &bull; ${city.region}</p>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isPort ? 'bg-sky-100 text-sky-900 border border-sky-300' : 'bg-amber-100 text-amber-900 border border-amber-300'}">
              ${isPort ? 'Maritime Port' : 'Inland Hub'}
            </span>
          </div>

          <p class="text-xs text-stone-700 leading-relaxed mb-2 font-serif-sub italic">
            "${city.historical_significance || 'Historical trading nexus.'}"
          </p>

          <div class="space-y-1 text-xs mb-3 bg-amber-50/70 p-2 rounded border border-amber-200">
            <div><strong class="text-amber-900">Rulers:</strong> <span class="text-stone-800">${rulingKingdoms}</span></div>
            <div><strong class="text-amber-900">Active Era:</strong> <span class="font-mono text-stone-800">${formatYear(city.era_start_year)} to ${formatYear(city.era_end_year)}</span></div>
            ${isPort ? `<div><strong class="text-amber-900">Water Body:</strong> <span class="text-stone-800">${city.water_body}</span></div>` : ''}
            ${metaExcerpt}
          </div>

          <div class="pt-1 flex items-center justify-between">
            <button onclick="window.openPramanaModal('city', '${city.city_id}')" class="badge-pramana">
              <i class="fa-solid fa-scroll text-amber-600"></i> Pramāṇa Citations (${city.pramana_citation_count})
            </button>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      cityMarkersLayer.addLayer(marker);
    });
  }

  function renderRoutes(routes) {
    routeLinesLayer.clearLayers();

    routes.forEach(route => {
      const stops = route.stops || [];
      if (stops.length < 2) return;

      const latlngs = stops.map(s => [parseFloat(s.latitude), parseFloat(s.longitude)]);
      const isMaritime = route.route_type === 'Maritime';
      const isRiverine = route.route_type === 'Riverine';

      const polylineOptions = {
        color: isMaritime ? '#1E293B' : (isRiverine ? '#0D9488' : '#B45309'),
        weight: isMaritime ? 3.5 : 4,
        opacity: 0.85,
        dashArray: isMaritime ? '8, 8' : (isRiverine ? '3, 6' : null),
        lineJoin: 'round'
      };

      const line = L.polyline(latlngs, polylineOptions);

      // Commodity Badges
      const commodities = route.commodities || [];
      const commTags = commodities.map(c => 
        `<span class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-900 text-[10px] font-bold border border-emerald-300">${c.commodity_name.split(' ')[0]}</span>`
      ).join(' ');

      const popupHtml = `
        <div class="p-1 max-w-[260px]">
          <h4 class="font-heading font-bold text-amber-950 text-sm border-b border-amber-300 pb-1 mb-1.5">${route.route_name}</h4>
          <p class="text-xs text-stone-600 mb-2"><strong>Modality:</strong> ${route.route_type} Corridor &bull; <strong>Mode:</strong> ${route.primary_transport_mode}</p>
          <div class="text-xs mb-2 text-stone-700">
            <strong>Traded Commodities:</strong>
            <div class="flex flex-wrap gap-1 mt-1">${commTags || '<span class="text-stone-400">Varied bulk goods</span>'}</div>
          </div>
          <button onclick="window.openPramanaModal('route', '${route.route_id}')" class="badge-pramana text-[11px]">
            <i class="fa-solid fa-scroll"></i> Classical Route Citations
          </button>
        </div>
      `;

      line.bindPopup(popupHtml);
      routeLinesLayer.addLayer(line);
    });
  }

  async function computeTradeRoute(fromCityId, toCityId) {
    const resultsBox = document.getElementById('pathfinderResults');
    const waypointsContainer = document.getElementById('pathWaypointsList');
    const tagsContainer = document.getElementById('pathCommoditiesTags');
    const totalDistEl = document.getElementById('pathTotalDist');
    const hopsBadge = document.getElementById('pathHopsBadge');

    resultsBox.classList.remove('hidden');
    waypointsContainer.innerHTML = `
      <div class="text-center p-4 text-amber-800">
        <i class="fa-solid fa-spinner fa-spin mr-1"></i> Running Recursive CTE trade path search...
      </div>`;

    try {
      const res = await fetch(`/api/route-finder?from_city=${fromCityId}&to_city=${toCityId}`);
      const data = await res.json();
      const paths = data.paths || [];

      if (paths.length === 0) {
        waypointsContainer.innerHTML = `
          <div class="p-3 text-amber-900 bg-amber-100/50 rounded border border-amber-300">
            No connected trade path discovered within maximum hop threshold.
          </div>`;
        pathfinderHighlightLayer.clearLayers();
        return;
      }

      const optimal = paths[0];
      hopsBadge.textContent = `${optimal.path_hops} Hops`;
      totalDistEl.textContent = `${optimal.total_distance_km} km`;

      // Highlight on Map
      pathfinderHighlightLayer.clearLayers();
      const pathCoords = optimal.ordered_stops.map(s => [parseFloat(s.latitude), parseFloat(s.longitude)]);

      // Outer glow polyline
      const glowLine = L.polyline(pathCoords, {
        color: '#D97706',
        weight: 9,
        opacity: 0.5,
        lineCap: 'round'
      });

      // Inner crisp path polyline
      const pathLine = L.polyline(pathCoords, {
        color: '#DC2626',
        weight: 5,
        opacity: 0.95,
        lineCap: 'round'
      });

      pathfinderHighlightLayer.addLayer(glowLine);
      pathfinderHighlightLayer.addLayer(pathLine);
      map.fitBounds(pathLine.getBounds(), { padding: [40, 40] });

      // Render Step-by-Step Waypoint Timeline
      waypointsContainer.innerHTML = optimal.ordered_stops.map((stop, index) => `
        <div class="relative pl-6 pb-3 border-l-2 border-amber-600 last:border-l-0 last:pb-0">
          <div class="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-amber-800 text-amber-100 flex items-center justify-center text-[9px] font-bold">
            ${index + 1}
          </div>
          <div>
            <div class="flex items-center justify-between">
              <span class="font-bold text-amber-950 font-heading text-xs">${stop.classical_name}</span>
              <span class="text-[10px] text-stone-500">${stop.modern_name}</span>
            </div>
            <p class="text-[11px] text-stone-600 mt-0.5">
              <span class="text-amber-800 font-semibold">Dynasty:</span> ${stop.ruling_kingdoms}
            </p>
            <p class="text-[10px] text-stone-500">
              <span class="text-amber-800 font-semibold">Coinage:</span> ${stop.circulating_currencies}
            </p>
          </div>
        </div>
      `).join('');

      // Render Commodities
      const commodities = optimal.commodities || [];
      if (commodities.length > 0) {
        tagsContainer.innerHTML = commodities.map(c => `
          <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300 font-bold text-[10px]">
            ${c.commodity_name} (${c.trade_direction})
          </span>
        `).join('');
      } else {
        tagsContainer.innerHTML = `<span class="text-stone-500 text-[11px]">Local staples and bullion</span>`;
      }

    } catch (e) {
      waypointsContainer.innerHTML = `
        <div class="text-red-700 p-2">Failed to calculate route: ${e.message}</div>`;
    }
  }

})();
