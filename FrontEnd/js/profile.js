/**
 * Profile & Inventory модули.
 * Профиль: ава-заглушка, юзернейм, кнопки "Сменить юзернейм" / "Сменить пароль".
 * Инвентарь: слайдеры по категориям, выбор активного скина.
 */

import { fetchApi } from './api.js';
import { getCurrentUser, applyUser } from './auth.js';

/* ================ Shared ================ */

let profileOverlay = null;
let inventoryOverlay = null;
let activeSkins = {};
let catalogSkinsCache = null;

const CATEGORY_META = {
  birds: { label: 'Скины птиц', icon: 'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zm-4 7c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5z' },
  pipes: { label: 'Скины труб', icon: 'M12 2v20M2 12h20' },
  backgrounds: { label: 'Скины фона', icon: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' },
};

function buildOverlay(id, title, wide) {
  const overlay = document.createElement('div');
  overlay.className = 'auth-overlay';
  overlay.id = id;
  overlay.innerHTML = `
    <div class="auth-modal${wide ? ' auth-modal--wide' : ''}">
      <button class="auth-modal__close" aria-label="Закрыть">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6 6 18M6 6l12 12"/>
        </svg>
      </button>
      <h2 class="auth-modal__title">${title}</h2>
      <div class="auth-modal__content"></div>
    </div>
  `;
  document.body.appendChild(overlay);

  const closeBtn = overlay.querySelector('.auth-modal__close');
  closeBtn.addEventListener('click', () => closeModal(overlay));
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal(overlay);
  });

  return overlay;
}

function closeModal(overlay) {
  if (overlay) overlay.classList.remove('auth-overlay--open');
}

function openModal(overlay) {
  if (overlay) overlay.classList.add('auth-overlay--open');
}

/* ================ Profile ================ */

export function openProfile() {
  const user = getCurrentUser();
  if (!user) return;

  if (!profileOverlay) {
    profileOverlay = buildOverlay('profile-overlay', 'Профиль');
  }

  renderProfile();
  openModal(profileOverlay);
}

function renderProfile() {
  const content = profileOverlay.querySelector('.auth-modal__content');
  const user = getCurrentUser();
  if (!user) return;

  content.innerHTML = `
    <div class="profile-card">
      <div class="profile-card__avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="8" r="4"/>
          <path d="M20 21a8 8 0 1 0-16 0"/>
        </svg>
      </div>
      <div class="profile-card__info">
        <h3 class="profile-card__name">${escapeHtml(user.username)}</h3>
        <p class="profile-card__balance-label">Баланс: ${user.balance ?? 0} монет</p>
      </div>
      <div class="profile-card__actions">
        <button class="profile-card__btn" data-action="change-username">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Сменить юзернейм
        </button>
        <button class="profile-card__btn" data-action="change-password">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          Сменить пароль
        </button>
      </div>
      <div class="profile-change-form" data-change-form style="display:none"></div>
    </div>
  `;

  // Обработчики
  content.querySelector('[data-action="change-username"]').addEventListener('click', () => {
    showChangeForm('username');
  });
  content.querySelector('[data-action="change-password"]').addEventListener('click', () => {
    showChangeForm('password');
  });
}

function showChangeForm(type) {
  const content = profileOverlay.querySelector('.auth-modal__content');
  const formContainer = content.querySelector('[data-change-form]');
  const user = getCurrentUser();
  if (!user) return;

  if (type === 'username') {
    formContainer.innerHTML = `
      <div class="profile-change-form__field">
        <label class="profile-change-form__label">Текущий пароль</label>
        <input class="profile-change-form__input" type="password" name="currentPassword" placeholder="Введите пароль" required>
      </div>
      <div class="profile-change-form__field">
        <label class="profile-change-form__label">Новый юзернейм</label>
        <input class="profile-change-form__input" type="text" name="newValue" placeholder="Новый юзернейм" required>
      </div>
      <p class="auth-form__error" data-form-error></p>
      <div class="profile-change-form__actions">
        <button class="profile-change-form__save" data-form-save>Сохранить</button>
        <button class="profile-change-form__cancel" data-form-cancel>Отмена</button>
      </div>
    `;
  } else {
    formContainer.innerHTML = `
      <div class="profile-change-form__field">
        <label class="profile-change-form__label">Текущий пароль</label>
        <input class="profile-change-form__input" type="password" name="currentPassword" placeholder="Введите текущий пароль" required>
      </div>
      <div class="profile-change-form__field">
        <label class="profile-change-form__label">Новый пароль</label>
        <input class="profile-change-form__input" type="password" name="newValue" placeholder="Новый пароль (мин. 4 символа)" required>
      </div>
      <p class="auth-form__error" data-form-error></p>
      <div class="profile-change-form__actions">
        <button class="profile-change-form__save" data-form-save>Сохранить</button>
        <button class="profile-change-form__cancel" data-form-cancel>Отмена</button>
      </div>
    `;
  }

  formContainer.style.display = 'flex';

  formContainer.querySelector('[data-form-cancel]').addEventListener('click', () => {
    formContainer.style.display = 'none';
    formContainer.innerHTML = '';
  });

  formContainer.querySelector('[data-form-save]').addEventListener('click', () => {
    handleProfileChange(type, formContainer);
  });
}

