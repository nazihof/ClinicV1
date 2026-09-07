@echo off
setlocal
if "%~1"=="" (
  echo Usage: scripts\restore_db.cmd backups\clinic_YYYYMMDD_HHMMSS.sql
  exit /b 2
)
if not exist "%~1" (
  echo Backup file not found: %~1
  exit /b 2
)
echo WARNING: This restores database content from %~1.
set /p CONFIRM=Type RESTORE to continue: 
if /I not "%CONFIRM%"=="RESTORE" exit /b 1

type "%~1" | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U clinic -d clinic
if errorlevel 1 (
  echo RESTORE FAILED.
  exit /b 1
)
echo Restore completed.
