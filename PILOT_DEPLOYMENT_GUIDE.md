# Pilot Deployment Guide

This is the first controlled Internet deployment of the clinic application.

## Phase 0 — Freeze the local build

Do this on your Windows development computer before touching a VPS.

1. Confirm the app works locally.
2. Confirm `alembic check` reports no unintended changes.
3. Create a fresh database backup.
4. Commit your current source — including your latest Service model and latest migration.
5. Tag the build.

Example:

```cmd
git add .
git commit -m "Pilot deployment candidate"
git tag pilot-deployment-1
```

Do not deploy an older ZIP over this current Git state.

## Phase 1 — Choose the server

Use one small Linux VPS for the controlled pilot. A practical starting size is:

- Ubuntu 22.04 or 24.04 LTS
- 2 vCPU
- 2–4 GB RAM
- 40+ GB SSD
- public IPv4

This is an initial pilot size, not a final capacity commitment.

## Phase 2 — Domain/DNS

Use two DNS names, for example:

- `clinic.example.com`
- `api-clinic.example.com`

Both A records should point to the VPS public IP.

Do not proceed to HTTPS until DNS resolves to the server.

## Phase 3 — Basic server preparation

SSH to the server and update packages:

```bash
sudo apt update && sudo apt upgrade -y
```

Install Docker Engine and the Docker Compose plugin using Docker's official repository/instructions for your Ubuntu release.

Check:

```bash
docker --version
docker compose version
```

Configure a firewall. At minimum allow SSH, HTTP and HTTPS. Keep PostgreSQL 5432 closed to the Internet.

Typical UFW example:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## Phase 4 — Put your CURRENT Git project on the server

Preferred method:

```bash
git clone <YOUR_PRIVATE_REPOSITORY_URL> clinic-frontdesk
cd clinic-frontdesk
git checkout pilot-deployment-1
```

If you do not use a remote Git repository, securely copy the current project folder to the server instead.

Then copy the files from this deployment overlay into the project root:

- `docker-compose.pilot.yml`
- `Caddyfile.pilot`
- `.env.pilot.example`
- `scripts/backup_prod.sh`
- `scripts/smoke_prod.sh`
- `scripts/check_migrations.sh`

Do not replace `backend/app/models.py` or migration files with this overlay.

## Phase 5 — Create production secrets

```bash
cp .env.pilot.example .env.pilot
```

Generate secrets:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Use one value for `POSTGRES_PASSWORD` and a different value for `JWT_SECRET`.

Set real values in `.env.pilot`:

```env
APP_DOMAIN=clinic.example.com
API_DOMAIN=api-clinic.example.com
CORS_ORIGINS=https://clinic.example.com
```

Protect the file:

```bash
chmod 600 .env.pilot
```

Never commit `.env.pilot`.

## Phase 6 — Validate Compose before starting

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml config >/dev/null
```

If this command returns without an error, the Compose configuration is syntactically valid.

## Phase 7 — First production start

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml up -d --build
```

Watch startup:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml ps
```

Expected:

- `db` healthy
- `backend` healthy
- `frontend` running
- `caddy` running

If backend stops:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml logs backend --tail=100
```

If HTTPS fails:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml logs caddy --tail=100
```

## Phase 8 — Confirm migrations safely

Run:

```bash
./scripts/check_migrations.sh
```

The database current revision should match the repository head.

This guide intentionally does not hard-code `0006_audit_logs`, because your local project may now contain a newer migration for the Service schema correction.

Do not downgrade the production database just to match an old Git revision.

## Phase 9 — Open the application

Open:

```text
https://clinic.example.com
```

For a fresh production database you should receive the first-run setup flow. Create:

- clinic
- OWNER account

Then log in.

## Phase 10 — Pilot acceptance test

As OWNER:

1. Create/check clinic settings.
2. Add one doctor.
3. Add one service.
4. Add working hours.
5. Create a test patient.
6. Create an appointment.
7. Confirm/reschedule/cancel as appropriate.
8. Test waiting list/recovery.
9. Test Attention Queue.
10. Test Operational Dashboard.
11. Create a SECRETARY and verify role restrictions.
12. Check Audit Log.

Do not import a large real-patient dataset before this passes.

## Phase 11 — Production backup

After the first successful acceptance test:

```bash
./scripts/backup_prod.sh
```

Then copy the generated `.sql` backup off the VPS. A backup kept only on the same VPS is not sufficient protection.

## Phase 12 — Automated smoke test

```bash
./scripts/smoke_prod.sh
```

Expected final line:

```text
PILOT SMOKE TEST PASSED
```

## Phase 13 — First real clinic pilot

Start small:

- one clinic
- a limited number of staff accounts
- no WhatsApp/AI communication yet because Sprint 4 remains postponed
- secretary continues normal operational fallback during the first days

Observe authentication, appointment workflow, audit log, backups and server logs.

## Routine production commands

Status:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml ps
```

Logs:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml logs backend --tail=100
```

Backup:

```bash
./scripts/backup_prod.sh
```

Restart without deleting data:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml restart
```

Stop without deleting the database volume:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml down
```

Never use:

```bash
docker compose --env-file .env.pilot -f docker-compose.pilot.yml down -v
```

## Updating the pilot later

Use this sequence every time:

1. backup production database
2. copy backup off server
3. tag current working code
4. pull/checkout new tested release
5. inspect pending Alembic migration
6. rebuild
7. check migration head/current
8. smoke test

## Rollback principle

Code and data have different rollback mechanisms.

- Bad code, database unchanged: return to previous Git tag and rebuild.
- Bad migration/data change: assess migration and backup carefully before restoring.
- SQL restore returns the entire database to the backup snapshot and can discard newer records.

Never perform an emergency restore without first making a backup of the current damaged/live state.
