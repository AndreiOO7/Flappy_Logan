/**
 * Auth module — управление модалками входа/регистрации, состоянием пользователя.
 *
 * Хранит состояние в localStorage и вешает data-атрибут `data-user` на <body>.
 * Экспортирует функции для использования в других модулях и инициализации.
 */

import { fetchApi, setToken, clearToken } from './api.js';
import { openProfile, openInventory } from './profile.js';

const STORAGE_KEY = 'flappy_logan_user';

let currentUser = null;

/* ================ DOM helpers (строим модалки один раз) ================ */

let loginModalEl = null;
let registerModalEl = null;

function createOverlay(id) {
  const overlay = document.createElement('div');
  overlay.className = 'auth-overlay';
  overlay.id = id;
  overlay.innerHTML = `
    <div class="auth-modal">
      <button class="auth-modal__close" aria-label="Закрыть">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6 6 18M6 6l12 12"/>
        </svg>
      </button>
      <h2 class="auth-modal__title"></h2>
      <form class="auth-form">
        <div class="auth-form__field">
          <label class="auth-form__label">Юзернейм</label>
          <input class="auth-form__input" type="text" name="username" placeholder="Введите юзернейм" required autocomplete="username">
        </div>
        <div class="auth-form__field">
          <label class="auth-form__label">Пароль</label>
          <input class="auth-form__input" type="password" name="password" placeholder="Введите пароль" required autocomplete="current-password">
        </div>
        <p class="auth-form__error"></p>
        <button class="auth-form__submit" type="submit"></button>
        <p class="auth-form__switch">
          <span class="auth-form__switch-text"></span>
          <a class="auth-form__switch-link"></a>
        </p>
      </form>
    </div>
  `;
  document.body.appendChild(overlay);
  return overlay;
}

function buildModals() {
  if (loginModalEl) return;

  // Login modal
  loginModalEl = createOverlay('auth-login-overlay');
  loginModalEl.querySelector('.auth-modal__title').textContent = 'Вход';
  loginModalEl.querySelector('.auth-form__submit').textContent = 'Войти';
  loginModalEl.querySelector('.auth-form__switch-text').textContent = 'Нет аккаунта? ';
  const toRegisterLink = loginModalEl.querySelector('.auth-form__switch-link');
  toRegisterLink.textContent = 'Зарегистрироваться';
  toRegisterLink.dataset.action = 'switch-to-register';

  // Register modal
  registerModalEl = createOverlay('auth-register-overlay');
  registerModalEl.querySelector('.auth-modal__title').textContent = 'Регистрация';
  registerModalEl.querySelector('.auth-form__submit').textContent = 'Создать аккаунт';
  registerModalEl.querySelector('.auth-form__switch-text').textContent = 'Уже есть аккаунт? ';
  const toLoginLink = registerModalEl.querySelector('.auth-form__switch-link');
  toLoginLink.textContent = 'Войти';
  toLoginLink.dataset.action = 'switch-to-login';

  // Bind events
  bindModalEvents(loginModalEl);
  bindModalEvents(registerModalEl);
}

function bindModalEvents(overlay) {
  const closeBtn = overlay.querySelector('.auth-modal__close');
  const form = overlay.querySelector('.auth-form');
  const errorEl = form.querySelector('.auth-form__error');

  // Close on X
  closeBtn.addEventListener('click', () => closeModal(overlay));

  // Close on overlay click (click outside modal)
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal(overlay);
  });

  // Close on Escape
  const onKey = (e) => {
    if (e.key === 'Escape') {
      closeModal(overlay);
      document.removeEventListener('keydown', onKey);
    }
  };

  // Submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.classList.remove('auth-form__error--visible');

    const username = form.querySelector('[name="username"]').value.trim();
    const password = form.querySelector('[name="password"]').value.trim();

    if (!username || !password) {
      showError(overlay, 'Заполните все поля');
      return;
    }

    // Валидация полей
    const validationError = validateAuthFields(username, password, overlay.id === 'auth-register-overlay');
    if (validationError) {
      showError(overlay, validationError);
      return;
    }

    const isLogin = overlay.id === 'auth-login-overlay';

    try {
      // Сначала пробуем настоящий API
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const data = await fetchApi(endpoint, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });

      // Сохраняем токен, если он есть (логин)
      if (data.token) {
        setToken(data.token);
      }

      applyUser(data.user);
      closeModal(overlay);
    } catch (err) {
      // Если API не отвечает — используем локальный fallback
      console.warn('Auth API недоступен, использую локальный режим:', err.message);
      handleLocalAuth(isLogin, username, password, overlay);
    }
  });

  // Switch between login / register
  const switchLink = overlay.querySelector('.auth-form__switch-link');
  switchLink.addEventListener('click', () => {
    const action = switchLink.dataset.action;
    if (action === 'switch-to-register') {
      closeModal(overlay);
      openRegister();
    } else if (action === 'switch-to-login') {
      closeModal(overlay);
      openLogin();
    }
  });
}

