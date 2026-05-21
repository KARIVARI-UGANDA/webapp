const ROLE_HOME = { tourist: '/', driver: '/driver/dashboard', admin: '/admin/dashboard' };
const token = localStorage.getItem('access_token');
const role  = localStorage.getItem('role');

if (!token) {
	window.location.href = '/owner/login';
} else if (role && role !== 'owner') {
	window.location.href = ROLE_HOME[role] || '/owner/login';
}

document.getElementById('logoutBtn').addEventListener('click', async (e) => {
	e.preventDefault();
	await apiLogout();
	window.location.href = '/owner/login';
});

(async () => {
	if (!token) return;
	try {
		const [meRes, vehiclesRes] = await Promise.all([
			fetch(`${API}/auth/me`,        { headers: { 'Authorization': `Bearer ${token}` } }),
			fetch(`${API}/vehicles/mine`,  { headers: { 'Authorization': `Bearer ${token}` } }),
		]);

		if (meRes.ok) {
			const user = await meRes.json();
			document.getElementById('ownerName').textContent = user.full_name;
		}

		if (vehiclesRes.ok) {
			const vehicles = await vehiclesRes.json();
			document.getElementById('statVehicles').textContent = vehicles.length;

			const pending = vehicles.filter(v => v.status === 'pending_review').length;
			document.getElementById('statPending').textContent = pending;

			const tbody = document.getElementById('vehiclesTableBody');
			if (tbody) {
				tbody.innerHTML = vehicles.length === 0
					? '<tr><td colspan="5" class="text-center py-5 text-secondary">No vehicles yet. Add your first vehicle.</td></tr>'
					: vehicles.map(v => `
						<tr>
							<td class="ps-4 fw-semibold">${v.make} ${v.model} <small class="text-secondary">(${v.year})</small></td>
							<td>${v.registration_plate}</td>
							<td><span class="badge ${statusBadge(v.status)}">${v.status.replace('_', ' ')}</span></td>
							<td>UGX ${(v.base_daily_rate_ugx / 1000).toFixed(0)}k/day</td>
							<td class="text-secondary small">${v.service_area || '—'}</td>
						</tr>`).join('');
			}
		}
	} catch (err) {
		console.error('Dashboard load failed:', err);
	}
})();

function statusBadge(status) {
	const map = {
		verified:       'bg-success bg-opacity-10 text-success',
		pending_review: 'bg-warning bg-opacity-10 text-warning',
		rejected:       'bg-danger  bg-opacity-10 text-danger',
	};
	return map[status] || 'bg-secondary bg-opacity-10 text-secondary';
}

async function loadVehicles() {
	if (!token) return;
	try {
		const res = await fetch(`${API}/vehicles/mine`, { headers: { 'Authorization': `Bearer ${token}` } });
		if (!res.ok) return;
		const vehicles = await res.json();
		document.getElementById('statVehicles').textContent = vehicles.length;
		document.getElementById('statPending').textContent = vehicles.filter(v => v.status === 'pending_review').length;
		const tbody = document.getElementById('vehiclesTableBody');
		if (!tbody) return;
		tbody.innerHTML = vehicles.length === 0
			? '<tr><td colspan="5" class="text-center py-5 text-secondary">No vehicles yet. Add your first vehicle.</td></tr>'
			: vehicles.map(v => `
				<tr>
					<td class="ps-4 fw-semibold">${v.make} ${v.model} <small class="text-secondary">(${v.year})</small></td>
					<td>${v.registration_plate}</td>
					<td><span class="badge ${statusBadge(v.status)}">${v.status.replace('_', ' ')}</span></td>
					<td>UGX ${(v.base_daily_rate_ugx / 1000).toFixed(0)}k/day</td>
					<td class="text-secondary small">${v.service_area || '—'}</td>
				</tr>`).join('');
	} catch (err) {
		console.error('Failed to reload vehicles:', err);
	}
}

document.getElementById('submitVehicleBtn').addEventListener('click', async () => {
	const form    = document.getElementById('addVehicleForm');
	const alertEl = document.getElementById('vehicleFormAlert');
	const btnText = document.getElementById('submitVehicleBtnText');
	const spinner = document.getElementById('submitVehicleSpinner');

	alertEl.className = 'alert d-none mb-3';
	alertEl.textContent = '';

	if (!form.checkValidity()) {
		form.reportValidity();
		return;
	}

	const fd = new FormData(form);
	const payload = {
		make:                  fd.get('make').trim(),
		model:                 fd.get('model').trim(),
		year:                  parseInt(fd.get('year'), 10),
		color:                 fd.get('color').trim(),
		registration_plate:    fd.get('registration_plate').trim(),
		vehicle_type:          fd.get('vehicle_type'),
		transmission:          fd.get('transmission'),
		fuel_type:             fd.get('fuel_type'),
		passenger_capacity:    parseInt(fd.get('passenger_capacity'), 10),
		base_daily_rate_ugx:   parseInt(fd.get('base_daily_rate_ugx'), 10),
		has_ac:                fd.get('has_ac') === 'on',
		has_wifi:              fd.get('has_wifi') === 'on',
		is_4wd:                fd.get('is_4wd') === 'on',
		has_roof_rack:         fd.get('has_roof_rack') === 'on',
		has_child_seat:        fd.get('has_child_seat') === 'on',
	};

	const serviceArea      = fd.get('service_area').trim();
	const rateWithDriver   = fd.get('rate_with_driver_ugx');
	const description      = fd.get('description').trim();
	if (serviceArea)    payload.service_area        = serviceArea;
	if (rateWithDriver) payload.rate_with_driver_ugx = parseInt(rateWithDriver, 10);
	if (description)    payload.description          = description;

	btnText.textContent = 'Submitting…';
	spinner.classList.remove('d-none');
	document.getElementById('submitVehicleBtn').disabled = true;

	try {
		const res = await fetch(`${API}/vehicles/`, {
			method:  'POST',
			headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
			body:    JSON.stringify(payload),
		});

		if (res.ok) {
			bootstrap.Modal.getInstance(document.getElementById('addVehicleModal')).hide();
			form.reset();
			await loadVehicles();
		} else {
			const err = await res.json().catch(() => ({}));
			let msg = 'Submission failed. Please check your inputs.';
			if (err.detail) {
				msg = Array.isArray(err.detail)
					? err.detail.map(e => e.msg).join('; ')
					: err.detail;
			}
			alertEl.textContent = msg;
			alertEl.className = 'alert alert-danger mb-3';
		}
	} catch {
		alertEl.textContent = 'Network error. Please try again.';
		alertEl.className = 'alert alert-danger mb-3';
	} finally {
		btnText.textContent = 'Submit Vehicle';
		spinner.classList.add('d-none');
		document.getElementById('submitVehicleBtn').disabled = false;
	}
});
