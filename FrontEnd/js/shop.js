/**
 * Shop module — магазин скинов с тумблером категорий.
 *
 * Работает с мок-данными, но готов к подключению реального API.
 * Проверяет авторизацию через auth-модуль.
 */

import { fetchApi } from './api.js';
import { isAuthenticated, getCurrentUser, openLogin, applyUser } from './auth.js';

/* ================ Mock data ================ */

const MOCK_SKINS = {
  birds: [
    { id: 'bird-default', name: 'Классическая', category: 'birds', price: 0, image: null, owned: true },
    { id: 'bird-red', name: 'Красный кардинал', category: 'birds', price: 200, image: null },
    { id: 'bird-blue', name: 'Голубая сойка', category: 'birds', price: 350, image: null },
    { id: 'bird-gold', name: 'Золотой орёл', category: 'birds', price: 500, image: null },
    { id: 'bird-phoenix', name: 'Феникс', category: 'birds', price: 800, image: null },
    { id: 'bird-owl', name: 'Сова', category: 'birds', price: 300, image: null },
    { id: 'bird-penguin', name: 'Пингвин', category: 'birds', price: 450, image: null },
    { id: 'bird-parrot', name: 'Попугай', category: 'birds', price: 600, image: null },
  ],
  pipes: [
    { id: 'pipe-default', name: 'Классические', category: 'pipes', price: 0, image: null, owned: true },
    { id: 'pipe-dark', name: 'Тёмный металл', category: 'pipes', price: 250, image: null },
    { id: 'pipe-neon', name: 'Неон', category: 'pipes', price: 400, image: null },
    { id: 'pipe-wood', name: 'Деревянные', category: 'pipes', price: 300, image: null },
    { id: 'pipe-ice', name: 'Ледяные', category: 'pipes', price: 550, image: null },
    { id: 'pipe-lava', name: 'Лава', category: 'pipes', price: 700, image: null },
  ],
  backgrounds: [
    { id: 'bg-default', name: 'Стандартный', category: 'backgrounds', price: 0, image: null, owned: true },
    { id: 'bg-sunset', name: 'Закат', category: 'backgrounds', price: 300, image: null },
    { id: 'bg-night', name: 'Ночь', category: 'backgrounds', price: 400, image: null },
    { id: 'bg-space', name: 'Космос', category: 'backgrounds', price: 600, image: null },
    { id: 'bg-underwater', name: 'Подводный', category: 'backgrounds', price: 500, image: null },
    { id: 'bg-retro', name: 'Ретро', category: 'backgrounds', price: 350, image: null },
  ],
};

const CATEGORIES = [
  { key: 'birds', label: 'Скины птиц' },
  { key: 'pipes', label: 'Скины труб' },
  { key: 'backgrounds', label: 'Скины фона' },
];

/* ================ State ================ */

let currentCategory = 'birds';
let userSkins = [];

/* ================ DOM refs ================ */

let containerEl = null;
let gridEl = null;
let tabsEl = null;

/* ================ Init ================ */

export function initShop(containerSelector = '.shop') {
  containerEl = document.querySelector(containerSelector);
  if (!containerEl) {
    console.warn('Shop container not found');
    return;
  }

  renderTabs();
  renderGrid();

  // Слушаем изменения авторизации
  window.addEventListener('auth:change', () => {
    loadUserSkins();
    renderGrid();
  });

  // Загружаем скины пользователя
  loadUserSkins();
}

/* ================ User skins ================ */

function loadUserSkins() {
  userSkins = [];

  if (!isAuthenticated()) return;

  const user = getCurrentUser();
  if (user && Array.isArray(user.skins)) {
    userSkins = user.skins;
  }

  // Пробуем загрузить с бэка
  fetchApi('/shop/user-skins')
    .then((data) => {
      if (data && Array.isArray(data.skins)) {
        userSkins = data.skins;
      }
    })
    .catch(() => {
      // fallback — локальные данные
      try {
        const raw = localStorage.getItem('flappy_logan_users');
        if (raw) {
          const users = JSON.parse(raw);
          const username = getCurrentUser()?.username;
          if (username && users[username]?.skins) {
            userSkins = users[username].skins;
          }
        }
      } catch {
        // ignore
      }
    });
}

