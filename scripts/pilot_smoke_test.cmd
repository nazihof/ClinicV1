@echo off
setlocal
set FAIL=0

echo === Clinic Front-Desk Pilot Smoke Test ===

docker compose ps

docker compose exec -T backend alembic current | findstr /C:"0006_audit_logs" >nul
if errorlevel 1 (
  echo [FAIL] Alembic is not at 0006_audit_logs.
  set FAIL=1
) else (
  echo [OK] Alembic revision is 0006_audit_logs.
)

powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health'; if($r.status -ne 'ok'){exit 1}; Write-Host '[OK] /health:' $r.version" 
if errorlevel 1 (
  echo [FAIL] /health failed.
  set FAIL=1
)

powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8000/ready'; if($r.status -ne 'ready'){exit 1}; Write-Host '[OK] /ready database=' $r.database ' alembic=' $r.alembic" 
if errorlevel 1 (
  echo [FAIL] /ready failed.
  set FAIL=1
)

powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:3000'; if($r.StatusCode -ne 200){exit 1}; Write-Host '[OK] Frontend HTTP 200'" 
if errorlevel 1 (
  echo [FAIL] Frontend check failed.
  set FAIL=1
)

if %FAIL% NEQ 0 (
  echo.
  echo SMOKE TEST FAILED.
  exit /b 1
)

echo.
echo SMOKE TEST PASSED.
exit /b 0
