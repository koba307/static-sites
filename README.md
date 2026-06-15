# Мой сайт (static)

Папка для статического сайта. Все .html и .htm файлы в этой папке доступны по прямым ссылкам.

## Как работает локально
Уже запущен сервер:
```
http://localhost:8000/
```

Просто добавляй файлы:
- `index.html` — главная
- `about.html` — любая страница
- `мои-проекты.html` — будет по адресу `/мои-проекты.html`

## Развёртывание (бесплатно)

### Вариант 0: Surge.sh (самый простой, один клик из терминала)

✅ **Сайт уже захосчен!**

**Публичный адрес:**
**https://koba-sites.surge.sh**

**Как обновить сайт в будущем:**

1. Открой терминал и перейди в эту папку:
   ```bash
   cd ~/Рабочий\ стол/sites
   ```

2. Отредактируй нужные `.html` файлы в корне (city.html, dance_scool.html и т.д.)

3. Запусти деплой:
   ```bash
   ./deploy.sh
   ```

   Скрипт автоматически:
   - скопирует актуальное содержимое в папки для чистых URL (`city-geo/`, `dance-scool/` и т.д.)
   - опубликует на Surge

Файл `CNAME` уже создан и содержит `koba-sites.surge.sh`, поэтому все последующие деплои будут автоматически идти на этот же адрес.

### Чистые ссылки (без .html)

**Основные:**

| Ссылка                                   | Файл-источник      |
|------------------------------------------|--------------------|
| https://koba-sites.surge.sh/city-geo     | city.html          |
| https://koba-sites.surge.sh/dance-scool  | dance_scool.html   |
| https://koba-sites.surge.sh/football     | football.html      |
| https://koba-sites.surge.sh/promo-codes  | promocode.html     |

**Ссылки на один и тот же файл gos.html**:

| Ссылка                                                      | Файл-источник |
|-------------------------------------------------------------|---------------|
| https://koba-sites.surge.sh/open-spotifycom-intl-f-artist   | gos.html      |
| https://koba-sites.surge.sh/music-yandex-ru-artist          | gos.html      |
| https://koba-sites.surge.sh/ru-pinteres-com-pin             | gos.html      |

Обычные пути с .html тоже работают (`/city.html`, `/gos.html` и т.д.).

### Как обновить
Отредактируй исходные файлы в корне (`gos.html`, `city.html` и т.д.), затем:
```bash
./deploy.sh
```
Скрипт сам обновит все папки и зальёт каждый домен отдельно.

### Конфигурация (config.json)
В файле `config.json` можно изменить:
- `phone_number` — номер телефона, который используется на всех страницах (фейковые госуслуги и т.д.)
- `links` — список имён ссылок/доменов
- `port` — порт локального сервера

После изменения номера телефона запусти:
```bash
python apply-config.py
```
(или apply-config.bat на Windows)

### Локальный сервер (Windows)
- `start-server.bat` — запуск
- `stop-server.bat` — остановка
- `restart-server.bat` — перезапуск
- `apply-config.bat` — применить настройки из config.json (телефон и т.д.)

На Linux используй `./serve.sh` (порт тоже берётся из config.json если возможно).

**Как обновить сайт в будущем:**

1. Открой терминал и перейди в эту папку:
   ```bash
   cd ~/Рабочий\ стол/sites
   ```

2. Отредактируй нужные `.html` файлы в корне:
   - `city.html`, `dance_scool.html`, `football.html`, `promocode.html` — для основных
   - `gos.html` — для gos-доменов: open-spotifycom-intl-f-artist, music-yandex-ru-artist, ru-pinteres-com-pin, gosuslugi-login

3. Запусти деплой:
   ```bash
   ./deploy.sh
   ```

   Скрипт автоматически:
   - скопирует актуальное содержимое в папки для чистых URL (включая новые алиасы на gos.html)
   - опубликует на Surge

Каждый домен деплоится отдельно через `./deploy.sh` (подпапки с index.html). Нет единого CNAME.

---

**Текущий деплой:**
- Аккаунт: folgavolosata@gmail.com (Student)
- 20 файлов, ~162 KB
- SSL включён, CDN в 10+ локациях

### Старые инструкции по первому деплою (для справки)

Если нужно создать новый проект на surge:
1. `cd` в папку
2. `surge`
3. Введи email/пароль surge (если не залогинен)
4. Выбери или подтверди домен

Чтобы сменить домен — удали файл `CNAME` и запусти `surge` заново.

### Вариант 1: GitHub Pages (рекомендую)
1. Репозиторий уже создан (или создаётся).
2. В настройках репозитория → Pages → Source: **Deploy from a branch** → `main` / `(root)`
3. Сайт будет по адресу: `https://koba307.github.io/НАЗВАНИЕ-РЕПО/`

### Вариант 2: Бесплатный "настоящий" домен
- **DigitalPlat** (лучший сейчас): https://dash.domain.digitalplat.org/
  Зарегистрируй например `koba.dpdns.org` или `мойсайт.qzz.io`
  Потом сделай CNAME на твой GitHub Pages / Netlify URL.

- **is-a.dev**: https://github.com/is-a-dev/register
  Получишь `koba.is-a.dev` (через PR).

### Быстрый деплой без Git
Зайди на https://app.netlify.com/drop и перетащи всю эту папку.

## Советы
- Для чистых URL без .html можно использовать подпапки с index.html внутри.
- Добавь файл `.nojekyll` (пустой), если используешь GitHub Pages.
- Можно подключить любой бесплатный домен через CNAME.

Удачи с сайтом!