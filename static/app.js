document.querySelectorAll('[data-toggle-password]').forEach(button => {
  button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.togglePassword);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Hide' : 'Show';
    button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
  });
});
document.querySelectorAll('[data-dismiss]').forEach(button => button.addEventListener('click', () => button.closest('.toast').remove()));
const confirmation = document.getElementById('confirm_password');
const password = document.getElementById('password');
if (confirmation && password) {
  function checkMatch() { confirmation.setCustomValidity(confirmation.value && confirmation.value !== password.value ? 'Your passwords do not match.' : ''); }
  confirmation.addEventListener('input', checkMatch);
  password.addEventListener('input', checkMatch);
}
document.querySelectorAll('form[method="post"]').forEach(form => {
  form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.textContent = 'Please wait…'; }
  });
});
window.addEventListener('pageshow', event => { if (event.persisted) window.location.reload(); });

const catalogSearch = document.querySelector('[data-catalog-search]');
if (catalogSearch) {
  const catalog = catalogSearch.closest('[data-catalog]');
  const cards = [...catalog.querySelectorAll('[data-movie-card]')];
  const resultCount = catalog.querySelector('[data-catalog-count]');
  const emptyState = catalog.querySelector('[data-search-empty]');

  function filterCatalog() {
    const query = catalogSearch.value.trim().toLocaleLowerCase();
    let visibleCount = 0;

    cards.forEach(card => {
      const matches = card.dataset.searchText.includes(query);
      card.hidden = !matches;
      if (matches) visibleCount += 1;
    });

    if (resultCount) {
      resultCount.textContent = `${visibleCount} ${visibleCount === 1 ? 'title' : 'titles'}`;
    }
    if (emptyState) emptyState.hidden = visibleCount !== 0;
  }

  catalogSearch.addEventListener('input', filterCatalog);
}

const tiltEnabled = window.matchMedia('(hover: hover) and (pointer: fine)');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
if (tiltEnabled.matches && !reducedMotion.matches) {
  document.querySelectorAll('[data-tilt]').forEach(card => {
    card.addEventListener('pointermove', event => {
      const bounds = card.getBoundingClientRect();
      const horizontal = (event.clientX - bounds.left) / bounds.width;
      const vertical = (event.clientY - bounds.top) / bounds.height;

      card.classList.toggle('tilt-left', horizontal < 0.35);
      card.classList.toggle('tilt-right', horizontal > 0.65);
      card.classList.toggle('tilt-up', vertical < 0.35);
      card.classList.toggle('tilt-down', vertical > 0.65);
    });

    card.addEventListener('pointerleave', () => {
      card.classList.remove('tilt-left', 'tilt-right', 'tilt-up', 'tilt-down');
    });
  });
}