function showError(overlay, msg) {
  const errorEl = overlay.querySelector('.auth-form__error');
  errorEl.textContent = msg;
  errorEl.classList.add('auth-form__error--visible');
}

/* ================ Local fallback (для офлайн-разработки) ================ */

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

function handleLocalAuth(isLogin, username, password, overlay) {
  const users = getLocalUsers();

  // Валидация полей (для локального режима)
  const validationError = validateAuthFields(username, password, !isLogin);
  if (validationError) {
    showError(overlay, validationError);
    return;
  }

  if (isLogin) {
    const stored = users[username];
    if (!stored || stored.password !== password) {
      showError(overlay, 'Неверный юзернейм или пароль');
      return;
    }
    // Добавляем стандартные скины, если их нет
    let skins = stored.skins || [];
    const defaultSkins = ['bird-default', 'pipe-default', 'bg-default'];
    defaultSkins.forEach((s) => { if (!skins.includes(s)) skins.push(s); });
    applyUser({ username, balance: stored.balance, skins, avatar: null });
  } else {
    if (users[username]) {
      showError(overlay, 'Пользователь уже существует');
      return;
    }
    const defaultSkins = ['bird-default', 'pipe-default', 'bg-default'];
    const newUser = { password, balance: 1000, skins: [...defaultSkins] };
    users[username] = newUser;
    saveLocalUsers(users);
    applyUser({ username, balance: 1000, skins: [...defaultSkins], avatar: null });
  }

  closeModal(overlay);
}

/* ================ Открытие / закрытие ================ */

export function openLogin() {
  buildModals();
  loginModalEl.classList.add('auth-overlay--open');
  // Clear fields
  loginModalEl.querySelector('form').reset();
  loginModalEl.querySelector('.auth-form__error').classList.remove('auth-form__error--visible');
}

export function openRegister() {
  buildModals();
  registerModalEl.classList.add('auth-overlay--open');
  registerModalEl.querySelector('form').reset();
  registerModalEl.querySelector('.auth-form__error').classList.remove('auth-form__error--visible');
}

function closeModal(overlay) {
  overlay.classList.remove('auth-overlay--open');
}

/* ================ Управление состоянием пользователя ================ */

export function getCurrentUser() {
  return currentUser ? { ...currentUser } : null;
}

export function isAuthenticated() {
  return currentUser !== null;
}

export function applyUser(user) {
  currentUser = user;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  updateUI();
  // Dispatch event для обновления других модулей
  window.dispatchEvent(new CustomEvent('auth:change', { detail: { user } }));
}

export function logout() {
  currentUser = null;
  localStorage.removeItem(STORAGE_KEY);
  clearToken();
  updateUI();
  window.dispatchEvent(new CustomEvent('auth:change', { detail: { user: null } }));
}

/**
 * Синхронизирует данные пользователя с бэкендом.
 * Вызывает /api/auth/me и обновляет локальное состояние.
 * Если бэкенд недоступен — оставляет текущие данные.
 */
export async function syncUser() {
  // Если нет токена — нечего синхронизировать
  if (!localStorage.getItem('flappy_logan_token')) {
    return;
  }

  try {
    const data = await fetchApi('/auth/me');
    if (data.success && data.user) {
      applyUser(data.user);
    }
  } catch (err) {
    // Бэкенд недоступен — оставляем локальные данные
    console.warn('syncUser: бэкенд недоступен, использую кэш:', err.message);
  }
}

/* ================ Обновление UI хедера ================ */

