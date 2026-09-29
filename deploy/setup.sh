#!/bin/sh
#
# Развёртывание трёх учебных проектов на сервере колледжа.
#
# Запускать НА СЕРВЕРЕ, подключившись по ssh student@192.168.1.11:
#
#   curl -fsSL https://raw.githubusercontent.com/njuk-s/rksi-learning-log/main/deploy/setup.sh | sh
#
# Скрипт для каждого проекта создаёт каталог командой newproject, забирает код
# с GitHub, дописывает настройки в .env, собирает контейнер и дожидается, пока
# приложение ответит. Повторный запуск ничего не ломает: пароли и секретный
# ключ, созданные в прошлый раз, сохраняются.
#
# Первый аргумент - фамилия латиницей (с неё начинаются имена проектов),
# второй и далее - какие проекты разворачивать. Без аргументов берётся
# фамилия njukalov и все три проекта.

set -eu

SURNAME="${1:-njukalov}"
[ $# -gt 0 ] && shift
SERVER_IP="192.168.1.11"
GITHUB_USER="njuk-s"
ADMIN_USER="review_admin"

# Короткое имя проекта -> имя репозитория на GitHub.
repo_for() {
    case "$1" in
        learning-log) echo "rksi-learning-log" ;;
        task-manager) echo "rksi-task-manager" ;;
        blog)         echo "rksi-blog" ;;
        *)            echo "" ;;
    esac
}

PROJECTS="${*:-learning-log task-manager blog}"
mkdir -p "$HOME/projects"
SUMMARY_FILE="$HOME/projects/${SURNAME}-sites.txt"

