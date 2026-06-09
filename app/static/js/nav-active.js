// Highlights the active nav link based on the current page path.
// Works for: public top navbars, customer sidebar, owner sidebar.
(function () {
  const path = window.location.pathname.replace(/\/$/, '') || '/';

  // ── Public top-navbar links ──────────────────────────────────────────────
  document.querySelectorAll('nav a.nav-link[href], header a.nav-link[href]').forEach(function (a) {
    const href = (a.getAttribute('href') || '').replace(/\/$/, '');
    if (!href || href === '#') return;
    const isActive = href === path || (href !== '/' && path.startsWith(href));
    if (!isActive) return;

    a.style.color         = '#154212';
    a.style.borderBottom  = '2px solid #154212';
    a.style.paddingBottom = '2px';
  });

  // ── Customer sidebar (href-based links) ─────────────────────────────────
  document.querySelectorAll('.sidebar-nav a.sidebar-link[href]').forEach(function (a) {
    const href = (a.getAttribute('href') || '').replace(/\/$/, '');
    if (!href || href === '#') return;
    const isActive = href === path || (href !== '/' && path.startsWith(href));

    a.classList.toggle('bg-secondary-container',      isActive);
    a.classList.toggle('text-on-secondary-container', isActive);
    a.classList.toggle('text-on-surface-variant',     !isActive);
    if (isActive) {
      a.classList.remove('hover:bg-surface-container-high', 'hover:translate-x-1');
    }
  });

  // ── Owner sidebar (section-based, active state managed by showSection()) ─
  // Already handled in dashboard JS via showSection(). Nothing extra needed.
})();
