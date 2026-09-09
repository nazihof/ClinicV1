#!/usr/bin/env sh
set -eu
mkdir -p backups
STAMP=$(date +%Y%m%d_%H%M%S)
FILE="backups/clinic_${STAMP}.sql"
COMPOSE="docker compose --env-file .env.pilot -f docker-compose.pilot.yml"

# Read non-secret DB names from env file without sourcing arbitrary shell code.
POSTGRES_USER=$(grep '^POSTGRES_USER=' .env.pilot | head -n1 | cut -d= -f2-)
POSTGRES_DB=$(grep '^POSTGRES_DB=' .env.pilot | head -n1 | cut -d= -f2-)
POSTGRES_USER=${POSTGRES_USER:-clinic}
POSTGRES_DB=${POSTGRES_DB:-clinic}

$COMPOSE exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists > "$FILE"

test -s "$FILE"
echo "Backup created: $FILE"
echo "Copy this file to a second location outside the VPS."
