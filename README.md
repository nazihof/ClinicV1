# Pilot Deployment Sprint

This package is a **deployment overlay** for the clinic application after Sprint 4.5D.

It intentionally does **not** contain or overwrite:

- `backend/app/models.py`
- Alembic migration files
- application schemas
- frontend business logic

That is deliberate. Your local project now contains your latest schema correction (including the Service `is_active` change and any newer Alembic revision). Keep those files from your current Git working tree.

## Goal

Deploy the current tested clinic application to one Linux VPS/server with:

- PostgreSQL 16
- FastAPI backend
- Next.js frontend
- Caddy reverse proxy
- HTTPS
- persistent database volume
- production-only secrets
- production backup/smoke-test scripts

## Files

- `docker-compose.pilot.yml` - production Compose overlay
- `Caddyfile.pilot` - HTTPS reverse proxy
- `.env.pilot.example` - production environment template
- `PILOT_DEPLOYMENT_GUIDE.md` - step-by-step server deployment
- `scripts/backup_prod.sh` - SQL backup
- `scripts/smoke_prod.sh` - production smoke test
- `scripts/check_migrations.sh` - compares current revision with repository head

## Important

Do not copy this ZIP over your project as if it were a full Sprint source replacement.
Copy these deployment files **into your current stable Git project**.

Never run `docker compose down -v` on the pilot server.
