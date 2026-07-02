import { initAuth } from './auth.js';
import { initShop } from './shop.js';

document.addEventListener('DOMContentLoaded', () => {
  // Инициализация авторизации (модалки, состояние, хедер)
  initAuth();

  // Если мы на странице магазина — инициализируем его
  if (document.querySelector('.shop')) {
    initShop();
  }
});