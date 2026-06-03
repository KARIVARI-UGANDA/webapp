const API = '/api';

function showAlert(id, message, type = 'danger') {
	const el = document.getElementById(id);
	if (!el) return;
	el.className = `alert alert-${type}`;
	el.innerHTML = message;
	el.classList.remove('d-none');
}

async function signup(data, alertId) {
	try {
		const res = await fetch(`${API}/auth/signup`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(data)
		});
		const json = await res.json();
		if (res.ok) {
			localStorage.setItem('access_token', json.access_token);
			localStorage.setItem('refresh_token', json.refresh_token);
			localStorage.setItem('role', json.role);
			localStorage.setItem('full_name', json.full_name);
			const redirects = {
				customer: '/',
				owner:    '/owner/dashboard',
				admin:    '/admin/dashboard',
			};
			window.location.href = redirects[json.role] || '/';
		} else {
			const msg = json.detail
				? (Array.isArray(json.detail) ? json.detail.map(e => e.msg).join(', ') : json.detail)
				: JSON.stringify(json);
			showAlert(alertId, 'Registration failed: ' + msg);
		}
	} catch (err) {
		showAlert(alertId, 'Network error: ' + err.message);
	}
}

async function login(email, password, alertId, expectedRole) {
	try {
		const res = await fetch(`${API}/auth/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		});
		const json = await res.json();
		if (res.ok) {
			if (expectedRole && json.role !== expectedRole) {
				const portalLinks = {
					customer: '<a href="/login">Customer Login</a>',
					owner:    '<a href="/owner/login">Owner Login</a>',
					admin:    '<a href="/admin/login">Admin Login</a>',
				};
				const link = portalLinks[json.role] || '<a href="/">Home</a>';
				showAlert(alertId, `Wrong portal — your account is a <strong>${json.role}</strong>. Please use the ${link} page.`);
				return;
			}
			localStorage.setItem('access_token', json.access_token);
			localStorage.setItem('refresh_token', json.refresh_token);
			localStorage.setItem('role', json.role);
			localStorage.setItem('full_name', json.full_name);
			const ROLE_HOME = {
				customer: '/',
				owner:    '/owner/dashboard',
				admin:    '/admin/dashboard',
			};
			window.location.href = ROLE_HOME[json.role] || '/';
		} else {
			showAlert(alertId, 'Login failed: ' + (json.detail || 'Unknown error'));
		}
	} catch (err) {
		showAlert(alertId, 'Network error: ' + err.message);
	}
}

async function apiLogout() {
	const refresh = localStorage.getItem('refresh_token');
	try {
		await fetch(`${API}/auth/logout`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ refresh_token: refresh })
		});
	} catch (_) {}
	localStorage.clear();
}
