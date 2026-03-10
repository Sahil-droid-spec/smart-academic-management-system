// MODAL
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape')
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
});

// SIMPLE MARKDOWN
function renderMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
    .replace(/(<li>[\s\S]*?<\/li>\n?)+/g, s => `<ul>${s}</ul>`)
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
}

// CHAT
let chatLoaded = false;

async function loadHistory() {
  if (chatLoaded) return;
  chatLoaded = true;
  try {
    const res = await fetch('/ai/history');
    const msgs = await res.json();
    msgs.forEach(m => appendMessage(m.role, m.content, false));
    scrollChat();
  } catch(e) {}
}

function appendMessage(role, content, scroll = true) {
  const c = document.getElementById('chatMessages');
  if (!c) return;
  const d = document.createElement('div');
  d.className = 'msg ' + role;
  d.innerHTML = `
    <div class="msg-avatar">${role === 'user' ? 'U' : 'A'}</div>
    <div class="msg-bubble">${renderMarkdown(content)}</div>`;
  c.appendChild(d);
  if (scroll) scrollChat();
}

function scrollChat() {
  const c = document.getElementById('chatMessages');
  if (c) c.scrollTop = c.scrollHeight;
}

function showTyping() {
  const c = document.getElementById('chatMessages');
  if (!c) return null;
  const d = document.createElement('div');
  d.className = 'msg assistant';
  d.id = 'typingIndicator';
  d.innerHTML = `<div class="msg-avatar">A</div>
    <div class="chat-typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
  c.appendChild(d);
  scrollChat();
  return d;
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const btn   = document.getElementById('chatSend');
  if (!input) return;
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  btn.disabled = true;
  appendMessage('user', message);
  const typing = showTyping();
  try {
    const res = await fetch('/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    if (typing) typing.remove();
    appendMessage('assistant', data.reply || 'Could not get a response. Please try again.');
  } catch(err) {
    if (typing) typing.remove();
    appendMessage('assistant', 'Network error. Please check your connection.');
  } finally {
    btn.disabled = false;
    input.focus();
  }
}

function quickAsk(msg) {
  const input = document.getElementById('chatInput');
  if (input) { input.value = msg; sendMessage(); }
}

async function clearChat() {
  if (!confirm('Clear chat history?')) return;
  await fetch('/ai/clear', { method: 'POST' });
  const c = document.getElementById('chatMessages');
  if (c) {
    c.innerHTML = `<div class="msg assistant">
      <div class="msg-avatar">A</div>
      <div class="msg-bubble"><strong>Chat cleared.</strong><br/>How can I help you?</div></div>`;
  }
  chatLoaded = false;
}

// SHOW TAB
function showTab(name, el) {
  document.querySelectorAll('.tab-pane').forEach(t => t.style.display = 'none');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('tab-' + name).style.display = 'block';
  el.classList.add('active');
}

// TABLE FILTER
function filterTable(query, tableId) {
  document.querySelectorAll('#' + tableId + ' tbody tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(query.toLowerCase()) ? '' : 'none';
  });
}

// ENTER KEY IN CHAT
document.addEventListener('DOMContentLoaded', function() {
  const ci = document.getElementById('chatInput');
  if (ci) ci.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); sendMessage(); } });
});
