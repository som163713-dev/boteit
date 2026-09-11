const API = window.location.origin;
let token = localStorage.getItem('admin_token') || '';

// ══ لاگین ══════════════════════════════════════
async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const res = await fetch(`${API}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (res.ok) {
            token = data.token;
            localStorage.setItem('admin_token', token);
            showDashboard();
        } else {
            document.getElementById('login-error').textContent = data.detail;
        }
    } catch (e) {
        document.getElementById('login-error').textContent = 'خطای اتصال!';
    }
}

function logout() {
    localStorage.removeItem('admin_token');
    location.reload();
}

// ══ داشبورد ════════════════════════════════════
function showDashboard() {
    document.querySelectorAll('.screen').forEach(s => {
        s.classList.remove('active');
    });
    document.getElementById('dashboard-screen').classList.add('active');
    loadStats();
    loadCustomers();
}

// ══ تب‌ها ═══════════════════════════════════════
function showTab(name) {
    document.querySelectorAll('.tab').forEach(t => {
        t.classList.remove('active');
    });
    document.querySelectorAll('.nav-btn').forEach(b => {
        b.classList.remove('active');
    });
    document.getElementById(`tab-${name}`).classList.add('active');
    event.target.classList.add('active');

    if (name === 'factory') {
        loadFactoryCustomers();
    }
}

// ══ آمار ════════════════════════════════════════
async function loadStats() {
    try {
        const res = await fetch(`${API}/stats/dashboard`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        const ov   = data.overview;

        document.getElementById('total-customers').textContent  =
            ov.total_customers;
        document.getElementById('active-customers').textContent =
            ov.active_customers;
        document.getElementById('total-messages').textContent   =
            ov.total_messages.toLocaleString();
        document.getElementById('today-messages').textContent   =
            ov.today_messages.toLocaleString();
        document.getElementById('month-revenue').textContent    =
            ov.month_revenue.toLocaleString();
        document.getElementById('total-revenue').textContent    =
            ov.total_revenue.toLocaleString();

        // فعال‌ترین مشتریان
        const tbody = document.querySelector('#top-customers-table tbody');
        tbody.innerHTML = data.top_customers.map(c => `
            <tr>
                <td>${c.name}</td>
                <td>${c.business}</td>
                <td>${c.msg_count}</td>
            </tr>
        `).join('');

        // حوزه‌ها
        const catBody = document.querySelector('#categories-table tbody');
        catBody.innerHTML = data.categories.map(c => `
            <tr>
                <td>${c.name}</td>
                <td>${c.count}</td>
            </tr>
        `).join('');

    } catch (e) {
        console.error('خطای لود آمار:', e);
    }
}

// ══ مشتریان ════════════════════════════════════
async function loadCustomers() {
    try {
        const res = await fetch(`${API}/admin/customers`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const customers = await res.json();

        const tbody = document.querySelector('#customers-table tbody');
        tbody.innerHTML = customers.map(c => `
            <tr>
                <td>${c.name}</td>
                <td>${c.business}</td>
                <td>${c.phone}</td>
                <td>${c.category}</td>
                <td>
                    <span class="badge ${c.plan}">${c.plan}</span>
                </td>
                <td>
                    <span class="badge ${c.is_active ? 'active' : 'inactive'}">
                        ${c.is_active ? 'فعال' : 'غیرفعال'}
                    </span>
                </td>
                <td>${c.expires_at ? 
                    new Date(c.expires_at).toLocaleDateString('fa-IR') : '-'}
                </td>
                <td>
                    <span class="api-key" 
                          onclick="copyKey('${c.api_key}')" 
                          title="کلیک برای کپی">
                        ${c.api_key.substring(0, 20)}...
                    </span>
                </td>
                <td>
                    <button class="action-btn delete" 
                            onclick="deleteCustomer(${c.id})">
                        🗑 حذف
                    </button>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        console.error('خطای لود مشتریان:', e);
    }
}

// ══ افزودن مشتری ═══════════════════════════════
function showAddCustomer() {
    document.getElementById('add-customer-form').classList.remove('hidden');
}

function hideAddCustomer() {
    document.getElementById('add-customer-form').classList.add('hidden');
}

async function addCustomer() {
    const data = {
        name:     document.getElementById('c-name').value,
        business: document.getElementById('c-business').value,
        phone:    document.getElementById('c-phone').value,
        category: document.getElementById('c-category').value,
        plan:     document.getElementById('c-plan').value,
        days:     parseInt(document.getElementById('c-days').value)
    };

    try {
        const res = await fetch(`${API}/admin/customers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        if (res.ok) {
            alert(`✅ مشتری اضافه شد!\nAPI Key:\n${result.api_key}`);
            hideAddCustomer();
            loadCustomers();
            loadStats();
        } else {
            alert(`❌ خطا: ${result.detail}`);
        }
    } catch (e) {
        alert('خطای اتصال!');
    }
}

// ══ حذف مشتری ══════════════════════════════════
async function deleteCustomer(id) {
    if (!confirm('مشتری حذف بشه؟')) return;

    try {
        const res = await fetch(`${API}/admin/customers/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            loadCustomers();
            loadStats();
        }
    } catch (e) {
        alert('خطای حذف!');
    }
}

// ══ کپی API Key ════════════════════════════════
function copyKey(key) {
    navigator.clipboard.writeText(key);
    alert('API Key کپی شد! ✅');
}

