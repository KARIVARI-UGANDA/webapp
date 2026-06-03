const ROLE_HOME = { customer: '/', admin: '/admin/dashboard' };
const token = localStorage.getItem('access_token');
const role  = localStorage.getItem('role');

if (!token) {
	window.location.href = '/owner/login';
} else if (role && role !== 'owner') {
	window.location.href = ROLE_HOME[role] || '/owner/login';
}

/** Redirect to login on 401 — token expired */
function handleUnauthorized(res) {
	if (res.status === 401) {
		localStorage.clear();
		window.location.href = '/owner/login';
		return true;
	}
	return false;
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

		if (handleUnauthorized(meRes) || handleUnauthorized(vehiclesRes)) return;

		if (meRes.ok) {
			const user = await meRes.json();
			document.getElementById('ownerName').textContent = user.full_name;
		}

		if (vehiclesRes.ok) {
			const vehicles = await vehiclesRes.json();
			document.getElementById('statVehicles').textContent = vehicles.length;

			// Backend stores 'pending', not 'pending_review'
			const pending = vehicles.filter(v => v.status === 'pending' || v.status === 'pending_review').length;
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
							<td>UGX ${Number(v.base_daily_rate_ugx).toLocaleString()}/day</td>
							<td class="text-secondary small">${v.service_area || '—'}</td>
							<td><button onclick="openEditVehicle('${v.id}')" class="btn btn-sm btn-outline-primary">Edit</button></td>
						</tr>`).join('');
			}

			document.dispatchEvent(new CustomEvent('kv:vehiclesLoaded', { detail: vehicles }));
		}
	} catch (err) {
		console.error('Dashboard load failed:', err);
	}
})();

function statusBadge(status) {
	const map = {
		verified:       'bg-success bg-opacity-10 text-success',
		pending:        'bg-warning bg-opacity-10 text-warning',
		pending_review: 'bg-warning bg-opacity-10 text-warning',
		rejected:       'bg-danger  bg-opacity-10 text-danger',
		suspended:      'bg-secondary bg-opacity-10 text-secondary',
	};
	return map[status] || 'bg-secondary bg-opacity-10 text-secondary';
}

async function loadVehicles() {
	if (!token) return;
	try {
		const res = await fetch(`${API}/vehicles/mine`, { headers: { 'Authorization': `Bearer ${token}` } });
		if (handleUnauthorized(res)) return;
		if (!res.ok) return;
		const vehicles = await res.json();
		document.getElementById('statVehicles').textContent = vehicles.length;
		document.getElementById('statPending').textContent = vehicles.filter(
			v => v.status === 'pending' || v.status === 'pending_review'
		).length;
		const tbody = document.getElementById('vehiclesTableBody');
		if (tbody) {
			tbody.innerHTML = vehicles.length === 0
				? '<tr><td colspan="5" class="text-center py-5 text-secondary">No vehicles yet. Add your first vehicle.</td></tr>'
				: vehicles.map(v => `
					<tr>
						<td class="ps-4 fw-semibold">${v.make} ${v.model} <small class="text-secondary">(${v.year})</small></td>
						<td>${v.registration_plate}</td>
						<td><span class="badge ${statusBadge(v.status)}">${v.status.replace('_', ' ')}</span></td>
						<td>UGX ${Number(v.base_daily_rate_ugx).toLocaleString()}/day</td>
						<td class="text-secondary small">${v.service_area || '—'}</td>
						<td><button onclick="openEditVehicle('${v.id}')" class="btn btn-sm btn-outline-primary">Edit</button></td>
					</tr>`).join('');
		}
		document.dispatchEvent(new CustomEvent('kv:vehiclesLoaded', { detail: vehicles }));
		// If the fleet section is visible, refresh it from the API directly
		const fleetSection = document.getElementById('section-fleet');
		if (fleetSection && fleetSection.style.display !== 'none' && typeof loadFleetData === 'function') {
			await loadFleetData();
		}
	} catch (err) {
		console.error('Failed to reload vehicles:', err);
	}
}

document.getElementById('submitVehicleBtn').addEventListener('click', async () => {
	const form    = document.getElementById('addVehicleForm');
	const alertEl = document.getElementById('vehicleFormAlert');
	const btnText = document.getElementById('submitVehicleBtnText');
	const spinner = document.getElementById('submitVehicleSpinner');
	const isEdit  = !!window._editVehicleId;

	alertEl.className = 'alert d-none mb-3';
	alertEl.textContent = '';

	if (!form.checkValidity()) {
		form.reportValidity();
		return;
	}

	const fd = new FormData(form);

	// Fields valid for both create and update
	const common = {
		make:               fd.get('make').trim(),
		model:              fd.get('model').trim(),
		year:               parseInt(fd.get('year'), 10),
		color:              fd.get('color').trim(),
		vehicle_type:       fd.get('vehicle_type'),
		transmission:       fd.get('transmission'),
		fuel_type:          fd.get('fuel_type'),
		passenger_capacity: parseInt(fd.get('passenger_capacity'), 10),
		base_daily_rate_ugx: parseInt(fd.get('base_daily_rate_ugx'), 10),
		has_ac:             fd.get('has_ac') === 'on',
		has_wifi:           fd.get('has_wifi') === 'on',
		is_4wd:             fd.get('is_4wd') === 'on',
		has_roof_rack:      fd.get('has_roof_rack') === 'on',
		has_child_seat:     fd.get('has_child_seat') === 'on',
	};

	const serviceArea = fd.get('service_area').trim();
	const description = fd.get('description').trim();
	if (serviceArea) common.service_area = serviceArea;
	if (description) common.description  = description;

	// registration_plate is only sent on create (not in VehicleUpdate schema)
	const payload = isEdit
		? common
		: { ...common, registration_plate: fd.get('registration_plate').trim() };

	const url    = isEdit ? `${API}/vehicles/${window._editVehicleId}` : `${API}/vehicles/`;
	const method = isEdit ? 'PATCH' : 'POST';

	btnText.textContent = isEdit ? 'Saving…' : 'Submitting…';
	spinner.classList.remove('d-none');
	document.getElementById('submitVehicleBtn').disabled = true;

	try {
		const res = await fetch(url, {
			method,
			headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
			body:    JSON.stringify(payload),
		});

		if (handleUnauthorized(res)) return;

		if (res.ok) {
			const savedVehicle = await res.json();
			const vehicleId = isEdit ? window._editVehicleId : savedVehicle.id;
			const selectedFiles = Array.from(document.getElementById('vehicleImages').files || []);

			bootstrap.Modal.getInstance(document.getElementById('addVehicleModal'))?.hide();
			form.reset();
			window._editVehicleId = null;

			if (selectedFiles.length > 0 && vehicleId) {
				const photoData = new FormData();
				selectedFiles.forEach(f => photoData.append('files', f));
				const photoRes = await fetch(`${API}/vehicles/${vehicleId}/photos`, {
					method: 'POST',
					headers: { 'Authorization': `Bearer ${token}` },
					body: photoData,
				}).catch(() => null);
				if (photoRes && !photoRes.ok) {
					const photoErr = await photoRes.json().catch(() => ({}));
					alertEl.textContent = 'Saved, but photo upload failed: ' + (photoErr.detail || 'Unknown error');
					alertEl.className = 'alert alert-warning mb-3';
				}
			}

			await loadVehicles();
		} else {
			const err = await res.json().catch(() => ({}));
			let msg = isEdit ? 'Update failed. Please check your inputs.' : 'Submission failed. Please check your inputs.';
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
		btnText.textContent = isEdit ? 'Save Changes' : 'Submit Vehicle';
		spinner.classList.add('d-none');
		document.getElementById('submitVehicleBtn').disabled = false;
	}
});