async function handleProfileChange(type, formContainer) {
  const errorEl = formContainer.querySelector('[data-form-error]');
  errorEl.classList.remove('auth-form__error--visible');

  const user = getCurrentUser();
  if (!user) return;

  const currentPassword = formContainer.querySelector('[name="currentPassword"]').value.trim();
  const newValue = formContainer.querySelector('[name="newValue"]').value.trim();

  if (!currentPassword) {
    errorEl.textContent = 'Введите текущий пароль';
    errorEl.classList.add('auth-form__error--visible');
    return;
  }
  if (!newValue) {
    errorEl.textContent = 'Заполните поле';
    errorEl.classList.add('auth-form__error--visible');
    return;
  }

  // Пробуем API
  try {
    const body = { currentPassword };
    if (type === 'username') body.newUsername = newValue;
    else body.newPassword = newValue;

    const data = await fetchApi('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(body),
    });

    if (data.success && data.user) {
      applyUser(data.user);
      formContainer.style.display = 'none';
      formContainer.innerHTML = '';
      renderProfile();
      return;
    }
  } catch {
    // fallback — локально
  }

  // Локальный fallback
  const users = getLocalUsers();
  const stored = users[user.username];
  if (!stored || stored.password !== currentPassword) {
    errorEl.textContent = 'Неверный текущий пароль';
    errorEl.classList.add('auth-form__error--visible');
    return;
  }

  if (type === 'username') {
    if (users[newValue]) {
      errorEl.textContent = 'Такой юзернейм уже занят';
      errorEl.classList.add('auth-form__error--visible');
      return;
    }
    users[newValue] = { ...users[user.username] };
    delete users[user.username];
    saveLocalUsers(users);
    applyUser({ ...user, username: newValue });
  } else {
    if (newValue.length < 4) {
      errorEl.textContent = 'Пароль должен быть минимум 4 символа';
      errorEl.classList.add('auth-form__error--visible');
      return;
    }
    users[user.username].password = newValue;
    saveLocalUsers(users);
  }

  formContainer.style.display = 'none';
  formContainer.innerHTML = '';
  renderProfile();
}

function getLocalUsers() {
  try {
    return JSON.parse(localStorage.getItem('flappy_logan_users') || '{}');
  } catch {
    return {};
  }
}

function saveLocalUsers(users) {
  localStorage.setItem('flappy_logan_users', JSON.stringify(users));
}

/* ================ Inventory ================ */

export async function openInventory() {
  const user = getCurrentUser();
  if (!user) return;

  if (!inventoryOverlay) {
    inventoryOverlay = buildOverlay('inventory-overlay', 'Инвентарь', true);
  }

  await renderInventory();
  openModal(inventoryOverlay);
}

async function renderInventory() {
  const content = inventoryOverlay.querySelector('.auth-modal__content');
  const user = getCurrentUser();
  if (!user) return;

  await loadActiveSkins();
  const userSkins = user.skins || [];
  const ALL_SKINS = await getAllSkins();
  const skinMap = {};
  ALL_SKINS.forEach((s) => { skinMap[s.id] = s; });

  // Группируем купленные скины по категориям (без дубликатов)
  const grouped = { birds: [], pipes: [], backgrounds: [] };
  const seen = new Set();
  userSkins.forEach((skinId) => {
    if (seen.has(skinId)) return;
    seen.add(skinId);
    const meta = skinMap[skinId];
    if (meta && grouped[meta.category]) {
      grouped[meta.category].push(meta);
    }
  });

  let html = '<div class="inv-content">';
  let hasAny = false;

  Object.keys(grouped).forEach((cat) => {
    const items = grouped[cat];
    const meta = CATEGORY_META[cat];
    const activeId = activeSkins[cat] || 'bird-default';
    const activeName = skinMap[activeId]?.name || '—';

    html += `
      <div class="inv-section">
        <div class="inv-section__header">
          <svg class="inv-section__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="${meta.icon}"/>
          </svg>
          <span class="inv-section__title">${meta.label}</span>
          <span class="inv-section__active">Активен: ${escapeHtml(activeName)}</span>
        </div>
    `;

    if (items.length === 0) {
      html += `<div class="inv-empty-msg">Нет купленных скинов</div>`;
    } else {
      html += '<div class="inv-slider">';
      items.forEach((skin) => {
        const isActive = activeSkins[cat] === skin.id;
        const skinImage = getSkinImage(skin);
        const isPipe = skin.image && typeof skin.image === 'object' && skin.image.bottom;
        const imgClass = isPipe ? 'inv-slide__image--pipe' : '';
        html += `
          <div class="inv-slide ${isActive ? 'inv-slide--active' : ''}" data-skin-id="${skin.id}" data-category="${cat}">
            <div class="inv-slide__image">
              <img src="${skinImage}" alt="${skin.name}" loading="lazy" class="${imgClass}">
            </div>
            <span class="inv-slide__name">${skin.name}</span>
            <span class="inv-slide__badge ${isActive ? 'inv-slide__badge--active' : 'inv-slide__badge--inactive'}">
              ${isActive ? '✓ Активен' : 'Надеть'}
            </span>
          </div>
        `;
      });
      html += '</div>';
    }

    html += '</div>';
    hasAny = true;
  });

  if (!hasAny) {
    html += `<div class="inv-empty-msg">У вас пока нет купленных скинов. Зайдите в магазин!</div>`;
  }

  html += '</div>';
  content.innerHTML = html;

  // Обработчики
  content.querySelectorAll('.inv-slide:not(.inv-slide--active)').forEach((slide) => {
    slide.addEventListener('click', () => {
      const skinId = slide.dataset.skinId;
      const category = slide.dataset.category;
      equipSkin(skinId, category);
    });
  });
}

