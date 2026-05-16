/* ============================================================
   ChemDesignAI — Main JavaScript
   Global utilities, AI chat, theme, loader
   ============================================================ */

'use strict';

// ── DOM Ready ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initLoader();
  initTheme();
  initChat();
  initToasts();
  initTooltips();
});

/* ─────────────────────────────────────────────────────────────
   LOADER
   ───────────────────────────────────────────────────────────── */
function initLoader() {
  const loader = document.getElementById('loader');
  if (!loader) return;
  window.addEventListener('load', () => {
    setTimeout(() => loader.classList.add('hidden'), 600);
  });
  // Failsafe: hide after 3 s even if load event doesn't fire
  setTimeout(() => loader && loader.classList.add('hidden'), 3000);
}

/* ─────────────────────────────────────────────────────────────
   DARK / LIGHT THEME TOGGLE
   ───────────────────────────────────────────────────────────── */
function initTheme() {
  const btn  = document.getElementById('themeToggle');
  const icon = document.getElementById('themeIcon');
  const html = document.documentElement;

  // Restore saved preference
  const saved = localStorage.getItem('cdai-theme') || 'dark';
  applyTheme(saved);

  if (btn) {
    btn.addEventListener('click', () => {
      const next = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('cdai-theme', next);
      // Sync with server preference (non-blocking)
      fetch('/api/v1/theme', { method: 'POST',
        headers: { 'Content-Type': 'application/json',
                   'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ theme: next }) }).catch(() => {});
    });
  }

  function applyTheme(theme) {
    html.setAttribute('data-bs-theme', theme);
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    }
  }
}

/* ─────────────────────────────────────────────────────────────
   AI CHAT SIDEBAR
   ───────────────────────────────────────────────────────────── */
function initChat() {
  const sidebar  = document.getElementById('chatSidebar');
  const overlay  = document.getElementById('chatOverlay');
  const toggle   = document.getElementById('chatToggle');
  const closeBtn = document.getElementById('chatClose');
  const sendBtn  = document.getElementById('chatSend');
  const input    = document.getElementById('chatInput');
  const messages = document.getElementById('chatMessages');

  if (!sidebar) return;

  function openChat() {
    sidebar.classList.add('open');
    overlay.classList.add('show');
    input && input.focus();
  }
  function closeChat() {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  }

  toggle  && toggle.addEventListener('click', e => { e.preventDefault(); openChat(); });
  closeBtn && closeBtn.addEventListener('click', closeChat);
  overlay  && overlay.addEventListener('click', closeChat);

  // ── Send Message ───────────────────────────────────────────
  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    // Append user bubble
    appendMessage('user', text);
    input.value = '';
    sendBtn.disabled = true;

    // Typing indicator
    const typingId = appendTyping();

    try {
      const resp = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ message: text, context: '' }),
      });
      const data = await resp.json();
      removeTyping(typingId);
      appendMessage('ai', data.response || 'Sorry, I could not process that.');
    } catch (err) {
      removeTyping(typingId);
      appendMessage('ai', '⚠ Connection error. Please check your API key and try again.');
    }

    sendBtn.disabled = false;
    input.focus();
  }

  sendBtn && sendBtn.addEventListener('click', sendMessage);
  input   && input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // ── Helpers ────────────────────────────────────────────────
  function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.innerHTML = `
      <div class="message-bubble">${escapeHtml(text).replace(/\n/g,'<br>')}</div>
      <small class="text-muted">${role === 'ai' ? 'ChemDesignAI' : 'You'}</small>
    `;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function appendTyping() {
    const id  = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'chat-message ai'; div.id = id;
    div.innerHTML = '<div class="message-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return id;
  }

  function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }
}

/* ─────────────────────────────────────────────────────────────
   TOAST AUTO-DISMISS
   ───────────────────────────────────────────────────────────── */
function initToasts() {
  document.querySelectorAll('.toast').forEach(el => {
    const toast = new bootstrap.Toast(el, { delay: 5000 });
    toast.show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
  });
}

/* ─────────────────────────────────────────────────────────────
   BOOTSTRAP TOOLTIPS
   ───────────────────────────────────────────────────────────── */
function initTooltips() {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });
}

/* ─────────────────────────────────────────────────────────────
   UTILITIES
   ───────────────────────────────────────────────────────────── */

/** Get CSRF token from any visible hidden input. */
function getCsrfToken() {
  return (
    document.querySelector('input[name="csrf_token"]')?.value ||
    document.querySelector('meta[name="csrf-token"]')?.content ||
    ''
  );
}

/** Escape HTML special characters. */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
    .replace(/'/g,'&#039;');
}

/** Format number with commas. */
function formatNumber(n, decimals = 2) {
  return Number(n).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** POST JSON helper. */
async function postJson(url, data) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(data),
  });
  return resp.json();
}

/** Show a temporary toast notification. */
function showToast(message, type = 'info') {
  const container = document.querySelector('.flash-container') ||
    (() => {
      const c = document.createElement('div');
      c.className = 'flash-container position-fixed top-0 end-0 p-3';
      c.style.cssText = 'z-index:9999;margin-top:70px';
      document.body.appendChild(c);
      return c;
    })();

  const toast = document.createElement('div');
  toast.className = `toast show align-items-center text-bg-${type} border-0 mb-2`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${escapeHtml(message)}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(toast);
  const t = new bootstrap.Toast(toast, { delay: 4000 });
  t.show();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// Export globals for template scripts
window.getCsrfToken = getCsrfToken;
window.postJson     = postJson;
window.showToast    = showToast;
window.formatNumber = formatNumber;
