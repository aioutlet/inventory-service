# AI Outlet - Inventory Service Database Setup Script (PowerShell)
# This script sets up the complete development environment

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Get script directory and service directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServiceDir = Split-Path -Parent $ScriptDir

function Write-Header {
    Write-Host "🚀 AI Outlet - Inventory Service Setup" -ForegroundColor Blue
    Write-Host "=======================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

Write-Header

Push-Location $ServiceDir

try {
    # 1. Check if .env exists
    if (-not (Test-Path ".env")) {
        Write-Info "Creating .env file from .env.example..."
        Copy-Item ".env.example" ".env"
        Add-Content ".env" "`n# Database URL (for migrations and seeding)"
        Add-Content ".env" "DATABASE_URL=postgres://postgres:password@localhost:5432/inventory_db?sslmode=disable"
        Write-Success ".env file created"
    } else {
        Write-Info ".env file already exists"
    }

    # 2. Start PostgreSQL and Redis
    Write-Info "Starting PostgreSQL and Redis containers..."
    & docker-compose up -d postgres redis
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start containers"
    }

    # 3. Wait for databases to be healthy
    Write-Info "Waiting for databases to be ready..."
    Start-Sleep -Seconds 10

    # Check if containers are running
    $containers = & docker-compose ps
    if (-not ($containers -match "Up.*postgres")) {
        Write-Error "PostgreSQL container failed to start"
        exit 1
    }

    if (-not ($containers -match "Up.*redis")) {
        Write-Error "Redis container failed to start"
        exit 1
    }

    Write-Success "Database containers are running"

    # 4. Wait for PostgreSQL to fully initialize
    Write-Info "Waiting for PostgreSQL to fully initialize..."
    for ($i = 1; $i -le 30; $i++) {
        try {
            & docker exec inventory-service-postgres-1 pg_isready -U postgres | Out-Null
            if ($LASTEXITCODE -eq 0) {
                break
            }
        } catch {
            # Continue waiting
        }
        
        if ($i -eq 30) {
            Write-Error "PostgreSQL failed to become ready"
            exit 1
        }
        Start-Sleep -Seconds 1
    }

    Write-Success "PostgreSQL is ready"

    # 5. Run migrations
    Write-Info "Running database migrations..."
    try {
        Get-Content "migrations\001_initial_schema.up.sql" | & docker exec -i inventory-service-postgres-1 psql -U postgres -d inventory_db | Out-Null
        Write-Success "Database migrations completed"
    } catch {
        Write-Warning "Migrations may have already been run (this is normal)"
    }

    # 6. Build seeder
    Write-Info "Building seeder..."
    if (-not (Test-Path "bin")) {
        New-Item -ItemType Directory -Name "bin" | Out-Null
    }
    
    & go build -o "bin\seed.exe" ".\cmd\seed"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to build seeder"
    }
    Write-Success "Seeder built successfully"

    # 7. Run seeder
    Write-Info "Seeding database with sample data..."
    & ".\bin\seed.exe"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to seed database"
    }
    Write-Success "Database seeded successfully"

    # 8. Show status
    Write-Host ""
    Write-Info "Setup completed! Here's what's running:"
    & docker-compose ps

    Write-Host ""
    Write-Info "Database summary:"
    & docker exec inventory-service-postgres-1 psql -U postgres -d inventory_db -c @"
SELECT 
    COUNT(*) as products,
    SUM(quantity_available) as total_stock,
    COUNT(*) FILTER (WHERE quantity_available <= reorder_level) as low_stock_items,
    COUNT(*) FILTER (WHERE quantity_available = 0) as out_of_stock_items
FROM inventory_items;
"@

    Write-Host ""
    Write-Success "🎉 Inventory service database is ready for development!"
    Write-Info "You can now run: .\bin\inventory-service.exe"
    Write-Host ""

} catch {
    Write-Error "Setup failed: $_"
    exit 1
} finally {
    Pop-Location
}