say()  { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
fail() { printf '\nОШИБКА: %s\n' "$*" >&2; exit 1; }

# --- подготовка -------------------------------------------------------------

for tool in git newproject; do
    command -v "$tool" >/dev/null 2>&1 || fail "на сервере нет команды $tool"
done

if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    fail "не найден ни docker compose, ни docker-compose"
fi

if command -v curl >/dev/null 2>&1; then
    fetch() { curl -fsS --max-time 10 "$1" >/dev/null 2>&1; }
elif command -v wget >/dev/null 2>&1; then
    fetch() { wget -q -T 10 -O /dev/null "$1" >/dev/null 2>&1; }
else
    fetch() { return 0; }   # проверить нечем - считаем, что всё хорошо
fi

# Случайная строка нужной длины из букв и цифр.
random_string() {
    LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom 2>/dev/null | dd bs=1 count="$1" 2>/dev/null
    echo
}

# Значение переменной из файла .env (пустая строка, если её там нет).
value_from() {
    [ -f "$2" ] || return 0
    sed -n "s/^$1=//p" "$2" | tail -n 1
}

# Пароли общие для всех трёх сайтов: так их проще запомнить и передать.
FIRST_ENV="$HOME/projects/${SURNAME}-learning-log/.env"
ADMIN_PASS="$(value_from DJANGO_SUPERUSER_PASSWORD "$FIRST_ENV")"
DEMO_PASS="$(value_from DEMO_PASSWORD "$FIRST_ENV")"
[ -n "$ADMIN_PASS" ] || ADMIN_PASS="Rksi-$(random_string 12)"
[ -n "$DEMO_PASS" ] || DEMO_PASS="Demo-$(random_string 10)"

say "Фамилия в именах проектов: $SURNAME"
say "Проекты: $PROJECTS"
say "Compose: $COMPOSE"

: > "$SUMMARY_FILE.tmp"

# --- развёртывание ----------------------------------------------------------

for SHORT in $PROJECTS; do
    REPO="$(repo_for "$SHORT")"
    [ -n "$REPO" ] || fail "неизвестный проект: $SHORT"

    NAME="${SURNAME}-${SHORT}"
    step "Проект $NAME"

    # 1. Каталог, порты и .env создаёт newproject. Повторный запуск безопасен:
    #    он только показывает уже выданные значения.
    NEWPROJECT_OUT="$(newproject "$NAME" 2>&1 || true)"
    say "$NEWPROJECT_OUT" | sed 's/^/   /'

    DIR="$HOME/projects/$NAME"
    [ -d "$DIR" ] || fail "каталог $DIR не появился. Вывод newproject выше."
    cd "$DIR"

    # 2. Порт берём из .env (его записывает newproject), иначе - из вывода команды.
    PORT="$(value_from PORT1 .env)"
    if [ -z "$PORT" ]; then
        PORT="$(printf '%s' "$NEWPROJECT_OUT" | tr -c '0-9' ' ' | tr ' ' '\n' \
                | grep -E '^[0-9]{4,5}$' | head -n 1)"
    fi
    [ -n "$PORT" ] || fail "не удалось определить порт проекта $NAME"
    say "   порт: $PORT"

    # 3. Код забираем с GitHub. reset --hard делает каталог точной копией main
    #    и при этом не трогает .env: он не под контролем версий.
    URL="https://github.com/${GITHUB_USER}/${REPO}.git"
    [ -d .git ] || git init -q
    if git remote | grep -qx origin; then
        git remote set-url origin "$URL"
    else
        git remote add origin "$URL"
    fi
    say "   забираю код из $REPO"
    git fetch -q --depth 1 origin main
    git reset -q --hard origin/main

    # 4. Настройки. Свой блок переписываем целиком, строки от newproject не трогаем.
    SECRET="$(value_from DJANGO_SECRET_KEY .env)"
    [ -n "$SECRET" ] || SECRET="$(random_string 60)"

    if [ -f .env ]; then
        sed '/# --- настройки проекта, добавлены скриптом ---/,$d' .env > .env.new
    else
        : > .env.new
    fi
    cat >> .env.new <<ENVEOF
# --- настройки проекта, добавлены скриптом ---
DJANGO_SECRET_KEY=$SECRET
DJANGO_DEBUG=False
# Сайт открывается по http://IP:порт, без HTTPS. При True браузер не сохранит
# куки, и вход перестанет работать.
DJANGO_USE_HTTPS=False
DJANGO_ALLOWED_HOSTS=$SERVER_IP,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://$SERVER_IP:$PORT
SQLITE_PATH=/app/data/db.sqlite3
APP_BIND_IP=0.0.0.0
APP_PORT=$PORT
# Сервер общий для группы: один рабочий процесс.
WEB_CONCURRENCY=1
DJANGO_SUPERUSER_USERNAME=$ADMIN_USER
DJANGO_SUPERUSER_PASSWORD=$ADMIN_PASS
SEED_DEMO=True
DEMO_PASSWORD=$DEMO_PASS
ENVEOF
    mv .env.new .env
    chmod 600 .env 2>/dev/null || true
    say "   .env обновлён"

    # 5. Сборка и запуск. Миграции, администратор и демо-данные выполняются
    #    внутри контейнера при старте (start.sh -> manage.py prestart).
    say "   собираю образ, это занимает несколько минут..."
    $COMPOSE up -d --build

    # 6. Ждём, пока приложение начнёт отвечать.
    say "   жду ответа приложения..."
    READY="нет"
    i=0
    while [ "$i" -lt 60 ]; do
        if fetch "http://127.0.0.1:$PORT/healthz/"; then READY="да"; break; fi
        i=$((i + 1))
        sleep 5
    done

    if [ "$READY" = "да" ]; then
        say "   готово: http://$SERVER_IP:$PORT/"
        printf '%-14s http://%s:%s/\n' "$SHORT" "$SERVER_IP" "$PORT" >> "$SUMMARY_FILE.tmp"
    else
        say "   приложение не ответило. Журнал:"
        $COMPOSE logs --tail=40 web | sed 's/^/      /'
        printf '%-14s http://%s:%s/  (НЕ ОТВЕТИЛО)\n' "$SHORT" "$SERVER_IP" "$PORT" >> "$SUMMARY_FILE.tmp"
    fi
done

# --- итог -------------------------------------------------------------------

{
    echo "Сайты на учебном сервере"
    echo
    cat "$SUMMARY_FILE.tmp"
    echo
    echo "Вход одинаковый на всех сайтах:"
    echo "  администратор /admin/: $ADMIN_USER / $ADMIN_PASS"
    echo "  пользователи: anna и boris, пароль $DEMO_PASS"
    echo
    echo "Обновить сайт после правок кода:"
    echo "  cd ~/projects/${SURNAME}-<проект> && git pull origin main && $COMPOSE up -d --build"
} > "$SUMMARY_FILE"
rm -f "$SUMMARY_FILE.tmp"

step "Готово"
cat "$SUMMARY_FILE"
say ""
say "Это же сохранено в файле $SUMMARY_FILE"
