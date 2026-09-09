#!/usr/bin/env sh
set -eu
COMPOSE="docker compose --env-file .env.pilot -f docker-compose.pilot.yml"
echo "Repository migration head(s):"
$COMPOSE exec -T backend alembic heads
echo
echo "Database current revision:"
$COMPOSE exec -T backend alembic current