async function loadActiveSkins() {
  // Сначала пробуем загрузить с бэкенда
  try {
    const data = await fetchApi('/shop/equipped');
    if (data && data.success && data.equipped) {
      activeSkins = { ...data.equipped };
      // Сохраняем в localStorage для fallback
      localStorage.setItem('flappy_logan_active_skins', JSON.stringify(activeSkins));
      return;
    }
  } catch {
    // fallback — localStorage
  }

  // Fallback на localStorage
  try {
    const raw = localStorage.getItem('flappy_logan_active_skins');
    if (raw) {
      activeSkins = JSON.parse(raw);
    } else {
      activeSkins = { birds: 'bird-default', pipes: 'pipe-default', backgrounds: 'bg-default' };
    }
  } catch {
    activeSkins = { birds: 'bird-default', pipes: 'pipe-default', backgrounds: 'bg-default' };
  }
}

async function equipSkin(skinId, category) {
  activeSkins[category] = skinId;
  localStorage.setItem('flappy_logan_active_skins', JSON.stringify(activeSkins));

  fetchApi('/shop/equip', {
    method: 'POST',
    body: JSON.stringify({ skinId, category }),
  }).catch(() => {});

  await renderInventory();
}

/* ================ Helpers ================ */

async function getAllSkins() {
  // Используем кеш, если уже загрузили
  if (catalogSkinsCache) return catalogSkinsCache;

  try {
    const data = await fetchApi('/shop/skins');
    if (data && data.success && Array.isArray(data.skins)) {
      catalogSkinsCache = data.skins;
      return catalogSkinsCache;
    }
  } catch {
    // fallback — используем стандартные скины
  }

  // Fallback — жёстко зашитый базовый набор
  const fallback = [
    { id: 'bird-default', name: 'Обычная птица', category: 'birds', price: 0, image: null },
    { id: 'pipe-default', name: 'Классическая труба', category: 'pipes', price: 0, image: null },
    { id: 'bg-default', name: 'Стандартный фон', category: 'backgrounds', price: 0, image: null },
  ];
  catalogSkinsCache = fallback;
  return fallback;
}

/**
 * Возвращает URL изображения для скина.
 * Для труб (объект с top/bottom) показывает только нижнюю часть.
 */
function getSkinImage(skin) {
  if (!skin.image) return getPlaceholderImage(skin);
  if (typeof skin.image === 'object' && skin.image.bottom) return skin.image.bottom;
  if (typeof skin.image === 'string') return skin.image;
  return getPlaceholderImage(skin);
}

function getPlaceholderImage(skin) {
  const colors = { birds: '#0fcf8a', pipes: '#e8a838', backgrounds: '#6c5ce7' };
  const color = colors[skin.category] || '#555';
  const letter = skin.name.charAt(0);
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='150' viewBox='0 0 200 150'%3E%3Crect width='200' height='150' fill='%23050d0a'/%3E%3Ccircle cx='100' cy='75' r='40' fill='${encodeURIComponent(color)}' opacity='0.2'/%3E%3Ctext x='100' y='85' text-anchor='middle' fill='${encodeURIComponent(color)}' font-size='40' font-weight='700' font-family='sans-serif'%3E${letter}%3C/text%3E%3C/svg%3E`;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function closeAllUserModals() {
  if (profileOverlay) closeModal(profileOverlay);
  if (inventoryOverlay) closeModal(inventoryOverlay);
}