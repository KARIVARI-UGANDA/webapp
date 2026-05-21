document.addEventListener('DOMContentLoaded', async () => {
	const vehicleContainer = document.getElementById('vehicleCardsContainer');
	const authButtons      = document.getElementById('authButtons');
	const userButtons      = document.getElementById('userButtons');
	const logoutBtn        = document.getElementById('logoutBtn');
	const userNameEl       = document.getElementById('userName');

	const token = localStorage.getItem('access_token');

	if (token) {
		try {
			const res = await fetch(`${API}/auth/me`, {
				headers: { 'Authorization': `Bearer ${token}` }
			});
			if (res.ok) {
				const user = await res.json();
				// Non-customers go straight to their dashboard
				const dashboards = { owner: '/owner/dashboard', driver: '/driver/dashboard', admin: '/admin/dashboard' };
				if (dashboards[user.role]) {
					window.location.href = dashboards[user.role];
					return;
				}
				// Show user name + logout, hide sign-in/register
				authButtons.classList.add('d-none');
				userButtons.classList.remove('d-none');
				userButtons.classList.add('d-flex');
				userNameEl.textContent = user.full_name;
			} else {
				localStorage.clear();
			}
		} catch (err) {
			console.error('Auth check failed:', err);
		}
	}

	if (logoutBtn) {
		logoutBtn.addEventListener('click', async () => {
			await apiLogout();
			window.location.href = '/';
		});
	}

	// Load featured vehicles from DB
	try {
		const res = await fetch(`${API}/vehicles/?page=1&page_size=6`);
		if (res.ok) {
			const vehicles = await res.json();
			if (vehicleContainer) {
				vehicleContainer.innerHTML = vehicles.length === 0
					? '<p class="text-center text-secondary col-12">No vehicles available yet.</p>'
					: vehicles.map(v => `
						<div class="col-md-6 col-lg-4">
							<div class="vehicle-card h-100">
								<div class="vehicle-img-wrapper position-relative">
									<img src="${v.photos && v.photos.length > 0 ? v.photos[0].photo_url : 'https://via.placeholder.com/400x300?text=' + encodeURIComponent(v.make + ' ' + v.model)}" alt="${v.make} ${v.model}" class="card-img-top">
									<span class="vehicle-badge">Available</span>
								</div>
								<div class="card-body p-4">
									<div class="d-flex justify-content-between align-items-start mb-3">
										<div>
											<h5 class="fw-bold mb-0">${v.make} ${v.model}</h5>
											<p class="text-secondary small">${v.vehicle_type}</p>
										</div>
										<div class="text-end">
											<span class="price fw-bold">UGX ${(v.base_daily_rate_ugx / 1000).toFixed(0)}k</span>
											<span class="text-secondary small">/ day</span>
										</div>
									</div>
									<div class="d-flex justify-content-between mb-4 text-secondary">
										<span><i class="bi bi-people-fill me-1"></i> ${v.passenger_capacity} Seats</span>
										<span><i class="bi bi-gear-fill me-1"></i> ${v.transmission}</span>
										<span><i class="bi bi-fuel-pump-fill me-1"></i> ${v.fuel_type}</span>
									</div>
									<button class="btn btn-primary w-100 py-2 fw-bold">Book Now</button>
								</div>
							</div>
						</div>`).join('');
			}
		}
	} catch (err) {
		console.error('Failed to load vehicles:', err);
		if (vehicleContainer) {
			vehicleContainer.innerHTML = '<p class="text-center text-danger col-12">Failed to load vehicles.</p>';
		}
	}
});
