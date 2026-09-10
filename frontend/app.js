const API = window.location.origin;
let category  = 'general';
let history   = [];
let loading   = false;
let streamBot = null;

// ── Init ──────────────────────────────────────────────
window.addEventListener('load', () => {
    initEitaa();
});

function initEitaa() {
    try {
        const WA = window.Eitaa?.WebApp;
        if (!WA) return;
        WA.ready();
        WA.expand();
        WA.setHeaderColor('#FF6A3D');
        WA.setBackgroundColor('#F9F5F1');
        if (WA.disableVerticalSwipes) WA.disableVerticalSwipes();
        WA.BackButton.onClick(goHome);
    } catch (e) {}
}

// ── Welcome ───────────────────────────────────────────
const WELCOME = {
    shopping:   'سلام! 🛍️ به فروشگاه هوشمند خوش اومدی!\nچه محصولی دنبالش هستی؟',
    clinic:     'سلام! 🏥 به کلینیک هوشمند خوش اومدی!\nچطور می‌تونم کمکت کنم؟',
    realestate: 'سلام! 🏠 به مشاور هوشمند املاک خوش اومدی!\nدنبال خرید، فروش یا اجاره هستی؟',
    education:  'سلام! 📚 به دستیار آموزشی خوش اومدی!\nچه سوال درسی داری؟',
    restaurant: 'سلام! 🍕 به رستوران هوشمند خوش اومدی!\nمنو رو ببین یا سفارش بده!',
    legal:      'سلام! ⚖️ به مشاور حقوقی هوشمند خوش اومدی!\nسوالت رو بپرس!',
    finance:    'سلام! 💰 به مشاور مالی هوشمند خوش اومدی!\nچطور می‌تونم کمکت کنم؟',
    support:    'سلام! 🔧 به پشتیبانی فنی خوش اومدی!\nمشکلت رو توضیح بده!',
    general:    'سلام! 🤖 من دستیار هوشمند توام!\nهر سوالی داری بپرس!'
};

// ── Toast ─────────────────────────────────────────────
function toast(msg) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.remove('hidden');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.add('hidden'), 2400);
}

// ── Banner ────────────────────────────────────────────
function closeBanner() {
    const b = document.getElementById('banner');
    if (!b) return;
    b.style.transition = 'opacity .2s, max-height .3s, margin .3s';
    b.style.opacity    = '0';
    b.style.maxHeight  = '0';
    b.style.margin     = '0';
    b.style.overflow   = 'hidden';
    setTimeout(() => b.remove(), 320);
}

// ── Rail ──────────────────────────────────────────────
function toggleRail() {
    const collapsed = document.body.classList.toggle('rail-collapsed');
    const openBtn   = document.getElementById('rail-open-btn');
    if (openBtn) openBtn.classList.toggle('hidden', !collapsed);
}

// ── Panel ─────────────────────────────────────────────
function openPanel() {
    document.getElementById('side-panel').classList.add('open');
    document.getElementById('backdrop').classList.remove('hidden');
}

function closePanel() {
    document.getElementById('side-panel').classList.remove('open');
    document.getElementById('backdrop').classList.add('hidden');
}

// ── Models ────────────────────────────────────────────
function toggleModels() {
    document.getElementById('model-menu').classList.toggle('hidden');
}

function pickModel(name) {
    document.getElementById('model-label').textContent = name;
    document.getElementById('model-menu').classList.add('hidden');

    // آپدیت رنگ dot
    const dots = { 'Gemini 2.0 Flash': '#8B5CF6', 'دستیار عمومی': '#FF6A3D', 'پشتیبانی فنی': '#10B981' };
    const dot = document.querySelector('.model-dot');
    if (dot && dots[name]) dot.style.background = dots[name];

    // تیک فعال
    document.querySelectorAll('.mm-item').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.mm-check').forEach(el => el.remove());
    event.currentTarget.classList.add('active');
    const check = document.createElement('span');
    check.className = 'mm-check';
    check.textContent = '✓';
    event.currentTarget.appendChild(check);

    toast('مدل: ' + name);
}

// ── Navigation ────────────────────────────────────────
function focusComposer() {
    document.getElementById('user-input').focus();
}

function showChatUI() {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('messages').classList.remove('hidden');
}

function goHome() {
    history  = [];
    category = 'general';
    document.getElementById('messages').innerHTML = '';
    document.getElementById('messages').classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
    closePanel();
    setRailActive('rail-chat');
    try { window.Eitaa?.WebApp?.BackButton?.hide(); } catch (e) {}
}

function setRailActive(id) {
    document.querySelectorAll('.rail-ico').forEach(b => b.classList.remove('active'));
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
}

function selectCategory(cat, title) {
    category = cat;
    history  = [];

    const box = document.getElementById('messages');
    box.innerHTML = '';
    addBotMsg(WELCOME[cat] || WELCOME.general);
    showChatUI();

    if (title) {
        const label = document.getElementById('model-label');
        if (label) label.textContent = title;
    }

    haptic('light');
    closePanel();
    try { window.Eitaa?.WebApp?.BackButton?.show(); } catch (e) {}
    setTimeout(() => document.getElementById('user-input').focus(), 200);
}

