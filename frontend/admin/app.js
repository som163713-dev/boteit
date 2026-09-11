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

// ══ شروع ═══════════════════════════════════════
window.addEventListener('load', () => {
    if (token) {
        showDashboard();
    } else {
        document.getElementById('login-screen').classList.add('active');
    }
});
