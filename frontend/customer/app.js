const STORAGE_KEY = 'factory_api_key';

// ══ راه‌اندازی ═══════════════════════════════════
window.addEventListener('DOMContentLoaded', () => {
    const savedKey = localStorage.getItem(STORAGE_KEY);
    if (savedKey) {
        boot(savedKey);
    }
    document.getElementById('login-key').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doLogin();
    });
});

async function boot(apiKey) {
    try {
        const res = await fetch(`/factory/access?api_key=${encodeURIComponent(apiKey)}`);
        if (!res.ok) throw new Error('invalid key');
        const data = await res.json();

        window.currentApiKey = apiKey;
        localStorage.setItem(STORAGE_KEY, apiKey);
        showDashboard(data);
    } catch (e) {
        localStorage.removeItem(STORAGE_KEY);
        showLogin('کد دسترسی معتبر نیست یا منقضی شده.');
    }
}

function showLogin(message) {
    document.getElementById('screen-login').classList.remove('hidden');
    document.getElementById('screen-dashboard').classList.add('hidden');
    document.getElementById('login-error').textContent = message || '';
}

async function doLogin() {
    const key = document.getElementById('login-key').value.trim();
    if (!key) {
        document.getElementById('login-error').textContent = 'کد دسترسی رو وارد کن.';
        return;
    }
    document.getElementById('login-error').textContent = '';
    document.getElementById('login-btn').disabled = true;
    await boot(key);
    document.getElementById('login-btn').disabled = false;
}

function doLogout() {
    localStorage.removeItem(STORAGE_KEY);
    window.currentApiKey = null;
    document.getElementById('screen-dashboard').classList.add('hidden');
    document.getElementById('login-key').value = '';
    showLogin('');
}

// ══ داشبورد ═══════════════════════════════════════
function showDashboard(data) {
    document.getElementById('screen-login').classList.add('hidden');
    document.getElementById('screen-dashboard').classList.remove('hidden');

    document.getElementById('biz-name').textContent = data.customer.business;
    document.getElementById('biz-plan').textContent = `پلن: ${data.customer.plan}`;

    renderAgentGrid(data.agents);
    loadHistory();
}

function renderAgentGrid(agents) {
    const grid = document.getElementById('agent-grid');
    grid.innerHTML = agents.map(a => `
        <div class="agent-card ${a.enabled ? '' : 'locked'}" data-key="${a.key}"
             onclick="${a.enabled ? `openTool('${a.key}')` : ''}">
            <div class="agent-top">
                <h3>${a.name}</h3>
                <span class="status-dot ${a.enabled ? '' : 'off'}"></span>
            </div>
            <p>${a.description}</p>
            ${a.enabled ? '' : '<div class="lock-note">جزو پلن فعلیت نیست</div>'}
        </div>
    `).join('');
}

