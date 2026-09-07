# Sprint 4.5C Production Deployment Runbook

This runbook is for a single Linux server/VPS using Docker Compose and two DNS names, for example:

- App: `clinic.example.com`
- API: `api-clinic.example.com`

## 1. Pre-deployment gate

Before touching the server:

1. Commit/tag the tested code in Git.
2. Create and verify a PostgreSQL backup from the current installation.
3. Record the current Alembic revision.
4. Confirm you can log in as an OWNER.
5. Keep the backup somewhere outside the server as well.

Do not rely on the Docker volume as your only backup.

## 2. Server requirements

- Linux VPS/server
- Docker Engine + Docker Compose plugin
- public IPv4/IPv6 as appropriate
- firewall allowing inbound TCP 80 and 443 (and UDP 443 for HTTP/3 if desired)
- SSH access restricted to administrators

Do not expose PostgreSQL port 5432 publicly.

## 3. DNS

Create DNS records pointing both names to the server:

- `clinic.example.com` -> server IP
- `api-clinic.example.com` -> server IP

Wait until DNS resolves correctly before starting Caddy. Automatic HTTPS depends on this.

## 4. Production secrets

Copy:

```bash
cp .env.production.example .env.production
```

Generate strong independent random values for `POSTGRES_PASSWORD` and `JWT_SECRET`.

Example JWT secret generation:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Set the real domains:

```env
APP_DOMAIN=clinic.example.com
API_DOMAIN=api-clinic.example.com
CORS_ORIGINS=https://clinic.example.com
```

Never commit `.env.production` to Git.

## 5. Start production

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Check:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Expected services:

- db healthy
- backend healthy
- frontend running
- caddy running

## 6. Verify migration

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec backend alembic current
```

Expected:

`0006_audit_logs (head)`

## 7. Verify HTTPS

Open:

- `https://clinic.example.com`
- `https://api-clinic.example.com/health`

The API health endpoint should return version `4.5.3-pilot.1`.

Check Caddy certificate logs if HTTPS is not issued:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs caddy --tail=100
```

## 8. Functional smoke test

1. Login as OWNER.
2. Check clinic, doctors and services.
3. Open today's appointment schedule.
4. Create a test patient/appointment if appropriate.
5. Check Attention Queue.
6. Check Operational Dashboard.
7. Open Audit log and verify the test write was recorded.
8. Log out and log in again.

## 9. Backup after deployment

Create a fresh production backup after successful migration and smoke testing. Store a copy outside the host.

The provided Windows `.cmd` scripts are for the development workstation. On a Linux server, a typical backup is:

```bash
mkdir -p backups
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists > backups/clinic_$(date +%Y%m%d_%H%M%S).sql
```

If shell variables are not exported, substitute the actual database user/database names from `.env.production`.

## 10. Updating production later

Always use this order:

1. backup database
2. verify backup
3. Git tag current working code
4. pull/copy new release
5. rebuild with production Compose
6. check Alembic revision
7. smoke test

Never use `docker compose down -v` on production.

## 11. Rollback rule

Code rollback and database rollback are different.

- If only frontend/backend code is bad and no incompatible migration occurred: return to the previous Git tag and rebuild.
- If a migration changed the database incompatibly: assess the Alembic downgrade first.
- Restore a SQL backup only when necessary, because restoring replaces newer database state with the backup snapshot.

Do not restore blindly over a live production database.

## 12. Logs and incidents

Useful commands:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs backend --tail=100
docker compose --env-file .env.production -f docker-compose.prod.yml logs frontend --tail=100
docker compose --env-file .env.production -f docker-compose.prod.yml logs caddy --tail=100
docker compose --env-file .env.production -f docker-compose.prod.yml logs db --tail=100
```

Audit logs complement server logs; they do not replace infrastructure monitoring or formal security incident logging.