// ── Quick send ────────────────────────────────────────
function quickSend(text) {
    const input = document.getElementById('user-input');
    input.value = text;
    autoGrow(input);
    sendMessage();
}

// ── Input ─────────────────────────────────────────────
function onEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoGrow(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

// ── Send ──────────────────────────────────────────────
async function sendMessage() {
    if (loading) return;
    const input = document.getElementById('user-input');
    const text  = input.value.trim();
    if (!text) return;

    showChatUI();
    input.value = '';
    autoGrow(input);

    addUserMsg(text);
    history.push({ role: 'user', content: text });
    setLoading(true);
    showTyping();

    const coldTimer = setTimeout(() => {
        const hint = document.getElementById('cold-hint');
        if (hint) hint.style.display = 'block';
    }, 4000);

    let fullText    = '';
    let botEl       = null;
    let firstChunk  = true;
    let historySaved = false;

    const saveHistory = () => {
        if (!historySaved && fullText) {
            history.push({ role: 'assistant', content: fullText });
            historySaved = true;
            haptic('success');
        }
    };

    try {
        const res = await fetch(`${API}/api/chat/stream`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message:  text,
                category: category,
                history:  history.slice(-10)
            })
        });

        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

        clearTimeout(coldTimer);
        removeTyping();

        const reader  = res.body.getReader();
        const decoder = new TextDecoder();
        let   buffer  = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith('data:')) continue;
                try {
                    const data = JSON.parse(line.slice(5).trim());

                    if (data.content) {
                        if (firstChunk) {
                            botEl      = addBotMsg('');
                            streamBot  = botEl;
                            firstChunk = false;
                        }
                        fullText += data.content;
                        renderBotContent(botEl, fullText);
                        scrollBottom();
                    }

                    if (data.done) saveHistory();

                } catch (_) {}
            }
        }

        // buffer باقی‌مانده
        if (buffer.startsWith('data:')) {
            try {
                const data = JSON.parse(buffer.slice(5).trim());
                if (data.content && botEl) {
                    fullText += data.content;
                    renderBotContent(botEl, fullText);
                }
            } catch (_) {}
        }

        saveHistory();
        if (!fullText) addBotMsg('پاسخی دریافت نشد. دوباره تلاش کن! 🔄');

    } catch (err) {
        clearTimeout(coldTimer);
        removeTyping();
        if (botEl && !fullText) botEl.remove();
        console.error(err);
        addBotMsg('اتصال به سرور ممکن نیست. دوباره تلاش کن! 🔌');
        haptic('error');
    }

    streamBot = null;
    setLoading(false);
    input.focus();
}

// ── Message Helpers ───────────────────────────────────
function addUserMsg(text) {
    const box = document.getElementById('messages');
    const div = document.createElement('div');
    div.className   = 'msg user';
    div.textContent = text;
    box.appendChild(div);
    scrollBottom();
    return div;
}

function addBotMsg(text) {
    const box = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'msg bot';
    if (text) renderBotContent(div, text);

    // کپی با دابل‌کلیک
    div.addEventListener('dblclick', () => {
        navigator.clipboard?.writeText(div.textContent)
            .then(() => toast('کپی شد! 📋'))
            .catch(() => {});
    });

    box.appendChild(div);
    scrollBottom();
    return div;
}

function renderBotContent(el, text) {
    // Markdown ساده
    const html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`\n]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    el.innerHTML = html;
}

function scrollBottom() {
    const box = document.getElementById('messages');
    requestAnimationFrame(() => { box.scrollTop = box.scrollHeight });
}

// ── Typing indicator ──────────────────────────────────
function showTyping() {
    const box = document.getElementById('messages');
    const div = document.createElement('div');
    div.id        = 'typing';
    div.className = 'typing-wrap';
    div.innerHTML = `
        <div class="dots"><span></span><span></span><span></span></div>
        <div id="cold-hint" class="cold-hint">در حال آماده‌سازی پاسخ...</div>
    `;
    box.appendChild(div);
    scrollBottom();
}

function removeTyping() {
    document.getElementById('typing')?.remove();
}

// ── Loading state ─────────────────────────────────────
function setLoading(state) {
    loading = state;
    const btn = document.getElementById('send-btn');
    btn.disabled = state;
    btn.style.opacity = state ? '.5' : '1';
}

// ── Haptic ────────────────────────────────────────────
function haptic(type) {
    try {
        const hf = window.Eitaa?.WebApp?.HapticFeedback;
        if (!hf) return;
        if (type === 'light')   hf.impactOccurred('light');
        if (type === 'success') hf.notificationOccurred('success');
        if (type === 'error')   hf.notificationOccurred('error');
    } catch (e) {}
}

// ── Close on outside click ────────────────────────────
document.addEventListener('click', (e) => {
    const menu = document.getElementById('model-menu');
    const chip = document.getElementById('model-chip');
    if (
        menu && !menu.classList.contains('hidden') &&
        !menu.contains(e.target) &&
        chip && !chip.contains(e.target)
    ) {
        menu.classList.add('hidden');
    }
});
