# AI Control System - Start Stack Script
# Starts Ollama and FastAPI services

param(
    [switch]$Headless = $true,
    [switch]$NoOllama = $false,
    [string]$Port = "8001",
    [string]$Host = "0.0.0.0"
)

Write-Host "🚀 Starting AI Control System..." -ForegroundColor Green

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if ($isAdmin) {
    Write-Host "✅ Running with Administrator privileges" -ForegroundColor Green
} else {
    Write-Host "⚠️ Not running as Administrator - some features may be limited" -ForegroundColor Yellow
}

# Create logs directory
$logDir = "logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "📁 Created logs directory" -ForegroundColor Blue
}

# Function to check if port is available
function Test-Port {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

# Function to kill process using port
function Stop-ProcessOnPort {
    param([int]$Port)
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        foreach ($processId in $processes) {
            if ($processId -and $processId -ne 0) {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "🔄 Stopping process $($process.Name) (PID: $processId) using port $Port" -ForegroundColor Yellow
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 2
                }
            }
        }
    } catch {
        Write-Host "⚠️ Could not stop processes on port $Port" -ForegroundColor Yellow
    }
}

# Check and free up ports
$ports = @($Port, 11434)
foreach ($p in $ports) {
    if (!(Test-Port $p)) {
        Write-Host "🔄 Port $p is in use, attempting to free it..." -ForegroundColor Yellow
        Stop-ProcessOnPort $p
        Start-Sleep -Seconds 3
        
        if (!(Test-Port $p)) {
            Write-Host "❌ Could not free port $p - please check manually" -ForegroundColor Red
            Write-Host "   Run: netstat -ano | findstr :$p" -ForegroundColor Gray
            # Continue anyway
        }
    }
}

# Start Ollama server if not disabled
if (!$NoOllama) {
    Write-Host "🧠 Starting Ollama server..." -ForegroundColor Blue
    
    # Check if Ollama is installed
    $ollamaPath = where.exe ollama 2>$null
    if (!$ollamaPath) {
        Write-Host "❌ Ollama not found in PATH. Please install Ollama first:" -ForegroundColor Red
        Write-Host "   Download from: https://ollama.com/download" -ForegroundColor Gray
        Write-Host "   Or run: .\scripts\install_ollama.ps1" -ForegroundColor Gray
        exit 1
    }
    
    # Set Ollama environment variables
    $env:OLLAMA_HOST = "0.0.0.0:11434"
    $env:OLLAMA_ORIGINS = "*"
    $env:OLLAMA_NUM_PARALLEL = "1"
    
    # Check if Ollama is already running
    $ollamaRunning = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($ollamaRunning) {
        Write-Host "🔄 Ollama already running, restarting..." -ForegroundColor Yellow
        Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }
    
    # Start Ollama in background
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Write-Host "✅ Ollama server started" -ForegroundColor Green
    
    # Wait for Ollama to be ready
    Write-Host "⏳ Waiting for Ollama to be ready..." -ForegroundColor Blue
    $ollamaReady = $false
    $attempts = 0
    while (!$ollamaReady -and $attempts -lt 30) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
            $ollamaReady = $true
            Write-Host "✅ Ollama is ready" -ForegroundColor Green
        } catch {
            Start-Sleep -Seconds 2
            $attempts++
            Write-Host "⏳ Waiting for Ollama... ($attempts/30)" -ForegroundColor Yellow
        }
    }
    
    if (!$ollamaReady) {
        Write-Host "❌ Ollama failed to start within timeout" -ForegroundColor Red
        Write-Host "   Check if port 11434 is available" -ForegroundColor Gray
        Write-Host "   Check logs: ollama logs" -ForegroundColor Gray
    }
}

# Activate Python virtual environment
Write-Host "🐍 Activating Python virtual environment..." -ForegroundColor Blue
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        & .venv\Scripts\Activate.ps1
        Write-Host "📦 Installing dependencies..." -ForegroundColor Blue
        pip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Dependencies installed" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Install Playwright browsers if needed
Write-Host "🎭 Checking Playwright browsers..." -ForegroundColor Blue
try {
    python -c "from playwright.sync_api import sync_playwright; print('Playwright available')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        # Check if browsers are installed
        $browserCheck = python -c "
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        browser.close()
        print('Browsers ready')
except Exception as e:
    print('Need browsers:', str(e))
" 2>$null
        
        if ($browserCheck -like "*Need browsers*") {
            Write-Host "📦 Installing Playwright browsers..." -ForegroundColor Blue
            playwright install chromium
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Playwright browsers installed" -ForegroundColor Green
            } else {
                Write-Host "⚠️ Playwright browser installation failed - web features may not work" -ForegroundColor Yellow
            }
        } else {
            Write-Host "✅ Playwright browsers ready" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "⚠️ Playwright not available - web features may not work" -ForegroundColor Yellow
}

# Start FastAPI server
Write-Host "🌐 Starting FastAPI server..." -ForegroundColor Blue
Write-Host "   Host: $Host" -ForegroundColor Gray
Write-Host "   Port: $Port" -ForegroundColor Gray

# Set environment variables
$env:PYTHONPATH = (Get-Location).Path
$env:ENVIRONMENT = "development"

# Start the server
$logFile = "logs\ai_control_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

try {
    if ($Headless) {
        Write-Host "🚀 Starting server in headless mode..." -ForegroundColor Blue
        Write-Host "   Logs: $logFile" -ForegroundColor Gray
        
        # Start in background
        $job = Start-Job -ScriptBlock {
            param($Host, $Port, $LogFile)
            Set-Location $using:PWD
            & .venv\Scripts\Activate.ps1
            $env:PYTHONPATH = (Get-Location).Path
            uvicorn app.main:app --host $Host --port $Port --reload 2>&1 | Tee-Object -FilePath $LogFile
        } -ArgumentList $Host, $Port, $logFile
        
        Write-Host "✅ FastAPI server started (Job ID: $($job.Id))" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌍 Access points:" -ForegroundColor Cyan
        Write-Host "   Local:          http://localhost:$Port" -ForegroundColor White
        Write-Host "   Network (LAN):  http://$(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Ethernet*', 'Wi-Fi*' | Select-Object -First 1 -ExpandProperty IPAddress):$Port" -ForegroundColor White
        
        # Check for Meshnet IP
        $meshnetIP = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "100.*" } | Select-Object -First 1 -ExpandProperty IPAddress
        if ($meshnetIP) {
            Write-Host "   Meshnet:        http://$($meshnetIP):$Port" -ForegroundColor White
        }
        
        Write-Host ""
        Write-Host "📊 Monitoring:" -ForegroundColor Cyan
        Write-Host "   Health:         http://localhost:$Port/health" -ForegroundColor White
        Write-Host "   API Docs:       http://localhost:$Port/docs" -ForegroundColor White
        Write-Host "   Logs:           $logFile" -ForegroundColor White
        Write-Host ""
        Write-Host "🛑 To stop: .\scripts\stop_stack.ps1" -ForegroundColor Yellow
        Write-Host "📊 To monitor: .\scripts\monitor_stack.ps1" -ForegroundColor Yellow
        
    } else {
        Write-Host "🚀 Starting server in interactive mode..." -ForegroundColor Blue
        uvicorn app.main:app --host $Host --port $Port --reload
    }
    
} catch {
    Write-Host "❌ Failed to start FastAPI server: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 AI Control System startup complete!" -ForegroundColor Green
