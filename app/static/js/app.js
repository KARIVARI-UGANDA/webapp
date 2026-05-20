const API = '/api';

document.addEventListener('DOMContentLoaded', () => {

	async function signup(data) {
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
				// Redirect based on role — dashboard pages built in Phase 15-18
				const redirects = {
					tourist: '/',
					owner:   '/owner/dashboard',
					driver:  '/driver/dashboard',
					admin:   '/admin/dashboard',
				};
				window.location.href = redirects[json.role] || '/';
			} else {
				const msg = json.detail
					? (Array.isArray(json.detail) ? json.detail.map(e => e.msg).join(', ') : json.detail)
					: JSON.stringify(json);
				alert('Registration failed: ' + msg);
			}
		} catch (err) {
			alert('Network error: ' + err.message);
		}
	}

	const travelerForm = document.getElementById('registerTravelerForm');
	if (travelerForm) {
		travelerForm.addEventListener('submit', (e) => {
			e.preventDefault();
			const roleSelect = travelerForm.querySelector('[name="role"]') || travelerForm.querySelector('#roleSelect');
			signup({
				full_name: travelerForm.full_name.value,
				email: travelerForm.email.value,
				phone_number: travelerForm.phone_number.value,
				password: travelerForm.password.value,
				role: roleSelect ? roleSelect.value : 'tourist'
			});
		});
	}

	const driverForm = document.getElementById('registerDriverForm');
	if (driverForm) {
		driverForm.addEventListener('submit', (e) => {
			e.preventDefault();
			signup({
				full_name: driverForm.full_name.value,
				email: driverForm.email.value,
				phone_number: driverForm.phone_number.value,
				password: driverForm.password.value,
				role: 'driver'
			});
		});
	}

	const ownerForm = document.getElementById('registerOwnerForm');
	if (ownerForm) {
		ownerForm.addEventListener('submit', (e) => {
			e.preventDefault();
			signup({
				full_name: ownerForm.full_name.value,
				email: ownerForm.email.value,
				phone_number: ownerForm.phone_number.value,
				password: ownerForm.password.value,
				role: 'owner'
			});
		});
	}

	const loginForm = document.getElementById('loginForm');
	if (loginForm) {
		loginForm.addEventListener('submit', async (e) => {
			e.preventDefault();
			try {
				const res = await fetch(`${API}/auth/login`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						email: loginForm.email.value,
						password: loginForm.password.value
					})
				});
				const json = await res.json();
				if (res.ok) {
					localStorage.setItem('access_token', json.access_token);
					localStorage.setItem('refresh_token', json.refresh_token);
					localStorage.setItem('role', json.role);
					localStorage.setItem('full_name', json.full_name);
					const ROLE_HOME = {
						tourist: '/',
						owner:   '/owner/dashboard',
						admin:   '/admin/dashboard',
						driver:  '/driver/dashboard',
					};
					window.location.href = ROLE_HOME[json.role] || '/';
				} else {
					alert('Login failed: ' + (json.detail || 'Unknown error'));
				}
			} catch (err) {
				alert('Network error: ' + err.message);
			}
		});
	}

	// Index page initialization
	async function initIndexPage() {
		const vehicleContainer = document.getElementById('vehicleCardsContainer');
		const authButtons = document.getElementById('authButtons');
		const userButtons = document.getElementById('userButtons');
		const logoutBtn = document.getElementById('logoutBtn');
		const userName = document.getElementById('userName');

		if (!vehicleContainer) return; // Not on index page

		// Check authentication status
		const token = localStorage.getItem('access_token');

		if (token) {
			try {
				// Fetch current user from database
				const userRes = await fetch(`${API}/auth/me`, {
					headers: { 'Authorization': `Bearer ${token}` }
				});

				if (userRes.ok) {
					const user = await userRes.json();
					authButtons.style.display = 'none';
					userButtons.style.display = 'flex';
					userName.textContent = user.full_name;
				} else {
					// Token invalid, clear storage
					localStorage.removeItem('access_token');
					localStorage.removeItem('refresh_token');
					localStorage.removeItem('role');
					localStorage.removeItem('full_name');
				}
			} catch (err) {
				console.error('Failed to fetch user:', err);
			}
		}

		// Logout handler
		if (logoutBtn) {
			logoutBtn.addEventListener('click', () => {
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
				localStorage.removeItem('role');
				localStorage.removeItem('full_name');
				window.location.href = '/';
			});
		}

		// Fetch vehicles from API
		try {
			const res = await fetch(`${API}/vehicles/?page=1&page_size=6`);
			if (res.ok) {
				const vehicles = await res.json();
				vehicleContainer.innerHTML = vehicles.map(vehicle => `
					<div class="col-md-6 col-lg-4">
						<div class="vehicle-card h-100">
							<div class="vehicle-img-wrapper position-relative">
								<img src="${vehicle.photos && vehicle.photos.length > 0 ? vehicle.photos[0].photo_url : 'https://via.placeholder.com/400x300?text=' + vehicle.make + '+' + vehicle.model}" alt="${vehicle.make} ${vehicle.model}" class="card-img-top">
								<span class="vehicle-badge">Available</span>
							</div>
							<div class="card-body p-4">
								<div class="d-flex justify-content-between align-items-start mb-3">
									<div>
										<h5 class="fw-bold mb-0">${vehicle.make} ${vehicle.model}</h5>
										<p class="text-secondary small">${vehicle.vehicle_type}</p>
									</div>
									<div class="text-end">
										<span class="price fw-bold">UGX ${(vehicle.base_daily_rate_ugx / 1000).toFixed(0)}k</span>
										<span class="text-secondary small">/ day</span>
									</div>
								</div>
								<div class="d-flex justify-content-between mb-4 text-secondary">
									<span><i class="bi bi-people-fill me-1"></i> ${vehicle.passenger_capacity} Seats</span>
									<span><i class="bi bi-gear-fill me-1"></i> ${vehicle.transmission}</span>
									<span><i class="bi bi-fuel-pump-fill me-1"></i> ${vehicle.fuel_type}</span>
								</div>
								<button class="btn btn-primary w-100 py-2 fw-bold">Book Now</button>
							</div>
						</div>
					</div>
				`).join('');
			}
		} catch (err) {
			console.error('Failed to fetch vehicles:', err);
			vehicleContainer.innerHTML = '<p class="text-center text-danger">Failed to load vehicles</p>';
		}
	}

	// Initialize index page if present
	initIndexPage();

});

