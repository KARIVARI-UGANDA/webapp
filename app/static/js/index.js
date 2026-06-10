const RATES = { USD: 3700, EUR: 4050 };
const SYMBOLS = { USD: '$', EUR: '€' };

function convertPrice(ugx, currency) {
	const rate = RATES[currency] || RATES.USD;
	return (ugx / rate).toFixed(2);
}

function toTitle(str) {
	if (!str) return '';
	return str.replace(/\b\w/g, c => c.toUpperCase());
}

function vehicleCardHTML(v) {
  const sym   = SYMBOLS[_currency] || '$';
  const price = convertPrice(v.base_daily_rate_ugx, _currency);

  const primaryPhoto = v.photos && v.photos.length > 0
    ? (v.photos.find(p => p.is_primary) || v.photos[0])
    : null;
  const imgSrc = primaryPhoto
    ? primaryPhoto.photo_url
    : 'https://via.placeholder.com/600x300?text=' + encodeURIComponent(v.make + ' ' + v.model);

  const chip = (icon, label) =>
    `<span class="inline-flex items-center gap-1 text-[13px] font-medium text-on-surface-variant">
      <span class="material-symbols-outlined text-[15px] text-safari-green" style="font-variation-settings:'FILL' 0;">${icon}</span>${label}</span>`;

  const features = [
    chip('person',            `<strong>${v.passenger_capacity}</strong> Seats`),
    chip('settings',          `<strong>${toTitle(v.transmission)}</strong>`),
    chip('local_gas_station', `<strong>${toTitle(v.fuel_type)}</strong>`),
    v.has_ac          ? chip('ac_unit',        'A/C')       : '',
    v.has_wifi        ? chip('wifi',           'WiFi')      : '',
    v.is_4wd          ? chip('terrain',        '4WD')       : '',
    v.has_gps         ? chip('location_on',    'GPS')       : '',
    v.has_bluetooth   ? chip('bluetooth',      'Bluetooth') : '',
    v.has_usb_charger ? chip('usb',            'USB')       : '',
    v.is_pet_friendly ? chip('pets',           'Pet OK')    : '',
  ].filter(Boolean).join('');

  const statusBadge = v.status === 'verified'
    ? `<span class="bg-safari-green text-white text-[10px] font-bold px-3 py-1 rounded-full inline-flex items-center gap-1 uppercase tracking-wider shadow-sm">
         <span class="material-symbols-outlined text-[12px]" style="font-variation-settings:'FILL' 1;">verified</span>Verified
       </span>`
    : `<span class="bg-status-pending text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-sm">Under Review</span>`;

  const availBadge = v.status === 'verified'
    ? `<span class="bg-white/95 text-safari-green text-[10px] font-bold px-3 py-1 rounded-full inline-flex items-center gap-1.5 uppercase tracking-wider shadow-sm">
         <span class="relative flex h-2 w-2 flex-shrink-0">
           <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-success opacity-75"></span>
           <span class="relative inline-flex rounded-full h-2 w-2 bg-status-success"></span>
         </span>Available
       </span>`
    : '';

  const type = toTitle(v.vehicle_type || '');
  const area = toTitle(v.service_area || 'Uganda');

  return `
  <div class="bg-surface-container-lowest rounded-2xl shadow-[0px_4px_20px_rgba(0,0,0,0.06)] overflow-hidden group hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 flex flex-col">
    <div class="relative h-56 overflow-hidden flex-shrink-0">
	 <img class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
		 src="${imgSrc}" alt="${v.make} ${v.model}" loading="eager">
      <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none"></div>
      <div class="absolute top-3 left-3">${statusBadge}</div>
      ${availBadge ? `<div class="absolute bottom-3 right-3">${availBadge}</div>` : ''}
    </div>
    <div class="p-5 flex flex-col flex-1">
      <div class="mb-3">
        <h3 class="font-headline-md text-headline-md text-on-surface font-bold leading-tight">${v.make} ${v.model}</h3>
        <p class="text-on-surface-variant text-[13px] mt-1">
          <span class="font-semibold">${v.year || ''}</span>
          <span class="mx-1 text-outline-variant">·</span>${type}
          <span class="mx-1 text-outline-variant">·</span>${area}
        </p>
      </div>
      <div class="flex flex-wrap gap-x-4 gap-y-2 mb-4">${features}</div>
      <div class="flex items-center justify-between pt-4 border-t border-outline-variant/30 mt-auto">
        <div class="leading-none">
          <span class="text-[22px] font-bold text-primary">${sym}${price}</span>
          <span class="text-[13px] text-on-surface-variant font-medium"> / day</span>
        </div>
        <a href="/vehicles/${v.id}"
           class="border-2 border-primary text-primary px-5 py-2 rounded-xl text-[13px] font-bold hover:bg-primary hover:text-white transition-all"
           style="text-decoration:none;">View Details</a>
      </div>
    </div>
  </div>`;
}

function renderVehicleCards(vehicles, currency) {
	const vehicleContainer = document.getElementById('vehicleCardsContainer');
	if (!vehicleContainer) return;

	if (vehicles.length === 0) {
		vehicleContainer.innerHTML = `
			<div class="col-span-3 text-center py-16 text-on-surface-variant">
				<span class="material-symbols-outlined text-[48px] mb-3 block" style="color:#c2c9bb;">search_off</span>
				<p class="font-semibold mb-1" style="color:#42493e;">No vehicles match your search</p>
				<p class="text-sm mb-3">Try adjusting your filters or clearing the search.</p>
				<button onclick="clearSearch()" class="px-5 py-2 rounded-xl text-white text-sm font-bold" style="background:#2D5A27;">Clear filters</button>
			</div>`;
		return;
	}

	vehicleContainer.innerHTML = vehicles.map(v => vehicleCardHTML(v)).join('');
}

