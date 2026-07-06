/**
 * API module — обёртка для fetch с автоподстановкой токена.
 * Токен сохраняется в localStorage и автоматически добавляется ко всем запросам.
 */

const API_BASE = 'https://flappylogan-production.up.railway.app/api';
const TOKEN_KEY = 'flappy_logan_token';

/**
 * Сохраняет JWT-токен в localStorage.
 */
export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

/**
 * Возвращает сохранённый токен или null.
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Удаляет токен (при логауте).
 */
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Универсальный запрос к API.
 * Автоматически подставляет Content-Type и Authorization (если токен есть).
 *
 * @param {string} endpoint — путь типа "/auth/login"
 * @param {object} options — опции fetch (method, body, headers и т.д.)
 */
export async function fetchApi(endpoint, options = {}) {
  const token = getToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers,
    ...options,
  });

  // Если сервер вернул 401 — токен протух/невалиден — чистим
  if (response.status === 401) {
    clearToken();
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message =
      errorBody?.error?.message || `API error: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}