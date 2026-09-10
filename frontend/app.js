const API = window.location.origin;
let category = 'general';
let history = [];
let loading = false;
let streamBot = null;

/* ══ تم‌های رنگی ══ */
const THEMES = {
    orange:{orange:'#FF6A3D',orange2:'#FF8F66',soft:'#FFF1EB',orangeRgb:'255,106,61',orange2Rgb:'255,143,102'},
    purple:{orange:'#8B5CF6',orange2:'#A78BFA',soft:'#F3F0FF',orangeRgb:'139,92,246',orange2Rgb:'167,139,250'},
    green: {orange:'#10B981',orange2:'#34D399',soft:'#ECFDF5',orangeRgb:'16,185,129',orange2Rgb:'52,211,153'},
    blue:  {orange:'#3B82F6',orange2:'#60A5FA',soft:'#EFF6FF',orangeRgb:'59,130,246',orange2Rgb:'96,165,250'},
    pink:  {orange:'#EC4899',orange2:'#F472B6',soft:'#FDF2F8',orangeRgb:'236,72,153',orange2Rgb:'244,114,182'}
};

function setTheme(name){
    const t = THEMES[name] || THEMES.orange;
    const root = document.documentElement.style;
    root.setProperty('--orange', t.orange);
    root.setProperty('--orange2', t.orange2);
    root.setProperty('--soft', t.soft);
    root.setProperty('--orange-rgb', t.orangeRgb);
    root.setProperty('--orange2-rgb', t.orange2Rgb);
    localStorage.setItem('asha-theme', name);
    document.querySelectorAll('.swatch').forEach(sw => sw.classList.remove('active'));
    const active = document.querySelector('.sw-' + name);
    if (active) active.classList.add('active');
}

function applySavedTheme(){
    const saved = localStorage.getItem('asha-theme') || 'orange';
    setTheme(saved);
}

window.addEventListener('load', () => {
    applySavedTheme();
    updateSideWidth();
    try {
        const WA = window.Eitaa?.WebApp;
        if (!WA) return;
        WA.ready();
        WA.expand();
        WA.setHeaderColor('#FF6A3D');
        WA.setBackgroundColor('#FBF6F1');
        if (WA.disableVerticalSwipes) WA.disableVerticalSwipes();
        WA.BackButton.onClick(goHome);
    } catch (e) {}
});

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

function toast(msg) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.remove('hidden');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.add('hidden'), 2200);
}

/* ══ مدیریت عرض فضای کناری (برای هل‌دادن محتوا) ══ */
function updateSideWidth() {
    const panelOpen = document.getElementById('side-panel').classList.contains('open');
    const railCollapsed = document.body.classList.contains('rail-collapsed');
    let w;
    if (panelOpen) w = 'var(--panel)';
    else if (railCollapsed) w = '0px';
    else w = 'var(--rail)';
    document.documentElement.style.setProperty('--side-width', w);
}

/* ══ بستن همه‌ی پنجره‌های شناور ══ */
function closeAllOverlays() {
    closePanel();
    closeAvatarMenu();
    closeAssistMenu();
    closeThemeMenu();
    document.getElementById('model-menu')?.classList.add('hidden');
}

/* ══ پنل کناری ══ */
function openPanel() {
    closeAvatarMenu();
    closeAssistMenu();
    closeThemeMenu();
    document.getElementById('side-panel').classList.add('open');
    updateSideWidth();
}

function closePanel() {
    document.getElementById('side-panel').classList.remove('open');
    updateSideWidth();
}

/* ══ منوی آواتار ══ */
function toggleAvatarMenu() {
    const menu = document.getElementById('avatar-menu');
    if (menu.classList.contains('open')) {
        closeAvatarMenu();
    } else {
        closePanel();
        closeAssistMenu();
        closeThemeMenu();
        menu.classList.add('open');
        document.getElementById('avatar-backdrop').classList.remove('hidden');
    }
}

function closeAvatarMenu() {
    document.getElementById('avatar-menu')?.classList.remove('open');
    document.getElementById('avatar-backdrop')?.classList.add('hidden');
}

