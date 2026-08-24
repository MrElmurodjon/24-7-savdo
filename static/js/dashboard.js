// dashboard.js — Quva Nihol

document.addEventListener('DOMContentLoaded', () => {
  // Animate fade-in elements
  const fadeEls = document.querySelectorAll('.fade-in');
  fadeEls.forEach(el => {
    el.style.animationFillMode = 'forwards';
  });

  // Modal overlay click to close
  const modalOverlay = document.getElementById('deleteModal');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) closeModal();
    });
  }

  // Stat counter animation
  const statValues = document.querySelectorAll('.stat-value');
  statValues.forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (!isNaN(target) && target > 0) {
      let current = 0;
      const increment = Math.max(1, Math.floor(target / 30));
      const timer = setInterval(() => {
        current = Math.min(current + increment, target);
        el.textContent = current;
        if (current >= target) clearInterval(timer);
      }, 30);
    }
  });

  // Alert auto-hide
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s, transform 0.5s';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });
});

// Global functions
function closeModal() {
  const modal = document.getElementById('deleteModal');
  if (modal) modal.classList.remove('active');
}