// ══ کارخانه‌ی ایجنت ═════════════════════════════
async function loadFactoryCustomers() {
    try {
        const res = await fetch(`${API}/admin/customers`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const customers = await res.json();

        const select = document.getElementById('f-customer');
        select.innerHTML = customers.map(c => `
            <option value="${c.api_key}">${c.name} — ${c.business}</option>
        `).join('');
    } catch (e) {
        console.error('خطای لود مشتریان کارخانه:', e);
    }
}

function getFactoryApiKey() {
    const select = document.getElementById('f-customer');
    return select.value;
}

function showFactoryOutput(html) {
    const box = document.getElementById('factory-output');
    box.classList.remove('hidden');
    box.innerHTML = html;
}

async function runFactoryContent() {
    const api_key = getFactoryApiKey();
    const topic   = document.getElementById('f-content-topic').value;
    if (!api_key) return alert('اول یه مشتری انتخاب کن');
    if (!topic)   return alert('موضوع محتوا رو بنویس');

    showFactoryOutput('⏳ در حال تولید محتوا...');
    try {
        const res  = await fetch(`${API}/factory/content`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key, topic })
        });
        const data = await res.json();
        if (!res.ok) return showFactoryOutput(`❌ خطا: ${data.detail}`);

        showFactoryOutput(`<h4>✍️ محتوای تولیدشده</h4><pre>${data.output}</pre>`);
        loadFactoryHistory();
    } catch (e) {
        showFactoryOutput('❌ خطای اتصال!');
    }
}

async function runFactoryCampaign() {
    const api_key      = getFactoryApiKey();
    const budget_toman = parseInt(document.getElementById('f-campaign-budget').value) || 0;
    const goal         = document.getElementById('f-campaign-goal').value;
    if (!api_key) return alert('اول یه مشتری انتخاب کن');

    showFactoryOutput('⏳ در حال ساخت طرح کمپین...');
    try {
        const res  = await fetch(`${API}/factory/campaign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key, budget_toman, goal })
        });
        const data = await res.json();
        if (!res.ok) return showFactoryOutput(`❌ خطا: ${data.detail}`);

        const kpiLine = data.kpis && data.kpis.status === 'ok'
            ? `پیام ۷ روز اخیر: ${data.kpis.messages_this_window} | رشد: ${data.kpis.growth_pct ?? 'نامشخص'}%`
            : (data.kpis ? data.kpis.message : '');

        showFactoryOutput(`
            <h4>📣 طرح کمپین</h4>
            <div class="kpi-line">${kpiLine}</div>
            <pre>${data.output}</pre>
        `);
        loadFactoryHistory();
    } catch (e) {
        showFactoryOutput('❌ خطای اتصال!');
    }
}

async function runFactoryReport() {
    const api_key = getFactoryApiKey();
    const days    = parseInt(document.getElementById('f-report-days').value) || 7;
    if (!api_key) return alert('اول یه مشتری انتخاب کن');

    showFactoryOutput('⏳ در حال ساخت گزارش...');
    try {
        const res  = await fetch(`${API}/factory/report?api_key=${encodeURIComponent(api_key)}&days=${days}`);
        const data = await res.json();
        if (!res.ok) return showFactoryOutput(`❌ خطا: ${data.detail}`);

        showFactoryOutput(`
            <h4>📊 گزارش واقعی تعامل (${days} روز اخیر)</h4>
            <pre>${JSON.stringify(data.kpis, null, 2)}</pre>
            <pre>${data.narrative}</pre>
        `);
        loadFactoryHistory();
    } catch (e) {
        showFactoryOutput('❌ خطای اتصال!');
    }
}

async function loadFactoryHistory() {
    const api_key = getFactoryApiKey();
    if (!api_key) return;

    try {
        const res   = await fetch(`${API}/factory/history?api_key=${encodeURIComponent(api_key)}`);
        const items = await res.json();

        const tbody = document.querySelector('#factory-history-table tbody');
        tbody.innerHTML = items.map(i => `
            <tr>
                <td>${i.kind}</td>
                <td>${(i.input_brief || '').substring(0, 40)}</td>
                <td>${(i.output_text || '').substring(0, 60)}...</td>
                <td>${new Date(i.created_at).toLocaleString('fa-IR')}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('خطای لود تاریخچه:', e);
    }
}

// ══ تنظیمات ═════════════════════════════════════
async function changePassword() {
    const old_password  = document.getElementById('s-old-password').value;
    const new_password  = document.getElementById('s-new-password').value;
    const new_password2 = document.getElementById('s-new-password2').value;
    const msgBox = document.getElementById('settings-message');
    msgBox.className = '';
    msgBox.textContent = '';

    if (!old_password || !new_password) {
        msgBox.textContent = '❌ رمز فعلی و رمز جدید رو پر کن.';
        msgBox.className = 'error';
        return;
    }
    if (new_password !== new_password2) {
        msgBox.textContent = '❌ تکرار رمز جدید با رمز جدید یکی نیست.';
        msgBox.className = 'error';
        return;
    }
    if (new_password.length < 6) {
        msgBox.textContent = '❌ رمز جدید باید حداقل ۶ کاراکتر باشه.';
        msgBox.className = 'error';
        return;
    }

    try {
        const res = await fetch(`${API}/admin/change-password`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ old_password, new_password })
        });
        const data = await res.json();

        if (res.ok) {
            msgBox.textContent = '✅ رمز عبور با موفقیت تغییر کرد.';
            msgBox.className = 'success';
            document.getElementById('s-old-password').value = '';
            document.getElementById('s-new-password').value = '';
            document.getElementById('s-new-password2').value = '';
        } else {
            msgBox.textContent = `❌ خطا: ${data.detail}`;
            msgBox.className = 'error';
        }
    } catch (e) {
        msgBox.textContent = '❌ خطای اتصال!';
        msgBox.className = 'error';
    }
}

// ══ شروع ═══════════════════════════════════════
window.addEventListener('load', () => {
    if (token) {
        showDashboard();
    } else {
        document.getElementById('login-screen').classList.add('active');
    }
});