/* ══ منوی شیشه‌ای دستیارها ══ */
function toggleAssistMenu() {
    const menu = document.getElementById('assist-menu');
    if (menu.classList.contains('open')) {
        closeAssistMenu();
    } else {
        closeAvatarMenu();
        closeThemeMenu();
        menu.classList.remove('hidden');
        requestAnimationFrame(() => menu.classList.add('open'));
    }
}

function closeAssistMenu() {
    const menu = document.getElementById('assist-menu');
    if (!menu) return;
    menu.classList.remove('open');
    setTimeout(() => menu.classList.add('hidden'), 300);
}

/* ══ منوی تم رنگی ══ */
function toggleThemeMenu() {
    const menu = document.getElementById('theme-menu');
    if (menu.classList.contains('open')) {
        closeThemeMenu();
    } else {
        closeAvatarMenu();
        closeAssistMenu();
        menu.classList.remove('hidden');
        const saved = localStorage.getItem('asha-theme') || 'orange';
        document.querySelectorAll('.swatch').forEach(sw => sw.classList.remove('active'));
        document.querySelector('.sw-' + saved)?.classList.add('active');
        requestAnimationFrame(() => menu.classList.add('open'));
    }
}

function closeThemeMenu() {
    const menu = document.getElementById('theme-menu');
    if (!menu) return;
    menu.classList.remove('open');
    setTimeout(() => menu.classList.add('hidden'), 250);
}

function toggleRail() {
    const collapsed = document.body.classList.toggle('rail-collapsed');
    const openBtn = document.getElementById('rail-open-btn');
    if (openBtn) openBtn.classList.toggle('hidden', !collapsed);
    updateSideWidth();
}

function toggleModels() {
    closeAvatarMenu();
    closeAssistMenu();
    closeThemeMenu();
    document.getElementById('model-menu').classList.toggle('hidden');
}

function pickModel(name) {
    document.getElementById('model-label').textContent = name;
    document.getElementById('model-menu').classList.add('hidden');
    toast('مدل: ' + name);
}

function focusComposer() {
    document.getElementById('user-input').focus();
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
    closeAllOverlays();
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
        if (label) label.textContent = title;
    }
    haptic('light');
    closeAllOverlays();
    try { window.Eitaa?.WebApp?.BackButton?.show(); } catch (e) {}
    setTimeout(() => document.getElementById('user-input').focus(), 200);
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
            body: JSON.stringify({ message: text, category, history: history.slice(-10) })
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
        console.error(err);
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

function haptic(type) {
    try {
        const hf = window.Eitaa?.WebApp?.HapticFeedback;
        if (!hf) return;
        if (type === 'light')   hf.impactOccurred('light');
        if (type === 'success') hf.notificationOccurred('success');
        if (type === 'error')   hf.notificationOccurred('error');
    } catch (e) {}
}

document.addEventListener('click', (e) => {
    const menu = document.getElementById('model-menu');
    const chip = document.getElementById('model-chip');
    if (menu && !menu.classList.contains('hidden') &&
        !menu.contains(e.target) && chip && !chip.contains(e.target)) {
        menu.classList.add('hidden');
    }

    const avMenu = document.getElementById('avatar-menu');
    const avBtn = document.getElementById('avatar-btn');
    if (avMenu && avMenu.classList.contains('open') &&
        !avMenu.contains(e.target) && avBtn && !avBtn.contains(e.target)) {
        closeAvatarMenu();
    }

    const asMenu = document.getElementById('assist-menu');
    if (asMenu && asMenu.classList.contains('open') &&
        !asMenu.contains(e.target) && !e.target.closest('.c-assist') && !e.target.closest('.fpill')) {
        closeAssistMenu();
    }

    const thMenu = document.getElementById('theme-menu');
    if (thMenu && thMenu.classList.contains('open') &&
        !thMenu.contains(e.target) && !e.target.closest('.rail-ico') && !e.target.closest('.side-item')) {
        closeThemeMenu();
    }
});
