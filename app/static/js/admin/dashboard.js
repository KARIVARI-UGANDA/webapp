const token = localStorage.getItem('access_token');
const role  = localStorage.getItem('role');

// Auth guard
if (!token) {
	window.location.href = '/admin/login';
} else if (role && role !== 'admin') {
	const homes = { customer: '/', owner: '/owner/dashboard', driver: '/driver/dashboard' };
	window.location.href = homes[role] || '/admin/login';
}

// Show logged-in name
const nameEl = document.getElementById('adminName');
if (nameEl) nameEl.textContent = localStorage.getItem('full_name') || 'Admin';

// Logout
document.getElementById('logoutBtn').addEventListener('click', async (e) => {
	e.preventDefault();
	await apiLogout();
	window.location.href = '/admin/login';
});

const authHeaders = { 'Authorization': `Bearer ${token}` };

// ── Stats ──────────────────────────────────────────────────────────────────────
(async () => {
	try {
		const res = await fetch(`${API}/admin/stats`, { headers: authHeaders });
		if (!res.ok) return;
		const s = await res.json();

		setText('statUsers',    s.total_users);
		setText('statVehicles', s.active_vehicles);
		setText('statDisputes', s.open_disputes);
		setText('statPending',  s.pending_verifications);

		// active bookings not in stats yet — show disputes as placeholder until booking API exists
		setText('statBookings', s.open_disputes ?? '—');

		const pendingBadge = document.getElementById('statPendingBadge');
		if (pendingBadge) {
			pendingBadge.textContent = s.pending_verifications > 0 ? 'High Priority' : 'Clear';
			pendingBadge.className   = s.pending_verifications > 0
				? 'text-status-pending text-label-sm font-label-sm'
				: 'text-status-success text-label-sm font-label-sm';
		}
	} catch (_) {}
})();

// ── Pending Vehicle Inspections ────────────────────────────────────────────────
(async () => {
	const tbody    = document.getElementById('vehicleTableBody');
	const countEl  = document.getElementById('pendingCount');
	const dotEl    = document.getElementById('pendingDot');
	try {
		const res = await fetch(`${API}/admin/verifications/pending?type=vehicle&page_size=8`, { headers: authHeaders });
		if (!res.ok) throw new Error();

		const list = await res.json();
		if (countEl) countEl.textContent = `${list.length} pending`;
		if (dotEl && list.length > 0) dotEl.classList.remove('hidden');

		if (!tbody) return;
		if (list.length === 0) {
			tbody.innerHTML = emptyRow(4, 'No pending vehicle inspections.');
			return;
		}

		tbody.innerHTML = list.map(v => `
			<tr class="hover:bg-surface/50 transition-colors">
				<td class="px-4 py-4">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center">
							<span class="material-symbols-outlined text-safari-green text-[20px]">directions_car</span>
						</div>
						<span class="font-label-lg text-label-lg text-on-surface">${esc(v.make)} ${esc(v.model)}</span>
					</div>
				</td>
				<td class="px-4 py-4 text-on-surface-variant">${esc(v.registration_plate)}</td>
				<td class="px-4 py-4 text-on-surface-variant">${v.year ?? '—'}</td>
				<td class="px-4 py-4">
					<span class="bg-status-pending/10 text-status-pending text-[10px] font-bold px-2 py-1 rounded-full uppercase">Pending</span>
				</td>
			</tr>`).join('');
	} catch (_) {
		if (tbody) tbody.innerHTML = emptyRow(4, 'Could not load verifications.');
		if (countEl) countEl.textContent = '—';
	}
})();

