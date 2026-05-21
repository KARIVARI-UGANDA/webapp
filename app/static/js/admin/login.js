document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('adminLoginForm');
	if (!form) return;
	form.addEventListener('submit', (e) => {
		e.preventDefault();
		login(form.email.value, form.password.value, 'adminLoginAlert', 'admin');
	});
});