function isSkinOwned(skinId) {
  return userSkins.includes(skinId);
}

/* ================ Tabs ================ */

function renderTabs() {
  tabsEl = document.createElement('div');
  tabsEl.className = 'shop-tabs';

  CATEGORIES.forEach((cat) => {
    const btn = document.createElement('button');
    btn.className = `shop-tabs__btn${cat.key === currentCategory ? ' shop-tabs__btn--active' : ''}`;
    btn.textContent = cat.label;
    btn.dataset.category = cat.key;
    btn.addEventListener('click', () => switchCategory(cat.key));
    tabsEl.appendChild(btn);
  });

  containerEl.appendChild(tabsEl);
}

function switchCategory(key) {
  currentCategory = key;

  tabsEl.querySelectorAll('.shop-tabs__btn').forEach((btn) => {
    btn.classList.toggle('shop-tabs__btn--active', btn.dataset.category === key);
  });

  renderGrid();
}

/* ================ Grid ================ */

function renderGrid() {
  const oldGrid = containerEl.querySelector('.shop-grid');
  if (oldGrid) oldGrid.remove();

  gridEl = document.createElement('div');
  gridEl.className = 'shop-grid';

  const skins = MOCK_SKINS[currentCategory] || [];

  if (skins.length === 0) {
    gridEl.innerHTML = `
      <div class="shop-empty">
        <svg class="shop-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M16 16s-1.5-2-4-2-4 2-4 2"/>
          <line x1="9" y1="9" x2="9.01" y2="9"/>
          <line x1="15" y1="9" x2="15.01" y2="9"/>
        </svg>
        <p class="shop-empty__text">В этой категории пока нет скинов</p>
      </div>
    `;
  } else {
    skins.forEach((skin) => {
      const card = createCard(skin);
      gridEl.appendChild(card);
    });
  }

  containerEl.appendChild(gridEl);
}

/* ================ Card ================ */

function createCard(skin) {
  const card = document.createElement('div');
  card.className = 'shop-card';

  // Image
  const imageWrap = document.createElement('div');
  imageWrap.className = 'shop-card__image-wrap';

  const img = document.createElement('img');
  img.className = 'shop-card__image';
  img.src = skin.image || getPlaceholderImage(skin);
  img.alt = skin.name;
  img.loading = 'lazy';
  imageWrap.appendChild(img);

  // Body
  const body = document.createElement('div');
  body.className = 'shop-card__body';

  const name = document.createElement('h3');
  name.className = 'shop-card__name';
  name.textContent = skin.name;
  body.appendChild(name);

  // Price
  const price = document.createElement('div');
  price.className = 'shop-card__price';
  price.innerHTML = `
    <svg class="shop-card__price-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 6v12M8 10h6a2 2 0 1 0 0-4H8v8h6a2 2 0 0 0 2-2"/>
    </svg>
    <span>${skin.price}</span>
  `;
  body.appendChild(price);

  // Actions
  const actions = document.createElement('div');
  actions.className = 'shop-card__actions';

  const buyBtn = document.createElement('button');
  buyBtn.className = 'shop-card__buy';

  if (skin.owned || isSkinOwned(skin.id)) {
    buyBtn.className += ' shop-card__buy--owned';
    buyBtn.textContent = '✓ Куплено';
    buyBtn.disabled = true;
  } else if (!isAuthenticated()) {
    buyBtn.className += ' shop-card__buy--disabled';
    buyBtn.textContent = 'Авторизуйтесь для покупки';
    buyBtn.addEventListener('click', (e) => {
      e.preventDefault();
      openLogin();
    });
  } else {
    buyBtn.textContent = 'Купить';
    buyBtn.addEventListener('click', () => handleBuy(skin, buyBtn));
  }

  actions.appendChild(buyBtn);
  body.appendChild(actions);

  card.appendChild(imageWrap);
  card.appendChild(body);

  return card;
}

