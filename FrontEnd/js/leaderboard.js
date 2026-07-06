import { fetchApi } from './api.js';

/**
 * Загружает данные таблицы лидеров с бэкенда.
 * Если API недоступен, использует статические демо-данные.
 */
async function fetchLeaderboard() {
  try {
    console.log('[Leaderboard] Подключаюсь к API...');
    const data = await fetchApi('/leaderboard');
    console.log('[Leaderboard] Данные от API:', data);
    // API возвращает { success, players, total } — достаём players
    if (data.players && Array.isArray(data.players)) {
      return data.players;
    }
    return data;
  } catch (error) {
    console.warn('API недоступен, использую демо-данные:', error.message);
    return getDemoData();
  }
}

/**
 * Демо-данные для разработки, пока нет бэкенда.
 */
function getDemoData() {
  return [
    { rank: 1, name: 'Champion', score: 4200, games: 156 },
    { rank: 2, name: 'PlayerTwo', score: 2850, games: 112 },
    { rank: 3, name: 'PlayerThree', score: 1980, games: 87 },
    { rank: 4, name: 'SpeedRunner', score: 1750, games: 89 },
    { rank: 5, name: 'FlappyFan', score: 1320, games: 64 },
    { rank: 6, name: 'LoganDriver', score: 1100, games: 52 },
    { rank: 7, name: 'BirdMaster', score: 980, games: 41 },
    { rank: 8, name: 'PixelPro', score: 760, games: 33 },
    { rank: 9, name: 'GameOver', score: 540, games: 27 },
    { rank: 10, name: 'Rookie', score: 320, games: 15 },
  ];
}

/**
 * Рендерит весь лидерборд (подиум + таблицу) на основе данных.
 */
function renderLeaderboard(players) {
  if (!players || players.length === 0) return;

  const top3 = players.slice(0, 3);
  const rest = players.slice(3);

  renderPodium(top3);
  renderTable(rest);
}

/**
 * Рендерит подиум топ-3.
 */
function renderPodium(top3) {
  const podiumContainer = document.querySelector('.podium');
  if (!podiumContainer) return;

  // Упорядочиваем для отображения: 2-е место, 1-е место, 3-е место
  const ordered = [
    top3.find(p => p.rank === 2),
    top3.find(p => p.rank === 1),
    top3.find(p => p.rank === 3),
  ];

  podiumContainer.innerHTML = ordered
    .filter(Boolean)
    .map(player => {
      const medalClass =
        player.rank === 1 ? 'gold' :
        player.rank === 2 ? 'silver' : 'bronze';

      const crownHtml =
        player.rank === 1
          ? `<div class="podium__crown">
               <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                 <path d="M2 19h20l-2-10-6 4-4-4-6 4-2 10Z"/>
               </svg>
             </div>`
          : '';

      return `
        <div class="podium__item podium__item--${medalClass}">
          ${crownHtml}
          <div class="podium__rank">${player.rank}</div>
          <div class="podium__avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
              <circle cx="12" cy="8" r="4"/>
              <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
            </svg>
          </div>
          <div class="podium__name">${player.name}</div>
          <div class="podium__score">${player.score.toLocaleString('ru-RU')}</div>
          <div class="podium__medal podium__medal--${medalClass}">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2" stroke="#fff" stroke-width="2" fill="none"/>
            </svg>
          </div>
        </div>
      `;
    })
    .join('');
}

/**
 * Рендерит таблицу с 4+ местами.
 */
function renderTable(players) {
  const tableContainer = document.querySelector('.leaderboard__table');
  if (!tableContainer) return;

  // Сохраняем заголовок
  const headerHtml = tableContainer.querySelector('.leaderboard__row--header');
  const header = headerHtml ? headerHtml.outerHTML : '';

  const rowsHtml = players
    .map(
      player => `
        <div class="leaderboard__row">
          <span class="leaderboard__cell leaderboard__cell--rank">${player.rank}</span>
          <span class="leaderboard__cell leaderboard__cell--player">
            <span class="leaderboard__avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <circle cx="12" cy="8" r="4"/>
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
              </svg>
            </span>
            ${player.name}
          </span>
          <span class="leaderboard__cell leaderboard__cell--score">${player.score.toLocaleString('ru-RU')}</span>
          <span class="leaderboard__cell leaderboard__cell--games">${player.games}</span>
        </div>
      `
    )
    .join('');

  tableContainer.innerHTML = header + rowsHtml;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
  const data = await fetchLeaderboard();
  renderLeaderboard(data);
});