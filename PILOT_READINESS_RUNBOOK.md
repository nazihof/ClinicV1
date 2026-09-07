# Pilot Readiness Rehearsal — Sprint 4.5D

This rehearsal is the final gate before deploying the current clinic front-desk pilot to a real server. It does not add WhatsApp/Sprint 4 or Sprint 3F revenue intelligence.

## Goal
Prove that the current release can be started, checked, backed up, restored safely, and rolled back without guessing.

## 1. Freeze the known-good code

```cmd
git add .
git commit -m "Sprint 4.5D pilot readiness"
git tag sprint-4.5d-pilot-ready
```

## 2. Preflight

```cmd
scripts\pilot_preflight.cmd
```

Expected: `PRE-FLIGHT PASSED.`

## 3. Start the local stack

```cmd
docker compose up --build -d
```

Then:

```cmd
scripts\pilot_smoke_test.cmd
```

Expected: `SMOKE TEST PASSED.`

The new `/ready` endpoint verifies both PostgreSQL connectivity and Alembic revision `0006_audit_logs`. `/health` only proves the API process itself is alive.

## 4. Back up the live pilot database

```cmd
scripts\backup_db.cmd
dir backups
scripts\verify_backup.cmd backups\YOUR_BACKUP_FILE.sql
```

Do not continue to a production upgrade if the backup or verification fails.

## 5. Prove restore works without touching the live database

```cmd
scripts\restore_drill.cmd backups\YOUR_BACKUP_FILE.sql
```

The script creates a temporary PostgreSQL database named `clinic_restore_drill`, restores the backup there, queries clinics/users/patients/appointments, then deletes only that temporary database.

Expected: `RESTORE DRILL PASSED. Your live clinic database was not modified.`

## 6. Manual functional acceptance

Sign in as OWNER and verify:
- clinic administration opens;
- doctors/services/working hours are visible;
- patient creation works;
- appointment booking works;
- Attention Queue works;
- waiting-list recovery works;
- Operational Dashboard works;
- Audit Log records a new write action.

Then verify one SECRETARY account and one DOCTOR account still obey their role restrictions.

## 7. Production configuration rehearsal

Copy `.env.production.example` to `.env.production` only for the server/rehearsal and set unique secrets, real domains, PostgreSQL password and exact CORS origin.

Validate the Compose file without starting it:

```cmd
docker compose --env-file .env.production -f docker-compose.prod.yml config
```

Never commit `.env.production`.

## 8. Rollback rule

If a deployment fails before a database migration completes, stop the new release and return to the known-good Git tag.

If a migration completed but application behavior is bad, do not blindly run Alembic downgrade or delete volumes. First inspect the migration and determine whether it is backward compatible. Restore the database backup only when you intentionally want to return the data to the pre-upgrade snapshot.

Never use `docker compose down -v` during a normal upgrade or rollback.

## Pilot gate

Pilot deployment is approved only when all of these pass:
1. preflight;
2. smoke test;
3. backup verification;
4. safe restore drill;
5. OWNER/SECRETARY/DOCTOR role test;
6. booking/waiting-list/attention/dashboard/audit functional test;
7. production Compose validation;
8. a known-good Git tag exists.