// ── Recent Users ───────────────────────────────────────────────────────────────
(async () => {
	const tbody = document.getElementById('usersTableBody');
	try {
		const res = await fetch(`${API}/admin/users?page_size=6`, { headers: authHeaders });
		if (!res.ok) throw new Error();

		const users = await res.json();
		if (!tbody) return;

		if (users.length === 0) {
			tbody.innerHTML = emptyRow(4, 'No users yet.');
			return;
		}

		const roleColor = {
			admin:    'text-tertiary bg-tertiary-fixed',
			owner:    'text-secondary bg-secondary-fixed',
			driver:   'text-safari-green bg-primary-fixed/40',
			customer: 'text-on-surface-variant bg-surface-container',
			tourist:  'text-on-surface-variant bg-surface-container',
		};

		tbody.innerHTML = users.map(u => `
			<tr class="hover:bg-surface/50 transition-colors">
				<td class="px-4 py-4 font-label-lg text-label-lg text-on-surface">${esc(u.full_name)}</td>
				<td class="px-4 py-4 text-on-surface-variant text-sm">${esc(u.email)}</td>
				<td class="px-4 py-4">
					<span class="px-2 py-1 rounded-full text-[10px] font-bold uppercase ${roleColor[u.role] || roleColor.customer}">
						${esc(u.role)}
					</span>
				</td>
				<td class="px-4 py-4">
					<span class="px-2 py-1 rounded-full text-[10px] font-bold uppercase ${u.is_active
						? 'bg-status-success/10 text-status-success'
						: 'bg-error/10 text-error'}">
						${u.is_active ? 'Active' : 'Suspended'}
					</span>
				</td>
			</tr>`).join('');
	} catch (_) {
		if (tbody) tbody.innerHTML = emptyRow(4, 'Could not load users.');
	}
})();

// ── Activity Feed ──────────────────────────────────────────────────────────────
(async () => {
	const feed = document.getElementById('activityFeed');
	if (!feed) return;

	try {
		// Build activity items from users + pending verifications in parallel
		const [usersRes, verifRes] = await Promise.all([
			fetch(`${API}/admin/users?page_size=3`, { headers: authHeaders }),
			fetch(`${API}/admin/verifications/pending?type=vehicle&page_size=2`, { headers: authHeaders }),
		]);

		const items = [];

		if (usersRes.ok) {
			const users = await usersRes.json();
			users.forEach(u => {
				items.push({
					color: 'bg-primary',
					title: `New ${capitalize(u.role)} Registered`,
					body: `${esc(u.full_name)} joined the platform.`,
					time: 'recently',
				});
			});
		}

		if (verifRes.ok) {
			const verifs = await verifRes.json();
			verifs.forEach(v => {
				items.push({
					color: 'bg-ugandan-sun',
					title: 'Vehicle Awaiting Inspection',
					body: `${esc(v.make)} ${esc(v.model)} (${esc(v.registration_plate)}) submitted for review.`,
					time: 'pending',
				});
			});
		}

		if (items.length === 0) {
			feed.innerHTML = `<p class="text-on-surface-variant text-sm text-center">No recent activity.</p>`;
			return;
		}

		feed.innerHTML = items.map(item => `
			<div class="flex gap-4">
				<div class="mt-1 w-2 h-2 rounded-full ${item.color} flex-shrink-0"></div>
				<div>
					<p class="text-on-surface font-label-lg text-label-lg">${item.title}</p>
					<p class="text-on-surface-variant text-sm">${item.body}</p>
					<p class="text-outline text-xs mt-1">${item.time}</p>
				</div>
			</div>`).join('');
	} catch (_) {
		feed.innerHTML = `<p class="text-on-surface-variant text-sm text-center">Could not load activity.</p>`;
	}
})();

// ── Helpers ────────────────────────────────────────────────────────────────────
function setText(id, value) {
	const el = document.getElementById(id);
	if (el) el.textContent = value ?? '—';
}

function esc(str) {
	if (!str) return '';
	return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function capitalize(str) {
	return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
}

function emptyRow(cols, msg) {
	return `<tr><td colspan="${cols}" class="px-4 py-8 text-center text-on-surface-variant">${msg}</td></tr>`;
}
