@echo off
setlocal
set FAIL=0

echo === Clinic Front-Desk Pilot Preflight ===
where docker >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Docker CLI not found.
  set FAIL=1
) else (
  echo [OK] Docker CLI found.
)

docker compose version >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Docker Compose is not available.
  set FAIL=1
) else (
  echo [OK] Docker Compose available.
)

if not exist .env (
  echo [FAIL] .env is missing.
  set FAIL=1
) else (
  findstr /B /C:"JWT_SECRET=" .env >nul
  if errorlevel 1 (
    echo [FAIL] JWT_SECRET is missing from .env.
    set FAIL=1
  ) else (
    echo [OK] .env contains JWT_SECRET.
  )
)

if not exist docker-compose.yml (
  echo [FAIL] docker-compose.yml not found. Run this from the project root.
  set FAIL=1
) else (
  echo [OK] docker-compose.yml found.
)

if %FAIL% NEQ 0 (
  echo.
  echo PRE-FLIGHT FAILED. Fix the items above before continuing.
  exit /b 1
)

echo.
echo PRE-FLIGHT PASSED.
exit /b 0
