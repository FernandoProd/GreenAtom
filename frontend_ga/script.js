// ================== ИНТЕРАКТИВНАЯ СЕТКА CANVAS ==================
const canvas = document.getElementById('gridCanvas');
const ctx = canvas.getContext('2d');
const CELL = 60;
const RADIUS = 180;
const STRENGTH = 22;
const LERP = 0.055;

let mouse = { x: -9999, y: -9999 };
let smoothMouse = { x: -9999, y: -9999 };

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

document.addEventListener('mousemove', e => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});
document.addEventListener('mouseleave', () => {
    mouse.x = -9999;
    mouse.y = -9999;
});

function drawGrid() {
    // Плавное следование за мышью
    if (mouse.x === -9999) {
        smoothMouse.x += (-9999 - smoothMouse.x) * 0.08;
        smoothMouse.y += (-9999 - smoothMouse.y) * 0.08;
    } else {
        smoothMouse.x += (mouse.x - smoothMouse.x) * LERP;
        smoothMouse.y += (mouse.y - smoothMouse.y) * LERP;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(126,217,87,0.07)';
    ctx.lineWidth = 1;

    const cols = Math.ceil(canvas.width / CELL) + 2;
    const rows = Math.ceil(canvas.height / CELL) + 2;

    // Вертикальные линии
    for (let i = -1; i < cols; i++) {
        ctx.beginPath();
        const baseX = i * CELL;
        for (let j = -1; j <= rows; j++) {
            const baseY = j * CELL;
            const dx = baseX - smoothMouse.x;
            const dy = baseY - smoothMouse.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            let offsetX = 0, offsetY = 0;
            if (dist < RADIUS) {
                const force = (RADIUS - dist) / RADIUS;
                const angle = Math.atan2(dy, dx);
                const push = force * STRENGTH;
                offsetX = Math.cos(angle) * push;
                offsetY = Math.sin(angle) * push;
            }
            const x = baseX + offsetX;
            const y = baseY + offsetY;
            if (j === -1) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
    }

    // Горизонтальные линии
    for (let j = -1; j < rows; j++) {
        ctx.beginPath();
        const baseY = j * CELL;
        for (let i = -1; i <= cols; i++) {
            const baseX = i * CELL;
            const dx = baseX - smoothMouse.x;
            const dy = baseY - smoothMouse.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            let offsetX = 0, offsetY = 0;
            if (dist < RADIUS) {
                const force = (RADIUS - dist) / RADIUS;
                const angle = Math.atan2(dy, dx);
                const push = force * STRENGTH;
                offsetX = Math.cos(angle) * push;
                offsetY = Math.sin(angle) * push;
            }
            const x = baseX + offsetX;
            const y = baseY + offsetY;
            if (i === -1) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
    }

    requestAnimationFrame(drawGrid);
}
drawGrid();

// ================== ЛОГИКА ПРИЛОЖЕНИЯ ==================
const USER_SERVICE = '/api/users';
const TICKET_SERVICE = '/api/tickets';

let currentUser = null;      // { user_id, email }
let currentTicket = null;    // { ticket_id, status, user_id }

const heroCta = document.getElementById('heroCta');
const ticketSection = document.getElementById('ticketSection');
const ticketResult = document.getElementById('ticketResult');
const ticketUserSpan = document.getElementById('ticketUser');
const ticketCodeSpan = document.getElementById('ticketCode');
const ticketStatusText = document.getElementById('ticketStatusText');
const getTicketBtn = document.getElementById('getTicketBtn');
const revokeTicketBtn = document.getElementById('revokeTicketBtn');
const navActions = document.getElementById('navActions');

// Модальные окна
function openModal(type) {
    document.getElementById(type + 'Overlay').classList.add('open');
}
function closeModal(id) {
    document.getElementById(id).classList.remove('open');
}
function overlayClick(e, id) {
    if (e.target === document.getElementById(id)) closeModal(id);
}
function switchModal(from, to) {
    closeModal(from);
    setTimeout(() => openModal(to.replace('Overlay','')), 200);
}

function clearErrors() {
    document.getElementById('loginError').classList.remove('show');
    document.getElementById('regError').classList.remove('show');
}

// Инициализация при загрузке
function loadSession() {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showLoggedInUI();
        checkExistingTicket();
    }
}
function saveSession() {
    if (currentUser) localStorage.setItem('user', JSON.stringify(currentUser));
    else localStorage.removeItem('user');
}
function clearSession() {
    localStorage.removeItem('user');
    currentUser = null;
    currentTicket = null;
    heroCta.style.display = '';
    ticketSection.classList.remove('visible');
    ticketResult.classList.remove('visible');
    navActions.innerHTML = `
        <button class="btn btn-outline" onclick="openModal('login')">
            <i class="fa-solid fa-right-to-bracket"></i> Вход
        </button>
        <button class="btn btn-solid" onclick="openModal('register')">
            <i class="fa-solid fa-user-plus"></i> Регистрация
        </button>
    `;
}

// Проверка билета через API
async function checkExistingTicket() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${TICKET_SERVICE}/tickets/by-user/${currentUser.user_id}`);
        if (res.ok) {
            const data = await res.json();
            currentTicket = data;
            displayTicket();
        } else if (res.status === 404) {
            currentTicket = null;
            ticketSection.classList.add('visible');
            ticketResult.classList.remove('visible');
            getTicketBtn.style.display = '';
        } else {
            console.error('Ошибка проверки билета:', res.status);
        }
    } catch (err) {
        console.error('Сетевая ошибка при проверке билета:', err);
    }
}

function showLoggedInUI() {
    heroCta.style.display = 'none';
    ticketUserSpan.textContent = currentUser.email;
    navActions.innerHTML = `
        <span style="color:#888; font-size:0.88rem;">
            <i class="fa-solid fa-circle-user" style="color:var(--green)"></i> ${currentUser.email}
        </span>
        <button class="btn btn-outline" onclick="logout()" style="color:#888; border-color:rgba(255,255,255,0.1);">
            <i class="fa-solid fa-right-from-bracket"></i> Выйти
        </button>
    `;
}

function displayTicket() {
    if (!currentTicket) return;
    ticketSection.classList.remove('visible');
    ticketResult.classList.add('visible');
    ticketCodeSpan.textContent = currentTicket.ticket_id;
    ticketStatusText.textContent = 'Статус: ' + currentTicket.status;
    revokeTicketBtn.style.display = '';
    getTicketBtn.style.display = 'none';
}

// Аутентификация
async function doLogin() {
    clearErrors();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');
    if (!email || !password) {
        errorEl.textContent = 'Заполните все поля';
        errorEl.classList.add('show');
        return;
    }
    try {
        const res = await fetch(`${USER_SERVICE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка входа');
        currentUser = { user_id: data.user_id, email };
        saveSession();
        closeModal('loginOverlay');
        showLoggedInUI();
        checkExistingTicket();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.add('show');
    }
}

async function doRegister() {
    clearErrors();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    const errorEl = document.getElementById('regError');
    if (!email || !password) {
        errorEl.textContent = 'Заполните все поля';
        errorEl.classList.add('show');
        return;
    }
    if (password.length < 4) {
        errorEl.textContent = 'Пароль минимум 4 символа';
        errorEl.classList.add('show');
        return;
    }
    try {
        const res = await fetch(`${USER_SERVICE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка регистрации');
        currentUser = { user_id: data.user_id, email };
        saveSession();
        closeModal('registerOverlay');
        showLoggedInUI();
        // новый пользователь — билета нет
        ticketSection.classList.add('visible');
        ticketResult.classList.remove('visible');
        getTicketBtn.style.display = '';
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.add('show');
    }
}

// Работа с билетом
async function getTicket() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${TICKET_SERVICE}/tickets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.user_id })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Не удалось создать билет');
        currentTicket = data;
        displayTicket();
    } catch (err) {
        alert(err.message);
    }
}

async function revokeTicket() {
    if (!currentTicket) return;
    try {
        const res = await fetch(`${TICKET_SERVICE}/tickets/${currentTicket.ticket_id}`, {
            method: 'DELETE'
        });
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Ошибка отзыва');
        }
        currentTicket = null;
        ticketResult.classList.remove('visible');
        ticketSection.classList.add('visible');
        getTicketBtn.style.display = '';
    } catch (err) {
        alert(err.message);
    }
}

// Выход
function logout() {
    clearSession();
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('regEmail').value = '';
    document.getElementById('regPassword').value = '';
}

// Enter key
document.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        if (document.getElementById('loginOverlay').classList.contains('open')) doLogin();
        if (document.getElementById('registerOverlay').classList.contains('open')) doRegister();
    }
});

// Старт
loadSession();
