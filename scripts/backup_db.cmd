@echo off
setlocal
if not exist backups mkdir backups
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set OUT=backups\clinic_%TS%.sql
echo Creating %OUT% ...
docker compose exec -T db pg_dump -U clinic -d clinic --clean --if-exists --no-owner --no-privileges > "%OUT%"
if errorlevel 1 (
  echo BACKUP FAILED.
  del "%OUT%" 2>nul
  exit /b 1
)
for %%A in ("%OUT%") do if %%~zA LSS 100 (
  echo BACKUP FAILED: output file is unexpectedly small.
  del "%OUT%" 2>nul
  exit /b 1
)
echo Backup created: %OUT%
