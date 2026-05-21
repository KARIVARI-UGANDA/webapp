document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('registerDriverForm');
	if (!form) return;
	form.addEventListener('submit', (e) => {
		e.preventDefault();
		signup({
			full_name:    form.full_name.value,
			email:        form.email.value,
			phone_number: form.country_code.value + form.phone_local.value.trim(),
			password:     form.password.value,
			role:         'driver',
		}, 'driverRegisterAlert');
	});
});
