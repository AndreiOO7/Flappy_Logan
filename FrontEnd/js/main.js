import { initAuth, syncUser } from './auth.js';
import { initShop } from './shop.js';

document.addEventListener('DOMContentLoaded', () => {
  // Инициализация авторизации (модалки, состояние, хедер)
  initAuth();

  // Если мы на странице магазина — инициализируем его
  if (document.querySelector('.shop')) {
    initShop();
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