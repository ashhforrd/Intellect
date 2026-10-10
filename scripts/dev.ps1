[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RootDir ".env"
$FrontendDir = Join-Path $RootDir "frontend"
$Processes = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()

function Get-EnvFileValue {
    param([Parameter(Mandatory)][string]$Key)

    if (-not (Test-Path $EnvFile)) { return "" }
    $line = Get-Content $EnvFile | Where-Object { $_ -match "^\s*$([regex]::Escape($Key))=" } | Select-Object -Last 1
    if (-not $line) { return "" }
    return (($line -split "=", 2)[1]).Trim().Trim('"').Trim("'")
}

function Test-ConfiguredValue {
    param([Parameter(Mandatory)][string]$Key)

    $value = Get-EnvFileValue $Key
    return -not [string]::IsNullOrWhiteSpace($value) -and
        $value -notmatch "[<>]" -and
        $value -notmatch "replace-with"
}

function Assert-LastCommand {
    param([Parameter(Mandatory)][string]$Label)

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) { throw "Required command not found: $Name" }
    return $command.Source
}

function Assert-PortAvailable {
    param([Parameter(Mandatory)][int]$Port)

    $listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    if ($listeners.Port -contains $Port) {
        throw "Port $Port is already in use. Stop the existing service and run this script again."
    }
}

function Start-DevelopmentProcess {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory
    )

    Write-Host "Starting $Name..."
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -NoNewWindow `
        -PassThru
    $Processes.Add($process)
    return $process
}

function Stop-DevelopmentProcesses {
    if ($Processes.Count -eq 0) { return }

    Write-Host "`nStopping Intellect development services..."
    foreach ($process in $Processes) {
        if (-not $process.HasExited) {
            & taskkill.exe /PID $process.Id /T /F 2>$null | Out-Null
        }
    }
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $RootDir ".env.example") $EnvFile
    Write-Host "Created .env from .env.example."
    Write-Host "Fill in OPENAI_API_KEY and any storage or queue settings, then run this script again."
    exit 0
}

$requiredSettings = @("OPENAI_API_KEY", "DATABASE_URL")
if ((Get-EnvFileValue "JOB_QUEUE_BACKEND") -eq "sqs") {
    $requiredSettings += "SQS_QUEUE_URL"
}
if ((Get-EnvFileValue "JOB_QUEUE_BACKEND") -eq "redis") {
    $requiredSettings += "REDIS_URL"
}
if ((Get-EnvFileValue "STORAGE_BACKEND") -eq "s3") {
    $requiredSettings += "S3_BUCKET_NAME"
}
if ((Get-EnvFileValue "STORAGE_BACKEND") -eq "supabase") {
    $requiredSettings += @(
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_STORAGE_BUCKET"
    )
}
$missingSettings = @($requiredSettings | Where-Object { -not (Test-ConfiguredValue $_) })
if ($missingSettings.Count -gt 0) {
    Write-Error ("Complete these settings in .env before starting Intellect:`n- " + ($missingSettings -join "`n- "))
}

try {
    $uv = Assert-Command "uv"
    $npm = Assert-Command "npm.cmd"
    $null = Assert-Command "node"
    $null = Assert-Command "docker"
    $null = Assert-Command "tesseract"

    & docker compose version | Out-Null
    Assert-LastCommand "Docker Compose validation"
    Assert-PortAvailable 8000
    Assert-PortAvailable 5173

    Set-Location $RootDir

    Write-Host "Syncing Python dependencies..."
    & $uv sync --locked
    Assert-LastCommand "Python dependency sync"

    & $uv run python -c "import sys; raise SystemExit(sys.version_info < (3, 12))"
    if ($LASTEXITCODE -ne 0) { throw "Python 3.12 or newer is required." }

    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Host "Installing frontend dependencies..."
        & $npm --prefix $FrontendDir ci
        Assert-LastCommand "Frontend dependency installation"
    }

    $databaseUrl = Get-EnvFileValue "DATABASE_URL"
    if ($databaseUrl -match "localhost|127\.0\.0\.1") {
        Write-Host "Starting PostgreSQL..."
        & docker compose up -d --wait database
        Assert-LastCommand "PostgreSQL startup"
    }

    if ((Get-EnvFileValue "JOB_QUEUE_BACKEND") -eq "redis") {
        Write-Host "Starting Redis..."
        & docker compose up -d --wait redis
        Assert-LastCommand "Redis startup"
    }

    Write-Host "Applying database migrations..."
    & $uv run alembic upgrade head
    Assert-LastCommand "Database migration"

    $api = Start-DevelopmentProcess `
        -Name "API on http://127.0.0.1:8000" `
        -FilePath $uv `
        -ArgumentList @("run", "uvicorn", "personal_document_intelligence_api.main:app", "--reload") `
        -WorkingDirectory $RootDir

    $worker = Start-DevelopmentProcess `
        -Name "document worker" `
        -FilePath $uv `
        -ArgumentList @("run", "python", "-m", "personal_document_intelligence_api.workers.runner") `
        -WorkingDirectory $RootDir

    $frontend = Start-DevelopmentProcess `
        -Name "frontend on http://localhost:5173" `
        -FilePath $npm `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory $FrontendDir

    Write-Host "`nIntellect is running. Press Ctrl+C to stop the API, worker, and frontend."

    while ($true) {
        foreach ($service in @(
            @{ Name = "api"; Process = $api },
            @{ Name = "worker"; Process = $worker },
            @{ Name = "frontend"; Process = $frontend }
        )) {
            $service.Process.Refresh()
            if ($service.Process.HasExited) {
                throw "$($service.Name) stopped unexpectedly (exit code $($service.Process.ExitCode))."
            }
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    Stop-DevelopmentProcesses
}
