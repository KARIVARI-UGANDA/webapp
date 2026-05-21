document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('registerOwnerForm');
	if (!form) return;
	form.addEventListener('submit', (e) => {
		e.preventDefault();
		const firstName = (form.first_name ? form.first_name.value.trim() : '');
		const lastName  = (form.last_name  ? form.last_name.value.trim()  : '');
		const fullName  = form.full_name
			? form.full_name.value.trim()
			: (firstName + ' ' + lastName).trim();
		signup({
			full_name:    fullName,
			email:        form.email.value,
			phone_number: form.country_code.value + form.phone_local.value.trim(),
			password:     form.password.value,
			role:         'owner',
		}, 'ownerRegisterAlert');
	});
});
