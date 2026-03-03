#!/bin/sh
# Generate runtime config from environment variables.
# This replaces Vite's build-time VITE_* variables with runtime injection
# so that pre-built Docker images can be configured per deployment.

CONFIG_FILE="/usr/share/nginx/html/config.js"

cat <<EOF > "$CONFIG_FILE"
window.__ENV = {
  TELEGRAM_BOT_USERNAME: "${TELEGRAM_BOT_USERNAME:-}",
  API_URL: "${API_URL:-}",
  WS_URL: "${WS_URL:-}",
  SECRET_PATH: "${WEB_SECRET_PATH:-}"
};
EOF

echo "Runtime config generated at $CONFIG_FILE"

# Generate nginx config with secret path support
if [ -n "$WEB_SECRET_PATH" ]; then
  # Strip leading/trailing slashes for consistent handling
  SECRET=$(echo "$WEB_SECRET_PATH" | sed 's|^/||;s|/$||')
  export NGINX_SECRET_PATH="/$SECRET"
  envsubst '${NGINX_SECRET_PATH}' < /etc/nginx/nginx-secret.conf.template > /etc/nginx/conf.d/default.conf
  echo "Secret path enabled: $NGINX_SECRET_PATH"
fi

exec "$@"
