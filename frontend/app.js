const API = window.location.origin;
let category = 'general';
let history = [];
let loading = false;
let streamBot = null;

window.addEventListener('load', () => {
    try {
        const WA = window.Eitaa?.WebApp;
        if (!WA) return;
        WA.ready();
        WA.expand();
        WA.setHeaderColor('#FF6A3D');
        WA.setBackgroundColor('#FBF6F1');
        if (WA.disableVerticalSwipes) WA.disableVerticalSwipes();
        WA.BackButton.onClick(goHome);
        console.log('✅ ایتا SDK متصل شد');
    } catch (e) {
        console.warn('خارج از محیط ایتا:', e.message);
    }
});

const WELCOME = {
    shopping: 'سلام! 🛍️ به فروشگاه هوشمند خوش اومدی!\nچه محصولی دنبالش هستی؟',
    clinic: 'سلام! 🏥 به کلینیک هوشمند خوش اومدی!\nچطور می‌تونم کمکت کنم؟',
    realestate: 'سلام! 🏠 به مشاور هوشمند املاک خوش اومدی!\nدنبال خرید، فروش یا اجاره هستی؟',
    education: 'سلام! 📚 به دستیار آموزشی خوش اومدی!\nچه سوال درسی داری؟',
    restaurant: 'سلام! 🍕 به رستوران هوشمند خوش اومدی!\nمنو رو ببین یا سفارش بده!',
    legal: 'سلام! ⚖️ به مشاور حقوقی هوشمند خوش اومدی!\nسوالت رو بپرس!',
    finance: 'سلام! 💰 به مشاور مالی هوشمند خوش اومدی!\nچطور می‌تونم کمکت کنم؟',
    support: 'سلام! 🔧 به پشتیبانی فنی خوش اومدی!\nمشکلت رو توضیح بده!',
    general: 'سلام! 🤖 من دستیار هوشمند توام!\nهر سوالی داری بپرس!'
};

function toast(msg) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.remove('hidden');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.add('hidden'), 2200);
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

function setPanel(name) {
    document.querySelectorAll('.side-item').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.side-item[data-panel="${name}"]`);
    if (btn) btn.classList.add('active');
    if (name === 'chat') goHome();
    if (window.innerWidth < 900) document.getElementById('sidebar').classList.remove('open');
}

function toggleModels() {
    document.getElementById('model-menu').classList.toggle('hidden');
}

function pickModel(name) {
    document.getElementById('model-label').textContent = name;
    document.getElementById('model-menu').classList.add('hidden');
    toast('مدل: ' + name);
}

function showChatUI() {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('messages').classList.remove('hidden');
}

function goHome() {
    history = [];
    category = 'general';
    document.getElementById('messages').innerHTML = '';
    document.getElementById('messages').classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
    document.getElementById('chat-title') && (document.getElementById('chat-title').textContent = 'چت');
    try { window.Eitaa?.WebApp?.BackButton?.hide(); } catch (e) {}
}

function selectCategory(cat, title) {
    category = cat;
    history = [];
    const box = document.getElementById('messages');
    box.innerHTML = `<div class="msg bot">${WELCOME[cat] || WELCOME.general}</div>`;
    showChatUI();
    if (title) {
        const label = document.getElementById('model-label');
        if (label) label.textContent = title.replace(/^[^\s]+\s/, '') || title;
    }
    haptic('light');
    try { window.Eitaa?.WebApp?.BackButton?.show(); } catch (e) {}
    setTimeout(() => document.getElementById('user-input').focus(), 200);
    if (window.innerWidth < 900) document.getElementById('sidebar').classList.remove('open');
}

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

async function sendMessage() {
    if (loading) return;
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text) return;

    showChatUI();
    input.value = '';
    autoGrow(input);
    addMsg(text, 'user');
    history.push({ role: 'user', content: text });
    setLoading(true);
    showTyping();

    const coldStartTimer = setTimeout(() => {
        const hint = document.getElementById('cold-hint');
        if (hint) hint.style.display = 'block';
    }, 4000);

    let fullText = '';
    let historySaved = false;

    const saveHistory = () => {
        if (!historySaved && fullText) {
            history.push({ role: 'assistant', content: fullText });
            historySaved = true;
            haptic('success');
        }
    };

    const handleData = (data) => {
        if (data.content) {
            fullText += data.content;
            if (streamBot) {
                streamBot.textContent = fullText;
                scrollBottom();
            }
        }
        if (data.done) saveHistory();
    };

    try {
        const res = await fetch(`${API}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                category: category,
                history: history.slice(-10)
            })
        });

        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

        clearTimeout(coldStartTimer);
        removeTyping();
        streamBot = addMsg('', 'bot');

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (!line.startsWith('data:')) continue;
                try {
                    handleData(JSON.parse(line.slice(5).trim()));
                } catch (_) {}
            }
        }

        buffer += decoder.decode();
        if (buffer.startsWith('data:')) {
            try {
                handleData(JSON.parse(buffer.slice(5).trim()));
            } catch (_) {}
        }

        saveHistory();
        if (!fullText && streamBot) streamBot.textContent = 'پاسخی دریافت نشد. دوباره تلاش کن!';
    } catch (err) {
        clearTimeout(coldStartTimer);
        removeTyping();
        console.error('Stream error:', err);
        if (streamBot && !fullText) streamBot.remove();
        addMsg('اتصال به سرور ممکن نیست. دوباره تلاش کن!', 'bot');
        haptic('error');
    }

    streamBot = null;
    setLoading(false);
    input.focus();
}

function addMsg(text, type) {
    const box = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `msg ${type}`;
    div.textContent = text;
    box.appendChild(div);
    scrollBottom();
    return div;
}

function scrollBottom() {
    const box = document.getElementById('messages');
    box.scrollTop = box.scrollHeight;
}

function showTyping() {
    const box = document.getElementById('messages');
    const div = document.createElement('div');
    div.id = 'typing';
    div.className = 'typing-wrap';
    div.innerHTML = `<div class="dots"><span></span><span></span><span></span></div><div id="cold-hint" class="cold-hint">در حال آماده‌سازی پاسخ...</div>`;
    box.appendChild(div);
    scrollBottom();
}

function removeTyping() {
    document.getElementById('typing')?.remove();
}

function setLoading(state) {
    loading = state;
    document.getElementById('send-btn').disabled = state;
}

function clearChat() {
    history = [];
    document.getElementById('messages').innerHTML = '';
    document.getElementById('empty-state').classList.remove('hidden');
    document.getElementById('messages').classList.add('hidden');
    haptic('light');
}

function haptic(type) {
    try {
        const hf = window.Eitaa?.WebApp?.HapticFeedback;
        if (!hf) return;
        if (type === 'light') hf.impactOccurred('light');
        if (type === 'success') hf.notificationOccurred('success');
        if (type === 'error') hf.notificationOccurred('error');
    } catch (e) {}
}

// بستن منو با کلیک بیرون
document.addEventListener('click', (e) => {
    const menu = document.getElementById('model-menu');
    const chip = document.getElementById('model-chip');
    if (menu && !menu.classList.contains('hidden') && !menu.contains(e.target) && !chip.contains(e.target)) {
        menu.classList.add('hidden');
    }
});
