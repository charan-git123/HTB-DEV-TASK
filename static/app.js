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