/* ================ Placeholder ================ */

function getPlaceholderImage(skin) {
  const colors = {
    birds: '#0fcf8a',
    pipes: '#e8a838',
    backgrounds: '#6c5ce7',
  };
  const color = colors[skin.category] || '#555';
  const letter = skin.name.charAt(0);

  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='150' viewBox='0 0 200 150'%3E%3Crect width='200' height='150' fill='%23050d0a'/%3E%3Ccircle cx='100' cy='75' r='40' fill='${encodeURIComponent(color)}' opacity='0.2'/%3E%3Ctext x='100' y='85' text-anchor='middle' fill='${encodeURIComponent(color)}' font-size='40' font-weight='700' font-family='sans-serif'%3E${letter}%3C/text%3E%3C/svg%3E`;
}

/* ================ Buy handler ================ */

async function handleBuy(skin, btn) {
  btn.textContent = '...';
  btn.disabled = true;

  const user = getCurrentUser();
  if (!user) {
    openLogin();
    return;
  }

  if (user.balance < skin.price) {
    btn.textContent = 'Недостаточно средств';
    btn.className = 'shop-card__buy shop-card__buy--disabled';
    setTimeout(() => {
      btn.textContent = 'Купить';
      btn.className = 'shop-card__buy';
      btn.disabled = false;
    }, 2000);
    return;
  }

  try {
    // Пробуем API
    const data = await fetchApi('/shop/buy', {
      method: 'POST',
      body: JSON.stringify({ skinId: skin.id }),
    });

    if (data.success) {
      onPurchaseSuccess(skin, data);
    }
  } catch {
    // Локальный fallback
    handleLocalPurchase(skin, btn);
  }
}

function handleLocalPurchase(skin, btn) {
  const user = getCurrentUser();
  if (!user) return;

  const newBalance = user.balance - skin.price;
  if (newBalance < 0) {
    btn.textContent = 'Недостаточно средств';
    btn.className = 'shop-card__buy shop-card__buy--disabled';
    setTimeout(() => {
      btn.textContent = 'Купить';
      btn.className = 'shop-card__buy';
      btn.disabled = false;
    }, 2000);
    return;
  }

  // Обновляем локальное хранилище пользователей
  try {
    const raw = localStorage.getItem('flappy_logan_users');
    if (raw) {
      const users = JSON.parse(raw);
      if (users[user.username]) {
        users[user.username].balance = newBalance;
        if (!users[user.username].skins) users[user.username].skins = [];
        users[user.username].skins.push(skin.id);
        localStorage.setItem('flappy_logan_users', JSON.stringify(users));
      }
    }
  } catch {
    // ignore
  }

  // Обновляем текущего пользователя
  applyUser({
    ...user,
    balance: newBalance,
    skins: [...(user.skins || []), skin.id],
  });

  onPurchaseSuccess(skin, { balance: newBalance });
}

function onPurchaseSuccess(skin, data) {
  // Обновляем UI пользователя
  const user = getCurrentUser();
  if (user) {
    applyUser({
      ...user,
      balance: data.balance ?? user.balance,
      skins: [...(user.skins || []), skin.id],
    });
  }

  // Обновляем кнопку в карточке
  const allBuyBtns = containerEl.querySelectorAll('.shop-card__buy');
  allBuyBtns.forEach((btn) => {
    const card = btn.closest('.shop-card');
    if (!card) return;
    const nameEl = card.querySelector('.shop-card__name');
    if (nameEl && nameEl.textContent === skin.name) {
      btn.className = 'shop-card__buy shop-card__buy--owned';
      btn.textContent = '✓ Куплено';
      btn.disabled = true;
    }
  });
}