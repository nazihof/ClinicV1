@echo off
setlocal
if "%~1"=="" (
  echo Usage: scripts\restore_drill.cmd backups\clinic_YYYYMMDD_HHMMSS.sql
  exit /b 2
)
if not exist "%~1" (
  echo Backup file not found: %~1
  exit /b 2
)

set TESTDB=clinic_restore_drill

echo === SAFE RESTORE DRILL ===
echo This DOES NOT overwrite your live clinic database.
echo Temporary database: %TESTDB%

docker compose exec -T db psql -U clinic -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS %TESTDB%;" >nul
if errorlevel 1 goto :fail

docker compose exec -T db psql -U clinic -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE %TESTDB%;" >nul
if errorlevel 1 goto :fail

type "%~1" | docker compose exec -T db psql -U clinic -d %TESTDB% -v ON_ERROR_STOP=1 >nul
if errorlevel 1 goto :failcleanup

echo [OK] Backup restored into temporary database.

docker compose exec -T db psql -U clinic -d %TESTDB% -t -A -c "SELECT 'clinics='||count(*) FROM clinics; SELECT 'users='||count(*) FROM users; SELECT 'patients='||count(*) FROM patients; SELECT 'appointments='||count(*) FROM appointments;"
if errorlevel 1 goto :failcleanup

echo [OK] Core tables can be queried after restore.

docker compose exec -T db psql -U clinic -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE %TESTDB%;" >nul
if errorlevel 1 goto :fail

echo [OK] Temporary restore database removed.
echo.
echo RESTORE DRILL PASSED. Your live clinic database was not modified.
exit /b 0

:failcleanup
echo [FAIL] Restore drill failed. Cleaning up temporary database...
docker compose exec -T db psql -U clinic -d postgres -c "DROP DATABASE IF EXISTS %TESTDB%;" >nul 2>nul
exit /b 1

:fail
echo [FAIL] Restore drill failed before validation.
exit /b 1
