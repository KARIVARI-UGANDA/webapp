/* signin.js - Vanilla JS, no external dependencies */

(function() {
  const form = document.getElementById('loginForm');
  const alertBox = document.getElementById('loginAlert');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const rememberCheckbox = document.getElementById('rememberMe');
  const togglePasswordBtn = document.getElementById('togglePassword');

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

  function saveCredentials(email, password, remember) {
    if (remember) {
      localStorage.setItem('savedEmail', email);
      localStorage.setItem('savedPassword', btoa(password));
      localStorage.setItem('rememberMe', 'true');
    } else {
      localStorage.removeItem('savedEmail');
      localStorage.removeItem('savedPassword');
      localStorage.setItem('rememberMe', 'false');
    }
  }

  function loadSavedCredentials() {
    const remember = localStorage.getItem('rememberMe') === 'true';
    if (remember && emailInput && passwordInput) {
      const savedEmail = localStorage.getItem('savedEmail');
      const savedPassword = localStorage.getItem('savedPassword');
      if (savedEmail) emailInput.value = savedEmail;
      if (savedPassword) passwordInput.value = atob(savedPassword);
      if (rememberCheckbox) rememberCheckbox.checked = true;
    }
  }

  async function handleLogin(event) {
    event.preventDefault();

    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const remember = rememberCheckbox ? rememberCheckbox.checked : false;

    if (!email) {
      showAlert('Please enter your email address.', 'error');
      emailInput.focus();
      return;
    }

    if (!validateEmail(email)) {
      showAlert('Please enter a valid email address.', 'error');
      emailInput.focus();
      return;
    }

    if (!password) {
      showAlert('Please enter your password.', 'error');
      passwordInput.focus();
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Signing In...';
    submitBtn.disabled = true;

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
          role: 'customer'
        }),
      });

      const data = await response.json();

      if (response.ok) {
        saveCredentials(email, password, remember);
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user_role', data.role);
        localStorage.setItem('user_name', data.full_name);
        showAlert('Login successful! Redirecting...', 'success');
        const roleRedirects = {
          tourist:  '/',
          customer: '/',
          owner:    '/owner/dashboard',
          driver:   '/driver/dashboard',
          admin:    '/admin/dashboard',
        };
        setTimeout(() => {
          window.location.href = roleRedirects[data.role] || '/';
        }, 1500);
      } else {
        const errorMsg = data.message || data.error || 'Invalid email or password.';
        showAlert(errorMsg, 'error');
      }
    } catch (error) {
      console.error('Login error:', error);
      showAlert('Network error. Please check your connection and try again.', 'error');
    } finally {
      submitBtn.innerHTML = originalText;
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
    form.addEventListener('submit', handleLogin);
  }

  const googleBtn = document.getElementById('googleLoginBtn');
  const facebookBtn = document.getElementById('facebookLoginBtn');

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

  loadSavedCredentials();

  console.log('Kari Vari Uganda — Customer Sign In ready');
})();