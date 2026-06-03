// register.js - Vanilla JS, no external dependencies

(function() {
  const form = document.getElementById('registerTravelerForm');
  const alertBox = document.getElementById('registerAlert');
  const togglePasswordBtn = document.getElementById('togglePassword');
  const passwordInput = document.getElementById('password');
  const fullNameInput = document.getElementById('full_name');
  const emailInput = document.getElementById('email');
  const phoneInput = document.getElementById('phone_number');
  const countryCodeSelect = document.getElementById('country_code');
  const termsCheckbox = document.getElementById('terms');

  function showAlert(message, type) {
    alertBox.textContent = message;
    alertBox.className = 'alert-message ' + type;
    alertBox.style.display = 'block';
    setTimeout(() => {
      alertBox.style.display = 'none';
    }, 5000);
  }

  function validateEmail(email) {
    const re = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
    return re.test(email);
  }

  function validatePhone(phone) {
    const digits = phone.replace(/\D/g, '');
    return digits.length >= 7 && digits.length <= 15;
  }

  async function handleRegister(event) {
    event.preventDefault();

    const fullName = fullNameInput.value.trim();
    const email = emailInput.value.trim();
    const countryCode = countryCodeSelect ? countryCodeSelect.value : '+256';
    let phone = countryCode + phoneInput.value.trim();
    const password = passwordInput.value;
    const termsAccepted = termsCheckbox.checked;

    if (!fullName) {
      showAlert('Please enter your full name.', 'error');
      fullNameInput.focus();
      return;
    }

    if (!email) {
      showAlert('Please enter your email address.', 'error');
      emailInput.focus();
      return;
    }

    if (!validateEmail(email)) {
      showAlert('Please enter a valid email address (e.g., name@example.com).', 'error');
      emailInput.focus();
      return;
    }

    if (!phone) {
      showAlert('Please enter your phone number.', 'error');
      phoneInput.focus();
      return;
    }

    if (!validatePhone(phone)) {
      showAlert('Please enter a valid phone number (at least 7 digits).', 'error');
      phoneInput.focus();
      return;
    }

    if (!password) {
      showAlert('Please create a password.', 'error');
      passwordInput.focus();
      return;
    }

    if (password.length < 8) {
      showAlert('Password must be at least 8 characters long.', 'error');
      passwordInput.focus();
      return;
    }

    if (!termsAccepted) {
      showAlert('You must agree to the Terms of Service and Privacy Policy.', 'error');
      termsCheckbox.focus();
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Creating account...';
    submitBtn.disabled = true;

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: fullName,
          email: email,
          phone_number: phone,
          password: password,
          role: 'customer'
        }),
      });

      const data = await response.json();

      if (response.ok) {
        showAlert('Account created successfully! Redirecting to login...', 'success');
        form.reset();
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      } else {
        const errorMsg = data.message || data.error || 'Registration failed. Please try again.';
        showAlert(errorMsg, 'error');
      }
    } catch (error) {
      console.error('Registration error:', error);
      showAlert('Network error. Please check your connection and try again.', 'error');
    } finally {
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    }
  }

  if (togglePasswordBtn && passwordInput) {
    const toggleIcon = togglePasswordBtn.querySelector('.material-symbols-outlined');
    togglePasswordBtn.addEventListener('click', function() {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      if (toggleIcon) {
        toggleIcon.textContent = type === 'password' ? 'visibility' : 'visibility_off';
      }
    });
  }

  if (form) {
    form.addEventListener('submit', handleRegister);
  }

  const googleBtn = document.getElementById('googleSignupBtn');
  const facebookBtn = document.getElementById('facebookSignupBtn');

  if (googleBtn) {
    googleBtn.addEventListener('click', function() {
      window.location.href = '/api/auth/google';
    });
  }

  if (facebookBtn) {
    facebookBtn.addEventListener('click', function() {
      window.location.href = '/api/auth/facebook';
    });
  }

  if (phoneInput) {
    phoneInput.addEventListener('input', function(e) {
      let value = e.target.value.replace(/\D/g, '');
      if (value.length > 12) value = value.slice(0, 12);
      e.target.value = value;
    });
  }

  console.log('Customer registration page ready — Kari Vari Uganda');
})();