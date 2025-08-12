# AI Outlet - Inventory Service Seeder Script (PowerShell)
# This script provides convenient commands for seeding the inventory database

param(
    [Parameter(Position=0)]
    [string]$Command = "",
    
    [Parameter(Position=1)]
    [string]$FilePath = "",
    
    [switch]$Verbose,
    [switch]$NoSummary
)

$ErrorActionPreference = "Stop"

# Get script directory and service directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServiceDir = Split-Path -Parent $ScriptDir

# Colors for output (if supported)
function Write-Header {
    Write-Host "🌱 AI Outlet - Inventory Service Seeder" -ForegroundColor Blue
    Write-Host "===============================================" -ForegroundColor Blue
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

function Test-Dependencies {
    Write-Info "Checking dependencies..."
    
    # Check Go installation
    try {
        $goVersion = & go version
        Write-Success "Go found: $goVersion"
    }
    catch {
        Write-Error "Go is not installed or not in PATH"
        exit 1
    }
    
    # Check if we're in the right directory
    if (-not (Test-Path "$ServiceDir\go.mod")) {
        Write-Error "Not in inventory service directory or go.mod not found"
        exit 1
    }
    
    Write-Success "Inventory service directory confirmed"
}

function Build-Seeder {
    Write-Info "Building seeder..."
    Push-Location $ServiceDir
    
    try {
        # Create bin directory if it doesn't exist
        if (-not (Test-Path "bin")) {
            New-Item -ItemType Directory -Name "bin" | Out-Null
        }
        
        & go build -o "bin\seed.exe" ".\cmd\seed"
        if ($LASTEXITCODE -ne 0) {
            throw "Build failed"
        }
        Write-Success "Seeder built successfully"
    }
    catch {
        Write-Error "Failed to build seeder: $_"
        exit 1
    }
    finally {
        Pop-Location
    }
}

function Show-Usage {
    Write-Host "Usage: .\seed.ps1 [COMMAND] [OPTIONS]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  build                  Build the seeder binary"
    Write-Host "  seed                   Run seeder with default data"
    Write-Host "  seed-file <file>       Run seeder with custom JSON file"
    Write-Host "  clear                  Clear all data"
    Write-Host "  clear-and-seed         Clear data and reseed with default data"
    Write-Host "  clear-and-seed-file    Clear data and reseed with custom JSON file"
    Write-Host "  summary                Show database summary without seeding"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Verbose               Enable verbose logging"
    Write-Host "  -NoSummary             Disable summary after seeding"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\seed.ps1 seed                                    # Seed with default data"
    Write-Host "  .\seed.ps1 seed-file inventory-data.json          # Seed with custom file"
    Write-Host "  .\seed.ps1 clear-and-seed -Verbose               # Clear and reseed with verbose output"
    Write-Host "  .\seed.ps1 seed -NoSummary                        # Seed without showing summary"
    Write-Host ""
}

function Invoke-Seeder {
    param([string[]]$Arguments)
    
    Push-Location $ServiceDir
    
    try {
        $seederArgs = @()
        
        # Add verbose flag if specified
        if ($Verbose) {
            $seederArgs += "-verbose"
        }
        
        # Add no-summary flag if specified
        if ($NoSummary) {
            $seederArgs += "-summary=false"
        }
        
        # Add command arguments
        $seederArgs += $Arguments
        
        Write-Info "Running seeder with args: $($seederArgs -join ' ')"
        
        if ($Verbose) {
            & ".\bin\seed.exe" @seederArgs
        } else {
            & ".\bin\seed.exe" @seederArgs 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Seeder failed. Run with -Verbose for more details."
                exit 1
            }
        }
    }
    finally {
        Pop-Location
    }
}

# Main script logic
Write-Header

switch ($Command.ToLower()) {
    "build" {
        Test-Dependencies
        Build-Seeder
    }
    
    "seed" {
        Test-Dependencies
        Build-Seeder
        Invoke-Seeder @()
    }
    
    "seed-file" {
        if ([string]::IsNullOrEmpty($FilePath)) {
            Write-Error "Please provide a JSON file path"
            Show-Usage
            exit 1
        }
        
        if (-not (Test-Path $FilePath)) {
            Write-Error "File not found: $FilePath"
            exit 1
        }
        
        Test-Dependencies
        Build-Seeder
        Invoke-Seeder @("-file", $FilePath)
    }
    
    "clear" {
        Test-Dependencies
        Build-Seeder
        Invoke-Seeder @("-clear")
    }
    
    "clear-and-seed" {
        Test-Dependencies
        Build-Seeder
        Invoke-Seeder @("-clear")
    }
    
    "clear-and-seed-file" {
        if ([string]::IsNullOrEmpty($FilePath)) {
            Write-Error "Please provide a JSON file path"
            Show-Usage
            exit 1
        }
        
        if (-not (Test-Path $FilePath)) {
            Write-Error "File not found: $FilePath"
            exit 1
        }
        
        Test-Dependencies
        Build-Seeder
        Invoke-Seeder @("-clear", "-file", $FilePath)
    }
    
    "summary" {
        Test-Dependencies
        Build-Seeder
        Write-Info "Showing database summary..."
        Push-Location $ServiceDir
        try {
            & ".\bin\seed.exe" "-summary"
        }
        finally {
            Pop-Location
        }
    }
    
    default {
        Show-Usage
        exit 0
    }
}

Write-Success "Operation completed!"
