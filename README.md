# Clinic Front-Desk — Sprint 4.5D

## Final Pilot Readiness / Deployment Rehearsal

Sprint 4.5D builds on Sprint 4.5C. It deliberately adds no new business feature, no Sprint 4 WhatsApp/communication layer, and no Sprint 3F revenue intelligence.

Backend version: `4.5.4-pilot.1`
Alembic head: `0006_audit_logs` (no new migration)

## What this sprint adds

### 1. Real readiness probe
`GET /ready` verifies:
- FastAPI can reach PostgreSQL;
- the database has an Alembic version;
- the current revision is exactly `0006_audit_logs`.

It returns HTTP 503 when the database or migration state is not ready. Production Docker now uses `/ready` for the backend health check.

### 2. Pilot preflight script

```cmd
scripts\pilot_preflight.cmd
```

Checks Docker, Docker Compose, `.env`, `JWT_SECRET`, and project-root structure before a rehearsal.

### 3. Automated smoke test

```cmd
scripts\pilot_smoke_test.cmd
```

Checks:
- Alembic head;
- backend `/health`;
- backend `/ready`;
- frontend HTTP 200.

### 4. Safe restore drill

```cmd
scripts\restore_drill.cmd backups\YOUR_BACKUP.sql
```

This restores your backup into a disposable PostgreSQL database, validates important tables, and deletes the temporary database. It does **not** replace your working clinic database.

### 5. Pilot readiness runbook
See `PILOT_READINESS_RUNBOOK.md` for the complete deployment rehearsal and rollback rules.

## Upgrade from Sprint 4.5C

First create and verify a backup:

```cmd
scripts\backup_db.cmd
scripts\verify_backup.cmd backups\YOUR_BACKUP_FILE.sql
```

Then:

```cmd
docker compose down
```

Do not use `docker compose down -v`.

Copy Sprint 4.5D over the same project folder, keeping `.env` and the Docker database volume, then:

```cmd
docker compose up --build
```

Verify:

```cmd
docker compose exec backend alembic current
```

Expected: `0006_audit_logs (head)`

Open:

`http://127.0.0.1:8000/health`

Expected version: `4.5.4-pilot.1`

Then open:

`http://127.0.0.1:8000/ready`

Expected:

```json
{"status":"ready","database":"ok","alembic":"0006_audit_logs","version":"4.5.4-pilot.1"}
```

## Recommended acceptance sequence

```cmd
scripts\pilot_preflight.cmd
scripts\pilot_smoke_test.cmd
scripts\backup_db.cmd
scripts\verify_backup.cmd backups\YOUR_BACKUP_FILE.sql
scripts\restore_drill.cmd backups\YOUR_BACKUP_FILE.sql
```

After these pass, perform the manual OWNER/SECRETARY/DOCTOR and appointment workflow checks in `PILOT_READINESS_RUNBOOK.md`.

## Scope boundary
Passing Sprint 4.5D means the current build has completed the technical pilot-readiness rehearsal defined for this project. It is not a claim of healthcare regulatory certification, formal penetration testing, disaster-recovery SLA, or production compliance certification.
