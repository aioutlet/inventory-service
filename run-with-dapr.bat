@echo off
REM =============================================================================
REM Inventory Service - Run with Dapr Sidecar (Windows)
REM =============================================================================

setlocal

echo ========================================
echo Inventory Service with Dapr
echo ========================================
echo.

REM Check if Dapr CLI is installed
where dapr >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Dapr CLI not found!
    echo Please install Dapr CLI: https://docs.dapr.io/getting-started/install-dapr-cli/
    exit /b 1
)

REM Configuration
set APP_ID=inventory-service
set APP_PORT=5002
set DAPR_HTTP_PORT=3502
set DAPR_GRPC_PORT=50002
set COMPONENTS_PATH=./.dapr/components
set CONFIG_PATH=./.dapr/config.yaml

echo [INFO] Configuration:
echo   App ID: %APP_ID%
echo   App Port: %APP_PORT%
echo   Dapr HTTP Port: %DAPR_HTTP_PORT%
echo   Dapr gRPC Port: %DAPR_GRPC_PORT%
echo   Components Path: %COMPONENTS_PATH%
echo   Config Path: %CONFIG_PATH%
echo.

REM Check if components directory exists
if not exist "%COMPONENTS_PATH%" (
    echo [WARNING] Components directory not found: %COMPONENTS_PATH%
    exit /b 1
)

REM Check if config file exists
if not exist "%CONFIG_PATH%" (
    echo [WARNING] Config file not found: %CONFIG_PATH%
    exit /b 1
)

echo [INFO] Starting Inventory Service with Dapr sidecar...
echo.

REM Run with Dapr
dapr run ^
  --app-id %APP_ID% ^
  --app-port %APP_PORT% ^
  --dapr-http-port %DAPR_HTTP_PORT% ^
  --dapr-grpc-port %DAPR_GRPC_PORT% ^
  --components-path %COMPONENTS_PATH% ^
  --config %CONFIG_PATH% ^
  --log-level info ^
  -- python run.py

endlocal
