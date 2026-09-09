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
        WA.setHeaderColor('#007AFF');
        WA.setBackgroundColor('#f2f2f7');
        if (WA.disableVerticalSwipes) WA.disableVerticalSwipes();
        WA.BackButton.onClick(goHome);
        WA.onEvent('themeChanged', () => console.log('تم تغییر کرد'));
        console.log('✅ ایتا SDK متصل شد');
    } catch (e) { console.warn('خارج از محیط ایتا:', e.message); }
});

const WELCOME = {
    shopping: 'سلام! 🛍️ به فروشگاه هوشمند خوش اومدی!\nچه محصولی دنبالش هستی؟',
    clinic: 'سلام! 🏥 به کلینیک هوشمند خوش اومدی!\nچطور میتونم کمکت کنم؟',
    realestate: 'سلام! 🏠 به مشاور هوشمند املاک خوش اومدی!\nدنبال خرید، فروش یا اجاره هستی؟',
    education: 'سلام! 📚 به دستیار آموزشی خوش اومدی!\nچه سوال درسی داری؟',
    restaurant: 'سلام! 🍕 به رستوران هوشمند خوش اومدی!\nمنو رو ببین یا سفارش بده!',
    legal: 'سلام! ⚖️ به مشاور حقوقی هوشمند خوش اومدی!\nسوالت رو بپرس!',
    finance: 'سلام! 💰 به مشاور مالی هوشمند خوش اومدی!\nچطور میتونم کمکت کنم؟',
    support: 'سلام! 🔧 به پشتیبانی فنی خوش اومدی!\nمشکلت رو توضیح بده!',
    general: 'سلام! 🤖 من دستیار هوشمند توام!\nهر سوالی داری بپرس!'
};

function selectCategory(cat, title) {
    category = cat;
    history = [];
    document.getElementById('chat-title').textContent = title;
    const box = document.getElementById('messages');
    box.innerHTML = <div class="welcome-bubble"></div>;
    showScreen('chat-screen');
    haptic('light');
    try { window.Eitaa?.WebApp?.BackButton?.show(); } catch(e) {}
    setTimeout(() => document.getElementById('user-input').focus(), 350);
}

function goHome() {
    history = [];
    showScreen('home-screen');
    haptic('light');
    try { window.Eitaa?.WebApp?.BackButton?.hide(); } catch(e) {}
}

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function onEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

async function sendMessage() {
    if (loading) return;
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
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
            if (streamBot) { streamBot.textContent = fullText; scrollBottom(); }
        }
        if (data.done) saveHistory();
    };

    try {
        const res = await fetch(${API}/chat/stream, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, category: category, history: history.slice(-10) })
        });

        if (!res.ok || !res.body) throw new Error(HTTP );

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
                try { handleData(JSON.parse(line.slice(5).trim())); } catch (_) {}
            }
        }

        buffer += decoder.decode();
        if (buffer.startsWith('data:')) {
            try { handleData(JSON.parse(buffer.slice(5).trim())); } catch (_) {}
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
    div.className = msg ;
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
    div.innerHTML = <div class="dots"><span></span><span></span><span></span></div><div id="cold-hint" class="cold-hint">☕ در حال بیدار کردن سرور هوشمند...<br><small>بار اول کمی زمان می‌بره</small></div>;
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
    const confirm_fn = (ok) => {
        if (!ok) return;
        history = [];
        document.getElementById('messages').innerHTML = <div class="welcome-bubble">چت پاک شد! سوال جدیدت رو بپرس 😊</div>;
        haptic('light');
    };
    try {
        const WA = window.Eitaa?.WebApp;
        if (WA?.showConfirm) WA.showConfirm('مکالمه پاک بشه؟', confirm_fn);
        else confirm_fn(confirm('مکالمه پاک بشه؟'));
    } catch(e) { confirm_fn(confirm('مکالمه پاک بشه؟')); }
}

function haptic(type) {
    try {
        const hf = window.Eitaa?.WebApp?.HapticFeedback;
        if (!hf) return;
        if (type === 'light') hf.impactOccurred('light');
        if (type === 'success') hf.notificationOccurred('success');
        if (type === 'error') hf.notificationOccurred('error');
    } catch(e) {}
}
