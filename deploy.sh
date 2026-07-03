#!/usr/bin/env bash
# ─── Deployment script for Ubuntu 24.04 (DigitalOcean) ─────────────────
# Usage:
#   sudo ./deploy.sh <your-domain.com>
#
# This script is idempotent — running it multiple times will update
# the application and re-issue certificates as needed.
#
# Prerequisites:
#   - Ubuntu 24.04 VM with root or sudo access
#   - DNS A record pointing <domain> to the VM's IP
#   - .env file at /root/leadgen-agent.env or passed interactively
#   - Git SSH deploy key (or use HTTPS clone)
# =======================================================================

set -euo pipefail

DOMAIN="${1:?Usage: sudo $0 <your-domain.com>}"
REPO_URL="${REPO_URL:-https://github.com/alpercaglar11-hub/-Leadgen.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="/opt/leadgen-agent"
ENV_FILE="/root/leadgen-agent.env"
COMPOSE_FILE="${APP_DIR}/docker-compose.yml"
SERVICE_NAME="leadgen-agent"

echo "═══ LeadGen Agent Deploy — domain: ${DOMAIN} ═══"

# ── 1. System packages ────────────────────────────────────────────────
echo "[1/7] Installing system dependencies…"
apt-get update -qq
apt-get install -y -qq \
    ca-certificates curl gnupg nginx certbot python3-certbot-nginx \
    >/dev/null

# ── 2. Docker ─────────────────────────────────────────────────────────
echo "[2/7] Installing Docker…"
if ! command -v docker &>/dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        | tee /etc/apt/sources.list.d/docker.list >/dev/null
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
        docker-compose-plugin >/dev/null
    systemctl enable --now docker
    echo "  Docker installed."
else
    echo "  Docker already installed — skipping."
fi

# ── 3. Clone / pull the repository ────────────────────────────────────
echo "[3/7] Deploying application code…"
mkdir -p "$(dirname "${APP_DIR}")"
if [ -d "${APP_DIR}/.git" ]; then
    cd "${APP_DIR}"
    git fetch origin
    git checkout "${BRANCH}"
    git pull origin "${BRANCH}"
else
    git clone --depth=1 --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
    cd "${APP_DIR}"
fi

# ── 4. Environment file ────────────────────────────────────────────────
echo "[4/7] Configuring environment…"
if [ -f "${ENV_FILE}" ]; then
    echo "  Using existing env file: ${ENV_FILE}"
else
    echo "  Creating env file from .env.example…"
    cp "${APP_DIR}/.env.example" "${ENV_FILE}"
    echo ""
    echo "  ⚠  EDIT THE ENV FILE NOW: sudo nano ${ENV_FILE}"
    echo "  Required: DB_PASSWORD, STRIPE_API_KEY, SENDGRID_API_KEY"
    echo "  After editing, re-run this script."
    exit 1
fi

# Validate essential variables
set +e
source "${ENV_FILE}" 2>/dev/null
grep -q 'DB_PASSWORD='   "${ENV_FILE}" && grep -qv 'DB_PASSWORD=$'   "${ENV_FILE}" \
    || { echo "ERROR: DB_PASSWORD is missing or empty in ${ENV_FILE}"; exit 1; }
grep -q 'STRIPE_API_KEY=' "${ENV_FILE}" && grep -qv 'STRIPE_API_KEY=$' "${ENV_FILE}" \
    || echo "WARNING: STRIPE_API_KEY is empty — subscriptions won't work."
grep -q 'SENDGRID_API_KEY=' "${ENV_FILE}" && grep -qv 'SENDGRID_API_KEY=$' "${ENV_FILE}" \
    || echo "WARNING: SENDGRID_API_KEY is empty — emails won't be sent."
set -e

# Copy env for docker-compose
cp "${ENV_FILE}" "${APP_DIR}/.env"

# ── 5. Start the application ──────────────────────────────────────────
echo "[5/7] Building and starting containers…"
cd "${APP_DIR}"
docker compose pull
docker compose up --build -d --remove-orphans
echo "  Containers started. Checking health…"

# Wait for web to be healthy (up to 60 s)
HEALTHY=false
for i in $(seq 1 12); do
    sleep 5
    if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
        HEALTHY=true
        echo "  ✅ Web service is healthy (attempt $i)."
        break
    fi
    echo "  Waiting… attempt $i/12"
done

if [ "${HEALTHY}" != "true" ]; then
    echo "  ⚠ Web service did not report healthy within 60 s."
    echo "    Run: docker compose logs web"
fi

# ── 6. Nginx reverse proxy ────────────────────────────────────────────
echo "[6/7] Configuring Nginx for ${DOMAIN}…"

NGINX_CONF="/etc/nginx/sites-available/${SERVICE_NAME}"

cat > "${NGINX_CONF}" <<NGINX
server {
    listen 80;
    server_name ${DOMAIN};
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 3600s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        access_log off;
    }
}
NGINX

# Enable site
ln -sf "${NGINX_CONF}" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t && systemctl reload nginx
echo "  Nginx configured for ${DOMAIN}."

# ── 7. SSL certificate (certbot) ─────────────────────────────────────
echo "[7/7] Obtaining SSL certificate for ${DOMAIN}…"
if [ -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
    echo "  Existing certificate found — renewing."
    certbot renew --nginx --non-interactive
else
    certbot --nginx \
        --domain "${DOMAIN}" \
        --non-interactive \
        --agree-tos \
        --email "admin@${DOMAIN}" \
        --redirect
fi

# Set up auto-renewal (certbot's systemd timer handles this, but add a
# daily check as a safety net)
(
    crontab -l 2>/dev/null || true
    echo "17 3 * * * certbot renew --nginx --non-interactive && systemctl reload nginx"
) | sort -u | crontab -

# ── Add agent cron ────────────────────────────────────────────────────
echo "  + Adding agent run cron (every 6 hours)…"
(
    crontab -l 2>/dev/null || true
    echo "0 */6 * * * cd ${APP_DIR} && docker compose run --rm agent run"
) | sort -u | crontab -

echo ""
echo "═══ Deploy complete ═══"
echo "  App:      https://${DOMAIN}"
echo "  Health:   https://${DOMAIN}/health"
echo "  Dashboard: https://${DOMAIN}/dashboard"
echo ""
echo "Next steps:"
echo "  - Verify DNS resolves: dig ${DOMAIN}"
echo "  - Check logs: docker compose logs -f"
echo "  - Add your API_KEY to ${ENV_FILE} and re-deploy for auth."
