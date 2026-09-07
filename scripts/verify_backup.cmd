@echo off
setlocal
if "%~1"=="" (
  echo Usage: scripts\verify_backup.cmd backups\clinic_YYYYMMDD_HHMMSS.sql
  exit /b 2
)
if not exist "%~1" (
  echo Backup file not found: %~1
  exit /b 2
)
findstr /C:"CREATE TABLE" "%~1" >nul
if errorlevel 1 (
  echo Verification FAILED: CREATE TABLE statements not found.
  exit /b 1
)
findstr /C:"COPY public.clinics" "%~1" >nul
if errorlevel 1 (
  echo Verification warning: clinic data COPY statement not found. This may be an empty database backup.
  exit /b 1
)
echo Backup looks structurally valid: %~1
