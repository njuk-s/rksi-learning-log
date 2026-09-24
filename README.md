# Learning Log

[![tests](https://github.com/njuk-s/rksi-learning-log/actions/workflows/ci.yml/badge.svg)](https://github.com/njuk-s/rksi-learning-log/actions/workflows/ci.yml)

Личный учебный журнал: темы и записи о том, что вы изучили.

**Работающий сайт:** https://njuk-learning-log.onrender.com

Учебный проект на Django 5.2 LTS (РКСИ, курс «Python & Django»).

## Как проверить

На сайте уже есть демонстрационные данные и два пользователя, чтобы сразу проверить разграничение доступа:

| Логин | Пароль |
|---|---|
| `anna` | передан вместе со ссылкой на работу |
| `boris` | тот же |
| `review_admin` (админка `/admin/`) | передан вместе со ссылкой на работу |

Можно и зарегистрировать собственных пользователей. Войдите под `anna`, запомните адрес любого её объекта,
затем войдите под `boris` и откройте этот адрес вручную - ответ будет 404.

## Возможности

Обязательная часть:

- Темы и записи к ним, создание и редактирование записей (по учебнику).
- Регистрация с автоматическим входом, вход, выход **только POST-формой** с CSRF.
- Каждая тема принадлежит пользователю: чужие темы и записи не открываются даже по прямой ссылке (404).
- Владелец темы добавлен отдельной миграцией: существующие темы получают существующего пользователя, без `default=1` в модели.
- Оформление на Bootstrap 4 через `django-bootstrap4`, адаптивно для телефона.

Дополнительно:

- **Открытые темы**: тему можно сделать публичной - её прочитает любой посетитель, но изменить может только автор.
- Переименование и удаление тем, удаление записей - с отдельной страницей подтверждения, удаление только POST.
- Поиск по темам и тексту записей (без учёта регистра, в том числе для русского текста в SQLite).
- Сводка на главной: число тем, записей, открытых тем, последние темы.
- Постраничный вывод записей, отметка «изменена» у отредактированных записей.
- Смена пароля, понятные сообщения об успешных действиях, свои страницы 404 и 500.

## Страницы

| Страница | URL | Доступ |
|---|---|---|
| Главная | `/` | всем |
| Мои темы (+ поиск) | `/topics/` | после входа |
| Открытые темы | `/topics/public/` | всем |
| Тема и её записи | `/topics/<id>/` | владельцу; открытую - всем |
| Новая тема | `/new_topic/` | после входа |
| Изменить / удалить тему | `/topics/<id>/edit/`, `/topics/<id>/delete/` | только владельцу |
| Новая запись | `/new_entry/<topic_id>/` | только владельцу темы |
| Изменить / удалить запись | `/edit_entry/<id>/`, `/entries/<id>/delete/` | только владельцу |
| Вход, регистрация, выход | `/users/login/`, `/users/register/`, `/users/logout/` (POST) | всем |

## Права доступа

Каждый объект для изменения достаётся сразу с проверкой владельца:

```python
topic = get_object_or_404(Topic, id=topic_id, owner=request.user)
entry = get_object_or_404(Entry, id=entry_id, topic__owner=request.user)
```

Поэтому чужой и несуществующий ID дают одинаковый ответ 404, а скрытые ссылки в шаблоне - только удобство интерфейса.
Открытую тему чужой пользователь может только читать: добавление записи в неё тоже отвечает 404.

## Технологии

- Python 3.12, Django 5.2 LTS, django-bootstrap4 (Bootstrap 4.6)
- Gunicorn + WhiteNoise (статические файлы), Docker Compose
- SQLite на томе Docker по умолчанию или PostgreSQL через `DATABASE_URL`
- GitHub Actions: тесты на SQLite и PostgreSQL, `check --deploy` и запуск через `docker compose` при каждом push

## Структура

```
learning_log/            настройки проекта (settings.py читает всё из переменных окружения)
learning_logs/             основное приложение: модели, формы, представления, шаблоны, тесты
  management/commands/seed_demo.py   демо-данные для проверки
users/             регистрация, вход, POST-выход, смена пароля
  management/commands/ensure_admin.py   администратор из переменных окружения
templates/         base.html (навигация Bootstrap 4), страницы 404 и 500
static/css/        оформление поверх Bootstrap
Dockerfile, compose.yaml, start.sh   запуск в контейнере
render.yaml        бесплатное развёртывание на Render
```

## Локальный запуск

```sh
git clone https://github.com/njuk-s/rksi-learning-log.git
cd rksi-learning-log
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # Linux / macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Сайт откроется на http://127.0.0.1:8000/. Без файла `.env` проект работает в режиме разработки (`DEBUG=True`, SQLite рядом с `manage.py`).

## Тесты

```sh
python manage.py check
python manage.py test
```

Что проверяют тесты:

- вход обязателен для личных страниц, аноним перенаправляется на вход;
- список тем показывает только свои темы;
- чужая закрытая тема - 404; чужие тема и запись не меняются и не удаляются ни GET, ни POST;
- открытая тема доступна для чтения, но не для изменения;
- новая тема получает текущего владельца, подмена `owner` в POST игнорируется;
- отсутствующий ID - 404; удаление через GET только показывает подтверждение;
- миграция владельца назначает существующим темам существующего пользователя;
- регистрация, вход с `next`, выход только через POST и с CSRF-токеном;
- команды `ensure_admin` и `seed_demo`.

## Развёртывание на сервере через Docker Compose

Нужны Docker с плагином Compose и домен, направленный на сервер.

1. Получите код и создайте `.env` по образцу:

   ```sh
   git clone https://github.com/njuk-s/rksi-learning-log.git
   cd rksi-learning-log
   cp .env.example .env
   nano .env
   ```

   Обязательно задайте `DJANGO_SECRET_KEY` (сгенерировать: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`),
   `DJANGO_DEBUG=False`, свой домен в `DJANGO_ALLOWED_HOSTS` и `https://домен` в `DJANGO_CSRF_TRUSTED_ORIGINS`.

2. Запустите:

   ```sh
   docker compose up -d --build
   docker compose ps
   docker compose logs --tail=100 web
   ```

   При каждом запуске контейнер сам применяет миграции (`start.sh`), статические файлы собираются при сборке образа.
   Если в `.env` заданы `DJANGO_SUPERUSER_USERNAME` и `DJANGO_SUPERUSER_PASSWORD`, администратор создаётся автоматически;
   иначе создайте его вручную:

   ```sh
   docker compose exec web python manage.py createsuperuser
   ```

3. Настройте HTTPS на обратном прокси. Пример для Nginx на том же сервере (`APP_BIND_IP=127.0.0.1`, `APP_PORT=8000`):

   ```nginx
   server {
       listen 80;
       server_name learning.example.ru;
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Затем выпустите сертификат: `sudo certbot --nginx -d learning.example.ru --redirect`.
   Для Nginx Proxy Manager на другом сервере укажите в `APP_BIND_IP` внутренний IP сервера с Django и используйте его с портом 8000 в Proxy Host.

База SQLite хранится на именованном томе `learning_log_data` и не пропадает при `docker compose up -d --build`.
Обновление: `git pull && docker compose up -d --build`.

## Переменные окружения

| Переменная | Обязательна | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | да, на сервере | Секретный ключ. При `DEBUG=False` проект не запустится с ключом по умолчанию |
| `DJANGO_DEBUG` | да, на сервере | `False` на сервере; по умолчанию `True` |
| `DJANGO_ALLOWED_HOSTS` | да | Домены через запятую |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | да, для HTTPS | `https://домен` через запятую |
| `SQLITE_PATH` | нет | Путь к базе SQLite; в Docker `/app/data/db.sqlite3` |
| `DATABASE_URL` | нет | PostgreSQL вместо SQLite, например `postgresql://user:pass@host/db?sslmode=require` |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` | нет | Создать администратора при запуске |
| `SEED_DEMO`, `DEMO_PASSWORD` | нет | `SEED_DEMO=True` создаёт пользователей `anna` и `boris` с паролем `DEMO_PASSWORD` и демо-данные (один раз) |
| `DJANGO_SECURE_SSL_REDIRECT` | нет | `True` - перенаправлять HTTP на HTTPS средствами Django |
| `DJANGO_HSTS_SECONDS` | нет | Срок HSTS в секундах, по умолчанию 0 |
| `DJANGO_TIME_ZONE` | нет | Часовой пояс, по умолчанию `Europe/Moscow` |
| `APP_BIND_IP`, `APP_PORT` | нет | На каком адресе и порту Compose публикует контейнер (по умолчанию `127.0.0.1:8000`) |
| `PORT`, `WEB_CONCURRENCY` | нет | Порт и число процессов Gunicorn внутри контейнера (по умолчанию 8000 и 2) |

Файл `.env` в репозиторий не попадает (`.gitignore`), в репозитории лежит только образец `.env.example`.

## Бесплатное развёртывание без своего сервера

Работающая версия размещена бесплатно и не зависит от чьего-либо компьютера:

- **Render** (free web service) собирает образ по тому же `Dockerfile` и даёт домен с HTTPS;
- **Neon** (бесплатный PostgreSQL без срока действия) хранит данные: на бесплатном Render диск стирается
  при каждом перезапуске, поэтому SQLite там использовать нельзя - иначе публикации и пользователи пропадают;
- бесплатный Render усыпляет сервис после 15 минут без запросов, и первое открытие после сна занимает около 30 секунд.
  Workflow `.github/workflows/keepalive.yml` открывает `/healthz/` каждые 10 минут по будням с 8:00 до 17:00 по Москве,
  поэтому в рабочее время сайт открывается сразу. Круглосуточно будить нельзя: 750 бесплатных часов в месяц
  делятся на все сервисы аккаунта, и при их исчерпании Render отключает сервисы до конца месяца.
  `/healthz/` не обращается к базе, поэтому база Neon в простое засыпает и не тратит свой лимит.

Данные при засыпании и перезапуске не теряются: они в Neon, а не на диске контейнера.

Как повторить:

1. В [Neon](https://neon.com) создайте проект (регион Frankfurt) и скопируйте строку подключения (**Pooled connection**).
2. В [Render](https://render.com) выберите **New → Blueprint** и укажите этот репозиторий: настройки возьмутся из `render.yaml`.
3. Заполните `DATABASE_URL` (строка из Neon), `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` и `DEMO_PASSWORD`.
   `DJANGO_SECRET_KEY` Render сгенерирует сам.
4. После сборки сайт доступен по адресу `https://<имя-сервиса>.onrender.com`; миграции, администратор и демо-данные
   создаются при запуске контейнера.
5. Автодеплой: добавьте в репозиторий секрет `RENDER_API_KEY` (ключ из Render → Account Settings → API Keys)
   и переменную `RENDER_SERVICE_ID` (`srv-…` из адреса сервиса). Тогда после каждого push в `main` GitHub Actions
   сначала прогоняет тесты и сборку Docker, и только при успехе запускает деплой на Render.