// ── Search state ─────────────────────────────────────────────────────────────
let _allVehicles = [];
let _currency    = 'USD';

function getFilters() {
	return {
		location: (document.getElementById('searchLocation')?.value || '').trim().toLowerCase(),
		type:     (document.getElementById('searchType')?.value || '').trim().toLowerCase(),
		seats:    parseInt(document.getElementById('searchSeats')?.value || '0', 10) || 0,
	};
}

function applySearch() {
	const { location, type, seats } = getFilters();

	const filtered = _allVehicles.filter(v => {
		if (location) {
			const area = (v.service_area || '').toLowerCase();
			const city = (v.city || '').toLowerCase();
			if (!area.includes(location) && !city.includes(location)) return false;
		}
		if (type && v.vehicle_type?.toLowerCase() !== type) return false;
		if (seats && v.passenger_capacity < seats) return false;
		return true;
	});

	// Update heading count
	const heading = document.getElementById('featuredHeading');
	const countEl = document.getElementById('searchResultCount');
	const hasFilter = location || type || seats;

	if (heading) heading.textContent = hasFilter ? 'Search Results' : 'Featured Vehicles';
	if (countEl) countEl.textContent = hasFilter ? `${filtered.length} vehicle${filtered.length !== 1 ? 's' : ''} found` : '';

	renderVehicleCards(filtered.slice(0, 9), _currency);
	renderActiveTags(location, type, seats);

	// Smooth scroll to results
	if (hasFilter) {
		document.getElementById('vehicleCardsContainer')
			?.closest('section')
			?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}
}

function renderActiveTags(location, type, seats) {
	const el = document.getElementById('activeFilters');
	if (!el) return;
	const tags = [];
	if (location) tags.push({ label: location, clear: () => { document.getElementById('searchLocation').value = ''; applySearch(); } });
	if (type)     tags.push({ label: type, clear: () => { document.getElementById('searchType').value = ''; applySearch(); } });
	if (seats)    tags.push({ label: `${seats}+ seats`, clear: () => { document.getElementById('searchSeats').value = ''; applySearch(); } });

	if (tags.length === 0) {
		el.style.display = 'none';
		return;
	}
	el.style.display = 'flex';
	el.innerHTML = tags.map((t, i) =>
		`<span style="background:#f3f3f6;border:1px solid #c2c9bb;border-radius:2rem;font-size:12px;font-weight:600;padding:3px 10px;display:inline-flex;align-items:center;gap:6px;color:#42493e;">
			${t.label}
			<button onclick="(${t.clear.toString()})()" style="background:none;border:none;padding:0;line-height:1;cursor:pointer;color:#72796e;font-size:14px;">&times;</button>
		</span>`
	).join('') + `<button onclick="clearSearch()" style="background:none;border:none;padding:0;font-size:12px;font-weight:600;color:#154212;cursor:pointer;text-decoration:underline;">Clear all</button>`;
}

function clearSearch() {
	const loc  = document.getElementById('searchLocation');
	const type = document.getElementById('searchType');
	const seats = document.getElementById('searchSeats');
	if (loc)  loc.value  = '';
	if (type) type.value = '';
	if (seats) seats.value = '';
	applySearch();
}

// ── Boot ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
	const authButtons = document.getElementById('authButtons');
	const userButtons = document.getElementById('userButtons');
	const logoutBtn   = document.getElementById('logoutBtn');
	const userNameEl  = document.getElementById('userName');

	const token = localStorage.getItem('access_token');

	if (token) {
		try {
			const res = await fetch(`${API}/auth/me`, {
				headers: { 'Authorization': `Bearer ${token}` }
			});
			if (res.ok) {
				const user = await res.json();
				const dashboards = { owner: '/owner/dashboard', admin: '/admin/dashboard' };
				if (dashboards[user.role]) {
					window.location.href = dashboards[user.role];
					return;
				}
				authButtons.classList.add('hidden');
				userButtons.classList.remove('hidden');
				userButtons.classList.add('flex');
				userNameEl.textContent = user.full_name;
			} else {
				localStorage.clear();
			}
		} catch (err) {
			console.error('Auth check failed:', err);
		}
	}

	if (logoutBtn) {
		logoutBtn.addEventListener('click', async () => {
			await apiLogout();
			window.location.href = '/';
		});
	}

	// Currency toggle
	document.querySelectorAll('input[name="currency"]').forEach(radio => {
		radio.addEventListener('change', () => {
			_currency = radio.value;
			applySearch();
		});
	});

	// Live search on input change (debounced)
	let debounceTimer;
	['searchLocation', 'searchType', 'searchSeats'].forEach(id => {
		document.getElementById(id)?.addEventListener('input', () => {
			clearTimeout(debounceTimer);
			debounceTimer = setTimeout(applySearch, 280);
		});
		document.getElementById(id)?.addEventListener('change', applySearch);
	});

	// Form submit — filter in place, don't navigate
	document.getElementById('searchForm')?.addEventListener('submit', e => {
		e.preventDefault();
		applySearch();
	});

	// Load vehicles
	try {
		const res = await fetch(`${API}/vehicles/?page=1&page_size=50`);
		if (res.ok) {
			_allVehicles = await res.json();
			applySearch(); // renders initial featured set
		}
	} catch (err) {
		console.error('Failed to load vehicles:', err);
		const container = document.getElementById('vehicleCardsContainer');
		if (container) container.innerHTML = '<p class="text-center text-danger col-12">Failed to load vehicles.</p>';
	}
});