// ══ پنل ابزار ═══════════════════════════════════════
function openTool(key) {
    document.querySelectorAll('.agent-card').forEach(c => {
        c.classList.toggle('active-open', c.dataset.key === key);
    });

    const panel = document.getElementById('tool-panel');
    panel.classList.remove('hidden');

    if (key === 'content') {
        panel.innerHTML = `
            <h2>✍️ تولید محتوا</h2>
            <input id="t-topic" type="text" placeholder="موضوع محتوا (مثلاً: تخفیف پاییزه)">
            <button class="run-btn" onclick="runContent()">تولید کن</button>
            <div id="t-output"></div>
        `;
    } else if (key === 'campaign') {
        panel.innerHTML = `
            <h2>📣 طرح کمپین</h2>
            <input id="t-budget" type="number" placeholder="بودجه (تومان)" value="2000000">
            <input id="t-goal" type="text" placeholder="هدف (اختیاری)">
            <button class="run-btn" onclick="runCampaign()">بساز</button>
            <div id="t-output"></div>
        `;
    } else if (key === 'report') {
        panel.innerHTML = `
            <h2>📊 گزارش تحلیلی</h2>
            <input id="t-days" type="number" placeholder="بازه (روز)" value="7">
            <button class="run-btn" onclick="runReport()">بگیر</button>
            <div id="t-output"></div>
        `;
    }

    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function setToolLoading(loading) {
    const btn = document.querySelector('.tool-panel .run-btn');
    if (btn) btn.disabled = loading;
}

function showToolOutput(html) {
    const out = document.getElementById('t-output');
    if (out) {
        out.innerHTML = `<div class="tool-output">${html}</div>`;
    }
}

async function runContent() {
    const topic = document.getElementById('t-topic').value.trim();
    if (!topic) return showToolOutput('❌ موضوع رو بنویس.');

    setToolLoading(true);
    showToolOutput('⏳ در حال تولید...');
    try {
        const res  = await fetch('/factory/content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: window.currentApiKey, topic })
        });
        const data = await res.json();
        if (!res.ok) { showToolOutput(`❌ ${data.detail}`); return; }
        showToolOutput(data.output);
        loadHistory();
    } catch (e) {
        showToolOutput('❌ خطای اتصال.');
    } finally {
        setToolLoading(false);
    }
}

async function runCampaign() {
    const budget_toman = parseInt(document.getElementById('t-budget').value) || 0;
    const goal = document.getElementById('t-goal').value.trim();

    setToolLoading(true);
    showToolOutput('⏳ در حال ساخت طرح...');
    try {
        const res  = await fetch('/factory/campaign', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: window.currentApiKey, budget_toman, goal })
        });
        const data = await res.json();
        if (!res.ok) { showToolOutput(`❌ ${data.detail}`); return; }

        const kpiLine = data.kpis && data.kpis.status === 'ok'
            ? `<div class="kpi-strip">پیام ۷ روز اخیر: ${data.kpis.messages_this_window} | رشد: ${data.kpis.growth_pct ?? 'نامشخص'}%</div>`
            : (data.kpis ? `<div class="kpi-strip">${data.kpis.message}</div>` : '');
        showToolOutput(kpiLine + data.output);
        loadHistory();
    } catch (e) {
        showToolOutput('❌ خطای اتصال.');
    } finally {
        setToolLoading(false);
    }
}

async function runReport() {
    const days = parseInt(document.getElementById('t-days').value) || 7;

    setToolLoading(true);
    showToolOutput('⏳ در حال ساخت گزارش...');
    try {
        const res  = await fetch(`/factory/report?api_key=${encodeURIComponent(window.currentApiKey)}&days=${days}`);
        const data = await res.json();
        if (!res.ok) { showToolOutput(`❌ ${data.detail}`); return; }
        showToolOutput(data.narrative);
        loadHistory();
    } catch (e) {
        showToolOutput('❌ خطای اتصال.');
    } finally {
        setToolLoading(false);
    }
}

// ══ تاریخچه ═══════════════════════════════════════
async function loadHistory() {
    if (!window.currentApiKey) return;
    try {
        const res   = await fetch(`/factory/history?api_key=${encodeURIComponent(window.currentApiKey)}`);
        const items = await res.json();

        const list = document.getElementById('history-list');
        if (!items.length) {
            list.innerHTML = '<div class="empty-note">هنوز چیزی ساخته نشده.</div>';
            return;
        }
        const kindLabel = { content: 'محتوا', campaign: 'کمپین', report: 'گزارش' };
        list.innerHTML = items.map(i => `
            <div class="history-item">
                <div class="h-top">
                    <span class="h-kind">${kindLabel[i.kind] || i.kind}</span>
                    <span>${new Date(i.created_at).toLocaleString('fa-IR')}</span>
                </div>
                <div class="h-body">${(i.output_text || '').substring(0, 160)}${i.output_text && i.output_text.length > 160 ? '…' : ''}</div>
            </div>
        `).join('');
    } catch (e) {
        console.error('خطای لود تاریخچه:', e);
    }
}
