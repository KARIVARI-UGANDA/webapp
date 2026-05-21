const ROLE_HOME = { tourist: '/', owner: '/owner/dashboard', driver: '/driver/dashboard' };
const token = localStorage.getItem('access_token');
const role  = localStorage.getItem('role');

if (!token) {
	window.location.href = '/admin/login';
} else if (role && role !== 'admin') {
	window.location.href = ROLE_HOME[role] || '/admin/login';
}

document.getElementById('logoutBtn').addEventListener('click', async (e) => {
	e.preventDefault();
	await apiLogout();
	window.location.href = '/admin/login';
});

// Live stats from DB
(async () => {
	if (!token) return;
	try {
		const res = await fetch(`${API}/admin/stats`, { headers: { 'Authorization': `Bearer ${token}` } });
		if (res.ok) {
			const stats = await res.json();
			document.getElementById('statUsers').textContent    = stats.total_users;
			document.getElementById('statVehicles').textContent = stats.active_vehicles;
			document.getElementById('statDisputes').textContent = stats.open_disputes;
			document.getElementById('statPending').textContent  = stats.pending_verifications;
		}
	} catch (_) {}
})();

// Pending verifications list
(async () => {
	if (!token) return;
	const el      = document.getElementById('verificationsList');
	const countEl = document.getElementById('pendingCount');
	try {
		const res = await fetch(`${API}/admin/verifications/pending?type=vehicle&page_size=5`, {
			headers: { 'Authorization': `Bearer ${token}` }
		});
		if (res.ok) {
			const list = await res.json();
			countEl.textContent = list.length + ' pending';
			if (list.length === 0) {
				el.innerHTML = '<div class="text-center py-4 text-secondary">No pending verifications.</div>';
			} else {
				document.getElementById('pendingDot').style.display = 'inline-block';
				el.innerHTML = list.map(v => `
					<div class="d-flex align-items-center justify-content-between py-3 border-bottom">
						<div>
							<span class="fw-semibold">${v.make} ${v.model}</span>
							<span class="text-secondary ms-2 small">${v.registration_plate}</span>
						</div>
						<span class="badge bg-warning bg-opacity-15 text-warning">Pending</span>
					</div>`).join('');
			}
		} else {
			el.innerHTML = '<div class="text-center py-4 text-secondary">Could not load verifications.</div>';
			countEl.textContent = '—';
		}
	} catch (_) {
		el.innerHTML = '<div class="text-center py-4 text-secondary">Could not load verifications.</div>';
	}
})();

// Recent users table
(async () => {
	if (!token) return;
	const el = document.getElementById('recentUsersList');
	if (!el) return;
	try {
		const res = await fetch(`${API}/admin/users?page_size=5`, {
			headers: { 'Authorization': `Bearer ${token}` }
		});
		if (res.ok) {
			const users = await res.json();
			if (users.length === 0) {
				el.innerHTML = '<div class="text-center py-4 text-secondary">No users yet.</div>';
			} else {
				el.innerHTML = `
					<div class="table-responsive">
						<table class="table table-hover mb-0">
							<thead class="table-light">
								<tr><th class="ps-4">Name</th><th>Email</th><th>Role</th><th>Status</th></tr>
							</thead>
							<tbody>
								${users.map(u => `
									<tr>
										<td class="ps-4 fw-semibold">${u.full_name}</td>
										<td class="text-secondary small">${u.email}</td>
										<td><span class="badge bg-secondary bg-opacity-10 text-secondary text-capitalize">${u.role}</span></td>
										<td><span class="badge ${u.is_active
											? 'bg-success bg-opacity-10 text-success'
											: 'bg-danger bg-opacity-10 text-danger'}">${u.is_active ? 'Active' : 'Suspended'}</span></td>
									</tr>`).join('')}
							</tbody>
						</table>
					</div>`;
			}
		}
	} catch (_) {}
})();
