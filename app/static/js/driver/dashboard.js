const ROLE_HOME = { tourist: '/', owner: '/owner/dashboard', admin: '/admin/dashboard' };
const token = localStorage.getItem('access_token');
const role  = localStorage.getItem('role');

if (!token) {
	window.location.href = '/driver/login';
} else if (role && role !== 'driver') {
	window.location.href = ROLE_HOME[role] || '/driver/login';
}

document.getElementById('logoutBtn').addEventListener('click', async (e) => {
	e.preventDefault();
	await apiLogout();
	window.location.href = '/driver/login';
});

(async () => {
	if (!token) return;
	try {
		const meRes = await fetch(`${API}/auth/me`, { headers: { 'Authorization': `Bearer ${token}` } });
		if (meRes.ok) {
			const user = await meRes.json();
			document.getElementById('driverName').textContent = user.full_name;
		}

		const [profileRes, trainingRes] = await Promise.all([
			fetch(`${API}/drivers/me/profile`,  { headers: { 'Authorization': `Bearer ${token}` } }),
			fetch(`${API}/drivers/me/training`,  { headers: { 'Authorization': `Bearer ${token}` } }),
		]);

		if (profileRes.ok) {
			const profile = await profileRes.json();
			const statusEl = document.getElementById('verificationStatus');
			const colors = { verified: 'success', pending: 'warning', rejected: 'danger' };
			const color = colors[profile.verification_status] || 'secondary';
			statusEl.innerHTML = `<span class="badge bg-${color} bg-opacity-15 text-${color} fw-semibold px-3 py-2">
				<i class="bi bi-patch-check me-1"></i>${profile.verification_status.toUpperCase()}
			</span>`;
			document.getElementById('statCompleted').textContent = profile.total_trips ?? '0';
		}

		if (trainingRes.ok) {
			const modules = await trainingRes.json();
			const completed = modules.filter(m => m.completed).length;
			const total = modules.length;
			document.getElementById('statTraining').textContent = `${completed}/${total}`;
			document.getElementById('trainingBadge').textContent =
				completed === total && total > 0 ? 'Complete' : `${completed} of ${total} done`;

			const trainingEl = document.getElementById('trainingList');
			trainingEl.innerHTML = total === 0
				? '<div class="text-center py-4 text-secondary">No training modules available yet.</div>'
				: modules.map(m => `
					<div class="d-flex align-items-center gap-3 py-3 border-bottom">
						<i class="bi ${m.completed ? 'bi-check-circle-fill text-success' : 'bi-circle text-secondary'} fs-5"></i>
						<div class="flex-grow-1">
							<div class="fw-semibold">${m.title}</div>
							${m.description ? `<div class="text-secondary small">${m.description}</div>` : ''}
						</div>
						${m.completed
							? '<span class="badge bg-success bg-opacity-10 text-success">Done</span>'
							: '<span class="badge bg-secondary bg-opacity-10 text-secondary">Pending</span>'}
					</div>`).join('');
		}
	} catch (err) {
		console.error('Driver dashboard load failed:', err);
	}
})();

(async () => {
	if (!token) return;
	try {
		const res = await fetch(`${API}/drivers/me/trips?status=upcoming`, {
			headers: { 'Authorization': `Bearer ${token}` }
		});
		if (res.ok) {
			const data = await res.json();
			document.getElementById('statUpcoming').textContent = data.total ?? '0';
		}
	} catch (_) {}
})();
