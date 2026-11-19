/* FrontierLab display preferences — no server-side account required. */
(() => {
  'use strict';
  const DEFAULT = 120, MIN = 90, MAX = 150, STEP = 5;
  const KEY = 'frontierlab:font-scale:v1';
  const get = id => document.getElementById(id);
  const overlay = get('settingsBackdrop');
  const range = get('fontScale');
  const valueText = get('fontScaleValue');
  const smaller = get('fontSmaller');
  const larger = get('fontLarger');
  const presets = [...document.querySelectorAll('[data-font-size]')];
  let lastFocus = null;
  const normalize = value => {
    const n = Number(value);
    return Number.isFinite(n) ? Math.min(MAX, Math.max(MIN, Math.round(n / STEP) * STEP)) : DEFAULT;
  };
  function apply(value) {
    const size = normalize(value);
    document.documentElement.style.setProperty('--font-scale', String(size / 100));
    range.value = String(size);
    range.setAttribute('aria-valuenow', String(size));
    range.setAttribute('aria-valuetext', size + '%');
    valueText.value = size + '%';
    valueText.textContent = size + '%';
    smaller.disabled = size <= MIN;
    larger.disabled = size >= MAX;
    presets.forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.fontSize) === size)));
    try { window.localStorage.setItem(KEY, String(size)); } catch (_) { /* private browsing */ }
  }
  function open() {
    lastFocus = document.activeElement;
    const sidebar = get('sidebar');
    if (sidebar) sidebar.classList.remove('open');
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    get('closeSettings').focus();
  }
  function close() {
    if (overlay.hidden) return;
    overlay.hidden = true;
    document.body.style.overflow = get('modalBackdrop')?.hidden === false ? 'hidden' : '';
    if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
  }
  let saved = DEFAULT;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw !== null) saved = normalize(raw);
  } catch (_) { /* storage disabled */ }
  apply(saved);
  get('topbarSettings').addEventListener('click', open);
  get('sidebarSettings').addEventListener('click', open);
  get('closeSettings').addEventListener('click', close);
  get('applySettings').addEventListener('click', close);
  get('resetFont').addEventListener('click', () => apply(DEFAULT));
  smaller.addEventListener('click', () => apply(Number(range.value) - STEP));
  larger.addEventListener('click', () => apply(Number(range.value) + STEP));
  range.addEventListener('input', () => apply(range.value));
  presets.forEach(button => button.addEventListener('click', () => apply(button.dataset.fontSize)));
  overlay.addEventListener('click', event => { if (event.target === overlay) close(); });
  document.addEventListener('keydown', event => {
    if (overlay.hidden) return;
    if (event.key === 'Escape') { event.preventDefault(); close(); return; }
    if (event.key === 'Tab') {
      const nodes = [...get('settingsPanel').querySelectorAll('button:not([disabled]),input:not([disabled])')];
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  }, true);
})();
