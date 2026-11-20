#!/usr/bin/env bash
#
# Install Umami analytics on this box.
#
#   sudo ./deploy/analytics-install.sh [domain]
#
# What it does:
#
#   1. installs Umami (free, open source) and its PostgreSQL database in
#      Docker, both bound to 127.0.0.1 - the dashboard is NOT on the
#      internet;
#   2. creates the website "Pliva River Lodge" and takes its id;
#   3. writes /var/www/plivariverlodge/analytics.js, the file the site
#      loads, with that id in it;
#   4. prints the one command that opens the dashboard.
#
# The dashboard is reached through an SSH tunnel, so there is no second
# domain, no second certificate and nothing for a stranger to log into.
# The numbers never leave this machine.
#
# The tracker itself is served from the same domain as the site (nginx
# proxies /stats.js and /api/send), so the visitor's browser talks to
# plivariverlodge.com only - no third party, no cookie, no banner.

set -euo pipefail

DOMAIN="${1:-plivariverlodge.com}"
SITE_DIR="${SITE_DIR:-/var/www/plivariverlodge}"
UMAMI_DIR="${UMAMI_DIR:-/opt/umami}"
UMAMI_PORT="${UMAMI_PORT:-3000}"
COMPOSE="$UMAMI_DIR/docker-compose.yml"
TRACKER="$SITE_DIR/analytics.js"

say() { printf '\n== %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" = "0" ] || die "run it with sudo"
[ -d "$SITE_DIR" ] || die "the site is not at $SITE_DIR - pass SITE_DIR=..."
command -v node >/dev/null 2>&1 || die "node is not installed (the site service needs it, so this is odd)"

# --- 1. docker -------------------------------------------------------------
say "1. docker"
if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed - installing it"
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq docker.io docker-compose-v2 || apt-get install -y -qq docker.io
  else
    die "no apt-get - install docker by hand and run this again"
  fi
fi
command -v docker >/dev/null 2>&1 || die "docker is still not there"
systemctl enable --now docker >/dev/null 2>&1 || true
docker info >/dev/null 2>&1 || die "docker is installed but not running (systemctl start docker)"

# --- 2. the container ------------------------------------------------------
say "2. umami"
mkdir -p "$UMAMI_DIR"
if [ ! -f "$UMAMI_DIR/.env" ]; then
  echo "writing a fresh .env with new secrets"
  umask 077
  PW="$(openssl rand -hex 24)"
  cat > "$UMAMI_DIR/.env" <<EOF
POSTGRES_DB=umami
POSTGRES_USER=umami
POSTGRES_PASSWORD=${PW}
DATABASE_URL=postgresql://umami:${PW}@db:5432/umami
DATABASE_TYPE=postgresql
APP_SECRET=$(openssl rand -hex 32)
TWO_FACTOR_ENCRYPTION_KEY=$(openssl rand -hex 32)
EOF
  chmod 600 "$UMAMI_DIR/.env"
else
  echo "the .env is already there - keeping it (the passwords must not change)"
fi

if [ ! -f "$COMPOSE" ]; then
  cat > "$COMPOSE" <<'EOF'
services:
  umami:
    image: ghcr.io/umami-software/umami:3
    container_name: umami
    restart: unless-stopped
    init: true
    env_file: .env
    environment:
      DATABASE_URL: ${DATABASE_URL}
      DATABASE_TYPE: ${DATABASE_TYPE}
      APP_SECRET: ${APP_SECRET}
      TWO_FACTOR_ENCRYPTION_KEY: ${TWO_FACTOR_ENCRYPTION_KEY}
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:3000/api/heartbeat"]
      interval: 10s
      retries: 30
  db:
    image: postgres:16-alpine
    container_name: umami-db
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - umami-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      retries: 20
volumes:
  umami-db-data:
EOF
fi

cd "$UMAMI_DIR"
docker compose up -d 2>/dev/null || docker-compose up -d
echo "waiting for the database and the app to come up"
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${UMAMI_PORT}/api/heartbeat" >/dev/null 2>&1; then
    echo "umami is up after ${i} seconds"
    break
  fi
  sleep 2
  if [ "$i" = "60" ]; then
    docker compose logs --tail 30 umami || true
    die "umami did not come up - read the log above"
  fi
done

# --- 3. the website and its id --------------------------------------------
say "3. the website"
WEBSITE_ID="$(node -e '
const base = "http://127.0.0.1:" + process.argv[1] + "/api/websites";
const domain = process.argv[2];
const auth = "Basic " + Buffer.from("admin:umami").toString("base64");
(async () => {
  const list = await fetch(base, { headers: { Authorization: auth } }).then(r => r.json());
  const found = (Array.isArray(list) ? list : list.websites || []).find(w => w.domain === domain);
  if (found) { console.log(found.id); return; }
  const res = await fetch(base, {
    method: "POST",
    headers: { Authorization: auth, "Content-Type": "application/json" },
    body: JSON.stringify({ name: "Pliva River Lodge", domain }),
  });
  if (!res.ok) { console.error("the API answered " + res.status); process.exit(1); }
  const body = await res.json();
  console.log(body.id || body.websiteId);
})();
' "$UMAMI_PORT" "$DOMAIN")"

[ -n "$WEBSITE_ID" ] || die "the website id could not be read from the API"
echo "website id: $WEBSITE_ID"

# --- 4. the tracker file the site loads -----------------------------------
say "4. the tracker"
cat > "$TRACKER" <<EOF
/* Written by deploy/analytics-install.sh - not part of the repository.
   The website id below is the only thing that is specific to this site. */
(function () {
  var s = document.createElement('script');
  s.defer = true;
  s.src = '/stats.js';
  s.setAttribute('data-website-id', '$WEBSITE_ID');
  s.setAttribute('data-host-url', 'https://$DOMAIN');
  document.head.appendChild(s);
})();
EOF
chown --reference="$SITE_DIR/index.html" "$TRACKER" 2>/dev/null || true
chmod 644 "$TRACKER"
echo "wrote $TRACKER"

cat > "$UMAMI_DIR/README.txt" <<EOF
Umami analytics for $DOMAIN
============================
The dashboard is on this machine only:

    ssh -L 3000:127.0.0.1:$UMAMI_PORT root@<this server>
    then open http://localhost:3000 in the browser
    the first time: admin / umami - change that password at once

The data is in the umami-db container (volume umami-db-data).
To start it again after a reboot:  cd $UMAMI_DIR && docker compose up -d
EOF
echo "wrote $UMAMI_DIR/README.txt"

# --- 5. what is left to do -------------------------------------------------
say "5. the nginx part"
if grep -qs "stats.js" /etc/nginx/sites-available/pliva-riverside 2>/dev/null; then
  echo "the site configuration already knows about /stats.js - nothing to do"
else
  cat <<'EOF'
The nginx configuration on this box does not have the two lines that
serve the tracker yet. They come with the repository:

    sudo ./deploy/deploy.sh plivariverlodge.com

and then reload nginx. Until that is done the site still works, it only
does not count anything yet.
EOF
fi

cat <<EOF

Done.

  * the tracker file is $TRACKER
  * the website id is $WEBSITE_ID
  * the dashboard is not on the internet - open it with:

        ssh -L 3000:127.0.0.1:$UMAMI_PORT root@<this server>
        (then http://localhost:3000 - admin / umami, change the password)

  * CHANGE THE ADMIN PASSWORD the first time you log in.

  * What you will see there: visitors and page views over time, the
    referring sites (which Facebook group sent somebody), the countries,
    the browsers, and the URL parameters - the utm_campaign tag in every
    posting link says which group it was.

EOF
