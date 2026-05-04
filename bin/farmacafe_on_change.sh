#!/usr/bin/env bash
set -euo pipefail

PAYLOAD_FILE="${1:-}"
if [[ -z "$PAYLOAD_FILE" || ! -f "$PAYLOAD_FILE" ]]; then
  echo "Usage: $0 <json_payload_file>" >&2
  exit 1
fi

ENV_FILE="${ENV_FILE:-$HOME/.config/environment.d/farmacafe.conf}"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# Configuration
EMAIL_TO="${EMAIL_TO:-rausalinas@gmail.com}"
TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Parse JSON
JSON="$(cat "$PAYLOAD_FILE")"
RESTAURANT="$(echo "$JSON" | jq -r '.parsed.restaurant.name // "Menu"')"
DATE="$(echo "$JSON" | jq -r '.parsed.menu.display_date // "N/A"')"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
PRICE="$(echo "$JSON" | jq -r '.parsed.menu.price // "N/A"')"
INCLUDES="$(echo "$JSON" | jq -r '.parsed.menu.includes // "N/A"')"
MENU_URL="$(echo "$JSON" | jq -r '.source.url // "https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu"')"
MENU_TEXT="$(echo "$JSON" | jq -r '
  (.parsed.menu.sections // [])
  | map(
      "- " + (.title // "Section") + "\n"
      + ((.dishes // [])
         | map(
             "  * "
             + (.name // "Dish")
             + (if ((.allergen_titles // []) | length) > 0
                then " (" + ((.allergen_titles // []) | join(", ")) + ")"
                else ""
                end)
           )
         | join("\n"))
    )
  | join("\n\n")
')"
TELEGRAM_MESSAGE="$(echo "$JSON" | jq -r '
  def allergens($values):
    if ($values | length) == 0 then "" else " (" + ($values | join(", ")) + ")" end;
  def dish_line:
    "   • " + (.name // "Plat") + allergens(.allergen_titles // []);

  "🍽 *" + (.parsed.restaurant.name // "Cafeteria de Farmàcia UV") + "*\n"
  + "📅 Menú del dia: " + (.parsed.menu.display_date // "hui") + "\n"
  + (if ((.parsed.menu.price // "") | length) > 0 then "💶 " + .parsed.menu.price + "\n" else "" end)
  + (if ((.parsed.menu.includes // "") | length) > 0 then "ℹ️ " + .parsed.menu.includes + "\n" else "" end)
  + "\n"
  + ((.parsed.menu.sections // [])
      | map(
          "▪️ *" + (.title // "Secció") + "*\n"
          + ((.dishes // []) | map(dish_line) | join("\n"))
        )
      | join("\n\n"))
  + "\n\n🔗 Menú online: " + (.source.url // "https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu")
')"

# 1. Mail notification
if command -v mail >/dev/null 2>&1; then
  SUBJECT="📋 Cambio en menú - $RESTAURANT"
  BODY="Cambio detectado en la Cafeteria de Farmàcia UV

Restaurante: $RESTAURANT
Fecha del menú: $DATE
Precio: $PRICE
Incluye: $INCLUDES
Notificación: $TIMESTAMP

Menú detectado:
$MENU_TEXT

Consulta el menú actualizado:
$MENU_URL"

  echo "$BODY" | mail -s "$SUBJECT" "$EMAIL_TO" 2>/dev/null || \
    echo "[farmacafe_on_change] Mail sending failed (mail command error)" >&2
else
  echo "[farmacafe_on_change] Mail command not found" >&2
fi

# 2. Telegram notification
if [[ -n "$TELEGRAM_TOKEN" ]] && [[ -n "$TELEGRAM_CHAT_ID" ]]; then
  TELEGRAM_RESPONSE="$(curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{
      \"chat_id\": $TELEGRAM_CHAT_ID,
      \"text\": $(echo "$TELEGRAM_MESSAGE" | jq -Rs .),
      \"parse_mode\": \"Markdown\"
    }" )"

  if [[ "$(echo "$TELEGRAM_RESPONSE" | jq -r '.ok // false' 2>/dev/null)" != "true" ]]; then
    echo "[farmacafe_on_change] Telegram notification failed" >&2
    echo "[farmacafe_on_change] Telegram response: $TELEGRAM_RESPONSE" >&2
    TELEGRAM_STATUS="failed"
  else
    TELEGRAM_STATUS="enabled (sent)"
  fi
else
  TELEGRAM_STATUS="disabled (set TELEGRAM_CHAT_ID)"
fi

echo "[farmacafe_on_change] Notifications sent"
echo "  - Email: $EMAIL_TO"
echo "  - Telegram: $TELEGRAM_STATUS"
