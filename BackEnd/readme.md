# Flappy Logan — Backend API Specification

## Stack (на усмотрение бэкендера)
- Рекомендуется: Node.js (Express) + PostgreSQL / SQLite
- Либо Python (FastAPI / Django) + PostgreSQL

---

## 1. Аутентификация

### POST /api/auth/register
Регистрация нового пользователя.

**Request body:**
```json
{
  "username": "string (3-20 символов, только латиница/цифры/underscore)",
  "password": "string (минимум 4 символа)"
}
```

**Response 201:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "username": "string",
    "balance": 1000,
    "skins": ["bird-default", "pipe-default", "bg-default"],
    "createdAt": "ISO8601"
  }
}
```

**Errors:**
- 409 — username already exists
- 400 — validation error

### POST /api/auth/login
**Request body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "success": true,
  "token": "jwt-token",
  "user": {
    "id": "uuid",
    "username": "string",
    "balance": 1000,
    "skins": ["bird-default", "pipe-default", "bg-default"]
  }
}
```

**Errors:**
- 401 — invalid credentials

### GET /api/auth/me
Проверка токена, получение данных пользователя.

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "username": "string",
    "balance": 1000,
    "skins": ["bird-default", "pipe-default", "bg-default"]
  }
}
```

---

## 2. Магазин / Скины

### GET /api/shop/skins
Получить все доступные скины.

**Response 200:**
```json
{
  "success": true,
  "skins": [
    {
      "id": "bird-red",
      "name": "Красный кардинал",
      "category": "birds",
      "price": 200,
      "image": "url-or-null"
    }
  ]
}
```

Categories: `birds`, `pipes`, `backgrounds`

### GET /api/shop/user-skins
Получить ID скинов, которые принадлежат текущему пользователю.

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "success": true,
  "skins": ["bird-default", "bird-red", "pipe-neon"]
}
```

### POST /api/shop/buy
Купить скин.

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "skinId": "bird-red"
}
```

**Response 200:**
```json
{
  "success": true,
  "balance": 800,
  "skinId": "bird-red"
}
```

**Errors:**
- 400 — skin not found
- 400 — skin already owned
- 402 — insufficient funds

---

## 3. Таблица лидеров

### GET /api/leaderboard
Получить топ игроков.

**Query params:** `?limit=50&offset=0`

**Response 200:**
```json
{
  "success": true,
  "players": [
    {
      "rank": 1,
      "username": "Champion",
      "score": 4200,
      "gamesPlayed": 150
    }
  ],
  "total": 100
}
```

### POST /api/game/result
Отправить результат игры (для пополнения баланса).

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "score": 42,
  "gamesPlayed": 1
}
```

**Response 200:**
```json
{
  "success": true,
  "balanceAwarded": 42,
  "newBalance": 1042
}
```

> **Примечание:** Баланс начисляется 1:1 к очкам за каждую сыгранную игру.

---

## 4. Профиль

### PUT /api/auth/profile
Смена юзернейма и/или пароля.

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "currentPassword": "string (обязательно)",
  "newUsername": "string (опционально, 3-20 символов)",
  "newPassword": "string (опционально, минимум 4 символа)"
}
```

**Response 200:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "username": "string",
    "balance": 1000,
    "skins": ["bird-default", "pipe-default", "bg-default"]
  }
}
```

**Errors:**
- 400 — validation error
- 401 — wrong current password
- 409 — new username already taken

---

## 5. Инвентарь / Снаряжение

### GET /api/shop/equipped
Получить список активных (надетых) скинов.

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "success": true,
  "equipped": {
    "birds": "bird-red",
    "pipes": "pipe-neon",
    "backgrounds": "bg-space"
  }
}
```

### POST /api/shop/equip
Надеть скин в определённую категорию.

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "skinId": "bird-red",
  "category": "birds"
}
```

**Response 200:**
```json
{
  "success": true,
  "equipped": {
    "birds": "bird-red",
    "pipes": "pipe-default",
    "backgrounds": "bg-default"
  }
}
```

**Errors:**
- 400 — skin not owned
- 400 — invalid category
- 400 — invalid skinId

---

## 6. Мок-данные (для разработки без БД)

Фронтенд использует локальный fallback (localStorage), если API не отвечает.  
Для полноценной работы достаточно реализовать описанные выше эндпоинты.

### Структура БД (рекомендуемая)

**Таблица `users`:**
| Колонка     | Тип        | Описание                      |
|-------------|------------|-------------------------------|
| id          | UUID (PK)  |                               |
| username    | VARCHAR(20)| unique, только латиница        |
| password    | VARCHAR    | bcrypt hash                   |
| balance     | INTEGER    | default 1000                  |
| created_at  | TIMESTAMP  |                               |

**Таблица `user_skins`:**
| Колонка  | Тип        | Описание                |
|----------|------------|-------------------------|
| id       | UUID (PK)  |                         |
| user_id  | UUID (FK)  | references users(id)    |
| skin_id  | VARCHAR    | например "bird-red"     |
| UNIQUE   | (user_id, skin_id) |                  |

**Таблица `skins` (опционально, можно хранить на фронте):**
| Колонка   | Тип        |
|-----------|------------|
| id        | VARCHAR(PK)|
| name      | VARCHAR     |
| category  | VARCHAR     |
| price     | INTEGER     |
| image_url | VARCHAR     |

**Таблица `game_results`:**
| Колонка      | Тип        |
|--------------|------------|
| id           | UUID (PK)  |
| user_id      | UUID (FK)  |
| score        | INTEGER    |
| played_at    | TIMESTAMP  |

> Для лидерборда: `SELECT username, SUM(score) as score, COUNT(*) as gamesPlayed FROM game_results JOIN users ON users.id = game_results.user_id GROUP BY users.id ORDER BY score DESC LIMIT ?`

---

## 7. JWT / Токены

- Использовать JWT с exp (например 7 дней)
- В payload: `{ userId: uuid, username: string }`
- Алгоритм: HS256
- Секрет: через env-переменную `JWT_SECRET`

---

## 8. Обработка ошибок (единый формат)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Username must be 3-20 characters"
  }
}
```

HTTP статусы:
- 400 — Bad Request (validation)
- 401 — Unauthorized
- 402 — Payment Required (insufficient funds)
- 404 — Not Found
- 409 — Conflict (already exists)
- 500 — Internal Server Error