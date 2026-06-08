const RATES = { USD: 3700, EUR: 4050 };
const SYMBOLS = { USD: '$', EUR: '€' };

function convertPrice(ugx, currency) {
	const rate = RATES[currency] || RATES.USD;
	return (ugx / rate).toFixed(2);
}

function renderVehicleCards(vehicles, currency) {
	const vehicleContainer = document.getElementById('vehicleCardsContainer');
	if (!vehicleContainer) return;

	if (vehicles.length === 0) {
		vehicleContainer.innerHTML = `
			<div class="col-span-3 text-center py-12">
				<span class="material-symbols-outlined text-[48px] mb-3 d-block" style="color:#c2c9bb;">search_off</span>
				<p class="fw-semibold mb-1" style="color:#42493e;">No vehicles match your search</p>
				<p class="small text-secondary mb-3">Try adjusting your filters or clearing the search.</p>
				<button onclick="clearSearch()" class="btn btn-sm" style="background:#2D5A27;color:white;">Clear filters</button>
			</div>`;
		return;
	}

	const sym = SYMBOLS[currency] || '$';

	vehicleContainer.innerHTML = vehicles.map(v => {
		const primaryPhoto = v.photos && v.photos.length > 0
			? (v.photos.find(p => p.is_primary) || v.photos[0])
			: null;
		const imgSrc = primaryPhoto
			? primaryPhoto.photo_url
			: 'https://via.placeholder.com/600x300?text=' + encodeURIComponent(v.make + ' ' + v.model);
		const price = convertPrice(v.base_daily_rate_ugx, currency);

		const features = [
			`<span class="flex items-center gap-1"><span class="material-symbols-outlined text-base">person</span> ${v.passenger_capacity} Seats</span>`,
			`<span class="flex items-center gap-1"><span class="material-symbols-outlined text-base">settings</span> ${v.transmission}</span>`,
			`<span class="flex items-center gap-1"><span class="material-symbols-outlined text-base">local_gas_station</span> ${v.fuel_type}</span>`,
			v.has_ac   ? `<span class="flex items-center gap-1"><span class="material-symbols-outlined text-base">ac_unit</span> A/C</span>` : '',
			v.has_wifi ? `<span class="flex items-center gap-1"><span class="material-symbols-outlined text-base">wifi</span> WiFi</span>` : '',
			v.is_4wd   ? `<span class="flex items-center gap-1"><span class="material-symbols-outlined text-base">terrain</span> 4WD</span>` : '',
		].filter(Boolean).join('');

		const statusBadge = v.status === 'verified'
			? `<span class="bg-safari-green text-white text-[10px] font-bold px-2.5 py-1 rounded-full inline-flex items-center gap-1 uppercase tracking-wider backdrop-blur-sm">
			     <span class="material-symbols-outlined text-[12px]" style="font-variation-settings:'FILL' 1;">verified</span>Verified
			   </span>`
			: `<span class="bg-status-pending text-white text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">Under Review</span>`;
		const availBadge = v.status === 'verified'
			? `<span class="bg-white/90 text-safari-green text-[10px] font-bold px-2.5 py-1 rounded-full inline-flex items-center gap-1.5 uppercase tracking-wider">
			     <span class="relative flex h-2 w-2 flex-shrink-0"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-success opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-status-success"></span></span>Available
			   </span>`
			: '';

		return `
		<div class="bg-surface-container-lowest rounded-xl shadow-[0px_4px_20px_rgba(0,0,0,0.05)] overflow-hidden group hover:shadow-xl transition-all duration-300">
			<div class="relative h-64 overflow-hidden">
				<img class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
				     src="${imgSrc}" alt="${v.make} ${v.model}">
				<div class="absolute top-4 left-4">${statusBadge}</div>
				${availBadge ? `<div class="absolute bottom-4 right-4">${availBadge}</div>` : ''}
			</div>
			<div class="p-6">
				<div class="flex justify-between items-start mb-2">
					<div>
						<h3 class="font-headline-md text-headline-md text-on-surface">${v.make} ${v.model}</h3>
						<p class="text-on-surface-variant font-label-sm text-label-sm mt-0.5">${v.year} · ${v.vehicle_type} · ${v.service_area || 'Uganda'}</p>
					</div>
				</div>
				<div class="flex flex-wrap gap-4 mb-6 text-on-surface-variant font-label-sm text-label-sm">${features}</div>
				<div class="flex items-center justify-between pt-4 border-t border-outline-variant/30">
					<div>
						<span class="font-headline-md text-headline-md text-safari-green">${sym}${price}</span>
						<span class="font-body-md text-body-md text-on-surface-variant">/ day</span>
					</div>
					<a href="/vehicles/${v.id}" class="bg-safari-green text-white px-6 py-2 rounded-lg font-label-lg text-label-lg font-bold hover:brightness-110 transition-all" style="text-decoration:none;">View Details</a>
				</div>
			</div>
		</div>`;
	}).join('');
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
