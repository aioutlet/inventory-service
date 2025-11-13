# Inventory Service - Run with Dapr

Write-Host "Starting Inventory Service with Dapr..."
Write-Host "Service will be available at: http://localhost:1005"
Write-Host "Dapr HTTP endpoint: http://localhost:3505"
Write-Host "Dapr gRPC endpoint: localhost:50005"
Write-Host ""

dapr run `
  --app-id inventory-service `
  --app-port 1005 `
  --dapr-http-port 3505 `
  --dapr-grpc-port 50005 `
  --log-level warn `
  --config ./.dapr/config.yaml `
  --resources-path ./.dapr/components `
  -- python run.py
