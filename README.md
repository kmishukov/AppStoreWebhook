# App Store Webhook Handler

Вебхук-обработчик для получения и обработки уведомлений от App Store Connect о событиях подписок.

## Возможности

- ✅ Валидация JWT токенов от Apple (с использованием x5c certificate chain)
- ✅ Обработка всех типов событий подписок:
  - `INITIAL_BUY` - первая покупка подписки
  - `DID_RENEW` - подписка продлена
  - `DID_FAIL_TO_RENEW` - не удалось продлить
  - `DID_CHANGE_RENEWAL_PREF` - изменены настройки продления
  - `DID_CHANGE_RENEWAL_STATUS` - изменен статус автопродления
  - `EXPIRED` - подписка истекла
  - `GRACE_PERIOD_EXPIRED` - истек льготный период
  - `REFUND` - возврат средств
  - `REVOKE` - подписка отозвана
  - `TEST` - тестовое уведомление
- ✅ Подробное логирование всех событий
- ✅ Обработка ошибок с правильными HTTP статусами
- ✅ Health check endpoint

## Структура проекта

```
AppStoreWebhook/
├── app/
│   ├── __init__.py
│   ├── main.py              # Основной FastAPI приложение
│   ├── jwt_validator.py     # Валидация JWT токенов от Apple
│   ├── models.py            # Модели данных
│   └── event_handlers.py    # Обработчики событий
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

## Установка и запуск

### 1. Клонирование и установка зависимостей

```bash
cd /Users/kmishukov/Development/AppStoreWebhook
pip install -r requirements.txt
```

### 2. Запуск через Docker Compose

```bash
docker-compose up -d
```

Сервис будет доступен на `http://localhost:8001`

### 3. Проверка работы

```bash
# Health check
curl http://localhost:8001/health

# Тестовый endpoint
curl http://localhost:8001/webhook/test
```

## Настройка в App Store Connect

1. Войдите в [App Store Connect](https://appstoreconnect.apple.com)
2. Перейдите в раздел вашего приложения
3. Найдите раздел **App Store Server Notifications**
4. Укажите URL вашего webhook: `https://appstore.kmishukov.me/webhook/appstore`
5. Сохраните настройки

### Тестирование webhook

Apple предоставляет возможность отправить тестовое уведомление:

1. В App Store Connect найдите раздел с настройками Server Notifications
2. Нажмите кнопку **"Send Test Notification"** или **"Test"**
3. Apple отправит тестовое уведомление типа `TEST` на ваш endpoint

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "ok": true,
  "service": "appstore-webhook"
}
```

### `POST /webhook/appstore`
Основной endpoint для приема уведомлений от Apple.

**Request Body:**
```json
{
  "signedPayload": "eyJhbGciOiJSUzI1NiIsIng1YyI6WyJ..."
}
```

**Response (success):**
```json
{
  "status": "success",
  "notification_type": "INITIAL_BUY",
  "message": "Notification processed successfully"
}
```

### `GET /webhook/test`
Тестовый endpoint для проверки доступности.

**Response:**
```json
{
  "status": "ok",
  "message": "Webhook endpoint is accessible",
  "endpoints": {
    "webhook": "/webhook/appstore",
    "health": "/health"
  },
  "supported_notification_types": ["INITIAL_BUY", "DID_RENEW", ...]
}
```

## Логирование

Все события логируются с уровнем INFO и выше. Логи включают:
- Входящие уведомления (без sensitive данных)
- Декодированные payload
- Типы уведомлений
- Ошибки валидации и обработки

## Разработка

### Добавление обработки нового типа события

1. Добавьте функцию-обработчик в `app/event_handlers.py`:
```python
def handle_new_event(payload: Dict[str, Any]) -> None:
    logger.info("Обработка нового события")
    # Ваша логика здесь
```

2. Добавьте обработчик в словарь `EVENT_HANDLERS`:
```python
EVENT_HANDLERS = {
    ...
    "NEW_EVENT": handle_new_event,
}
```

### Расширение функциональности

- **База данных**: Добавьте подключение к БД для сохранения информации о подписках
- **Уведомления**: Интегрируйте отправку уведомлений пользователям
- **Мониторинг**: Добавьте метрики и алерты
- **Retry логика**: Реализуйте обработку повторных попыток при ошибках

## Безопасность

- ✅ Все запросы должны приходить по HTTPS
- ✅ JWT токены валидируются с использованием публичных ключей Apple
- ✅ Проверяется подпись, expiration и issued at время
- ⚠️ В production рекомендуется добавить rate limiting
- ⚠️ Рекомендуется добавить проверку IP адресов Apple (whitelist)

## Troubleshooting

### Ошибка валидации JWT

Если получаете ошибку "Invalid or expired JWT token":
- Проверьте, что сертификат Apple не изменился
- Убедитесь, что время на сервере синхронизировано (NTP)
- Проверьте логи для детальной информации об ошибке

### Webhook не получает уведомления

1. Проверьте доступность endpoint: `curl https://appstore.kmishukov.me/webhook/appstore`
2. Убедитесь, что URL правильно настроен в App Store Connect
3. Проверьте логи Nginx и приложения
4. Используйте тестовое уведомление из App Store Connect

## Полезные ссылки

- [App Store Server Notifications Documentation](https://developer.apple.com/documentation/appstoreservernotifications)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