function updateUI() {
  const headerActions = document.querySelector('.header-actions');
  if (!headerActions) return;

  if (currentUser) {
    // Авторизован — показываем аватарку, юзернейм, баланс, дропдаун
    headerActions.innerHTML = `
      <div class="header-user">
        <div class="header-user__wrapper">
          <button class="header-user__dropdown-btn" data-dropdown-toggle>
            <div class="header-user__avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="8" r="4"/>
                <path d="M20 21a8 8 0 1 0-16 0"/>
              </svg>
            </div>
            <span class="header-user__name">${escapeHtml(currentUser.username)}</span>
            <svg class="header-user__dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          <div class="header-user__dropdown" data-dropdown-menu>
            <button class="header-user__dropdown-item" data-action="profile">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="8" r="4"/>
                <path d="M20 21a8 8 0 1 0-16 0"/>
              </svg>
              Профиль
            </button>
            <button class="header-user__dropdown-item" data-action="inventory">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
              Инвентарь
            </button>
            <div class="header-user__dropdown-divider"></div>
            <button class="header-user__dropdown-item" data-action="logout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              Выйти
            </button>
          </div>
        </div>
        <div class="header-user__balance">
          <svg class="header-user__balance-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v12M8 10h6a2 2 0 1 0 0-4H8v8h6a2 2 0 0 0 2-2"/>
          </svg>
          <span>${currentUser.balance ?? 0}</span>
        </div>
      </div>
    `;

    // Dropdown toggle
    const toggleBtn = headerActions.querySelector('[data-dropdown-toggle]');
    const dropdown = headerActions.querySelector('[data-dropdown-menu]');

    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = dropdown.classList.contains('header-user__dropdown--open');
      closeAllDropdowns();
      if (!isOpen) {
        dropdown.classList.add('header-user__dropdown--open');
        toggleBtn.classList.add('header-user__dropdown-btn--open');
      }
    });

    // Dropdown actions
    dropdown.querySelector('[data-action="profile"]').addEventListener('click', () => {
      closeAllDropdowns();
      openProfile();
    });
    dropdown.querySelector('[data-action="inventory"]').addEventListener('click', () => {
      closeAllDropdowns();
      openInventory();
    });
    dropdown.querySelector('[data-action="logout"]').addEventListener('click', () => {
      closeAllDropdowns();
      logout();
    });

    // Закрытие дропдауна по клику вне
    document.addEventListener('click', closeAllDropdowns, { once: false });
  } else {
    // Не авторизован
    headerActions.innerHTML = `
      <a href="#" class="header-actions__login js-open-login">Войти</a>
      <a href="#" class="header-actions__register js-open-register">Регистрация</a>
    `;
    headerActions.querySelector('.js-open-login').addEventListener('click', (e) => {
      e.preventDefault();
      openLogin();
    });
    headerActions.querySelector('.js-open-register').addEventListener('click', (e) => {
      e.preventDefault();
      openRegister();
    });
  }
}

function closeAllDropdowns() {
  document.querySelectorAll('[data-dropdown-menu]').forEach((m) => {
    m.classList.remove('header-user__dropdown--open');
  });
  document.querySelectorAll('[data-dropdown-toggle]').forEach((b) => {
    b.classList.remove('header-user__dropdown-btn--open');
  });
}

/**
 * Валидация полей регистрации/логина.
 * @param {string} username
 * @param {string} password
 * @param {boolean} isRegister - true для регистрации (строгая валидация), false для логина (только проверка пароля)
 * @returns {string|null} - сообщение об ошибке или null, если всё ок
 */
function validateAuthFields(username, password, isRegister) {
  const USERNAME_REGEX = /^[a-zA-Z0-9]+$/;

  if (isRegister) {
    // Валидация username только при регистрации
    if (username.length <= 3) {
      return 'Юзернейм должен быть длиннее 3 символов';
    }
    if (username.length >= 20) {
      return 'Юзернейм должен быть короче 20 символов';
    }
    if (!USERNAME_REGEX.test(username)) {
      return 'Юзернейм должен содержать только латиницу и цифры';
    }
  }

  // Валидация пароля (всегда)
  if (password.length < 4) {
    return 'Пароль должен быть не меньше 4 символов';
  }

  return null;
}

function escapeHtml(str) {
    const action = target.dataset.auth;
    if (action === 'login') openLogin();
    else if (action === 'register') openRegister();
  });
}