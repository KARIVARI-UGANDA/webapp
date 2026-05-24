document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('adminLoginForm');
	if (form) {
		form.addEventListener('submit', (e) => {
			e.preventDefault();
			login(form.email.value, form.password.value, 'adminLoginAlert', 'admin');
		});
	}

	const devBtn = document.getElementById('devSignInBtn');
	if (devBtn) {
		devBtn.addEventListener('click', async () => {
			devBtn.disabled = true;
			devBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Signing in…';
			try {
				const res  = await fetch('/api/admin/dev-signin', { method: 'POST' });
				const json = await res.json();
				if (res.ok) {
					localStorage.setItem('access_token',  json.access_token);
					localStorage.setItem('refresh_token', json.refresh_token);
					localStorage.setItem('role',          json.role);
					localStorage.setItem('full_name',     json.full_name);
					window.location.href = '/admin/dashboard';
				} else {
					showAlert('adminLoginAlert', json.detail || 'Dev sign-in failed');
					devBtn.disabled = false;
					devBtn.innerHTML = '<i class="bi bi-lightning-fill me-1 text-warning"></i> Dev Quick Access';
				}
			} catch (err) {
				showAlert('adminLoginAlert', 'Network error: ' + err.message);
				devBtn.disabled = false;
				devBtn.innerHTML = '<i class="bi bi-lightning-fill me-1 text-warning"></i> Dev Quick Access';
			}
		});
	}
});
