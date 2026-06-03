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
		vehicleContainer.innerHTML = '<p class="col-span-3 text-center py-8 text-on-surface-variant">No vehicles available yet.</p>';
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

		const actionBtn = `<a href="/vehicles/${v.id}" class="bg-safari-green text-white px-6 py-2 rounded-lg font-label-lg text-label-lg font-bold hover:brightness-110 transition-all" style="text-decoration:none;">View Details</a>`;

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
					${actionBtn}
				</div>
			</div>
		</div>`;
	}).join('');
}

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

	let _allVehicles  = [];
	let _shown        = [];
	let _currency     = 'USD';

	function getCurrentCurrency() {
		const checked = document.querySelector('input[name="currency"]:checked');
		return checked ? checked.value : 'USD';
	}

	function applySearch() {
		const location = (document.getElementById('searchLocation')?.value || '').trim().toLowerCase();
		const type     = (document.getElementById('searchType')?.value || '').trim().toLowerCase();
		const resultEl = document.getElementById('searchResultCount');
		const heading  = document.getElementById('featuredHeading');

		_shown = _allVehicles.filter(v => {
			if (location && !(v.service_area || '').toLowerCase().includes(location)) return false;
			if (type     && v.vehicle_type.toLowerCase() !== type) return false;
			return true;
		});

		const isFiltered = location || type;
		if (heading) heading.textContent = isFiltered ? 'Search Results' : 'Featured Vehicles';
		if (resultEl) {
			resultEl.textContent = isFiltered
				? `${_shown.length} vehicle${_shown.length !== 1 ? 's' : ''} found`
				: '';
		}

		renderVehicleCards(_shown, getCurrentCurrency());
		document.getElementById('vehicleCardsContainer')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	// Currency toggle
	document.querySelectorAll('input[name="currency"]').forEach(radio => {
		radio.addEventListener('change', () => {
			_currency = radio.value;
			renderVehicleCards(_shown, _currency);
		});
	});

	// Search form
	document.getElementById('searchForm')?.addEventListener('submit', e => {
		e.preventDefault();
		applySearch();
	});

	// Load featured vehicles
	try {
		const res = await fetch(`${API}/vehicles/?page=1&page_size=50`);
		if (res.ok) {
			_allVehicles = await res.json();
			_shown = _allVehicles.slice(0, 6);

			// Populate type dropdown from real data
			const typeSelect = document.getElementById('searchType');
			if (typeSelect) {
				const types = [...new Set(_allVehicles.map(v => v.vehicle_type).filter(Boolean))].sort();
				types.forEach(t => {
					const opt = document.createElement('option');
					opt.value = t;
					opt.textContent = t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
					typeSelect.appendChild(opt);
				});
			}

			renderVehicleCards(_shown, 'USD');
		}
	} catch (err) {
		console.error('Failed to load vehicles:', err);
		const vehicleContainer = document.getElementById('vehicleCardsContainer');
		if (vehicleContainer) {
			vehicleContainer.innerHTML = '<p class="text-center text-danger col-12">Failed to load vehicles.</p>';
		}
	}
});
