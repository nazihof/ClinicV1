#!/usr/bin/env sh
set -eu
APP_DOMAIN=$(grep '^APP_DOMAIN=' .env.pilot | head -n1 | cut -d= -f2-)
API_DOMAIN=$(grep '^API_DOMAIN=' .env.pilot | head -n1 | cut -d= -f2-)
COMPOSE="docker compose --env-file .env.pilot -f docker-compose.pilot.yml"

echo "1/5 Containers"
$COMPOSE ps

echo "2/5 Alembic"
$COMPOSE exec -T backend alembic current

echo "3/5 API health"
curl -fsS "https://${API_DOMAIN}/health"
echo

echo "4/5 Frontend"
curl -fsSI "https://${APP_DOMAIN}/" >/dev/null

echo "5/5 Database connectivity"
$COMPOSE exec -T backend python -c "from backend.app.database import engine; from sqlalchemy import text; c=engine.connect(); c.execute(text('SELECT 1')); c.close(); print('database ok')"

echo "PILOT SMOKE TEST PASSED"
