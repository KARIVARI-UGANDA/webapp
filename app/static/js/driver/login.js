document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('driverLoginForm');
	if (!form) return;
	form.addEventListener('submit', (e) => {
		e.preventDefault();
		login(form.email.value, form.password.value, 'driverLoginAlert', 'driver');
	});
});
