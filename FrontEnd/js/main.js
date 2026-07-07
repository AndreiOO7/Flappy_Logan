import { initAuth, syncUser } from './auth.js';
import { initShop } from './shop.js';

/**
 * Мобильное меню — открытие/закрытие через бургер.
 */
function initMobileNav() {
  const burger = document.querySelector('.header__burger');
  const nav = document.querySelector('.nav');
  const overlay = document.querySelector('.nav-overlay');

  if (!burger || !nav || !overlay) return;

  function openNav() {
    nav.classList.add('nav--open');
    overlay.classList.add('nav-overlay--visible');
    burger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }

  function closeNav() {
    nav.classList.remove('nav--open');
    overlay.classList.remove('nav-overlay--visible');
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  burger.addEventListener('click', () => {
    if (nav.classList.contains('nav--open')) {
      closeNav();
    } else {
      openNav();
    }
  });

  overlay.addEventListener('click', closeNav);

  // Закрываем меню при нажатии Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('nav--open')) {
      closeNav();
    }
  });

  // Закрываем меню при переходе по ссылке (для SPA-like поведения)
  nav.querySelectorAll('.nav__link').forEach((link) => {
    link.addEventListener('click', closeNav);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  // Инициализация мобильной навигации
  initMobileNav();

  // Инициализация авторизации (модалки, состояние, хедер)
  initAuth();

  // Если мы на странице магазина — инициализируем его
  if (document.querySelector('.shop')) {
    initShop().catch((err) => console.error('Shop init error:', err));
  }
});

/**
 * Периодическая синхронизация с бэкендом.
 * Обновляет баланс, скины и другие данные раз в 30 секунд,
 * а также при возвращении на вкладку (visibilitychange).
 */

// Запускаем синхронизацию сразу после загрузки всех модулей
setTimeout(() => {
  syncUser();
}, 1000);

// Периодическая синхронизация каждые 30 секунд
setInterval(() => {
  syncUser();
}, 30000);

// Синхронизация при возвращении на вкладку (пользователь переключился и вернулся)
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    syncUser();
  }
});