# AI Control System - Ollama Installation Script
# Downloads and installs Ollama on Windows

param(
    [switch]$Force = $false,
    [string[]]$Models = @("gpt-oss:20b", "llama3.1:8b"),
    [switch]$SkipModels = $false
)

Write-Host "🧠 Ollama Installation Script for AI Control System" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if ($isAdmin) {
    Write-Host "✅ Running with Administrator privileges" -ForegroundColor Green
} else {
    Write-Host "⚠️ Not running as Administrator - installation may require elevation" -ForegroundColor Yellow
}

# Check if Ollama is already installed
$ollamaPath = where.exe ollama 2>$null
if ($ollamaPath -and !$Force) {
    Write-Host "✅ Ollama is already installed at: $ollamaPath" -ForegroundColor Green
    $version = & ollama --version 2>$null
    if ($version) {
        Write-Host "   Version: $version" -ForegroundColor Gray
    }
    
    $response = Read-Host "Do you want to continue with model installation? (y/N)"
    if ($response -notlike "y*") {
        Write-Host "ℹ️ Installation cancelled by user" -ForegroundColor Yellow
        exit 0
    }
    $SkipInstall = $true
} else {
    $SkipInstall = $false
}

if (!$SkipInstall) {
    Write-Host "📥 Downloading Ollama..." -ForegroundColor Blue
    
    # Create temp directory
    $tempDir = Join-Path $env:TEMP "ollama_install"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    # Download URL for Ollama Windows installer
    $downloadUrl = "https://ollama.com/download/windows"
    $installerPath = Join-Path $tempDir "OllamaSetup.exe"
    
    try {
        Write-Host "   Downloading from: $downloadUrl" -ForegroundColor Gray
        Write-Host "   Saving to: $installerPath" -ForegroundColor Gray
        
        # Use Invoke-WebRequest to download
        $progressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Host "✅ Download completed" -ForegroundColor Green
        
        # Verify file was downloaded
        if (!(Test-Path $installerPath)) {
            throw "Downloaded file not found"
        }
        
        $fileSize = (Get-Item $installerPath).Length
        Write-Host "   File size: $([math]::Round($fileSize / 1MB, 2)) MB" -ForegroundColor Gray
        
    } catch {
        Write-Host "❌ Download failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Please download manually from: https://ollama.com/download" -ForegroundColor Yellow
        exit 1
    }
    
    # Install Ollama
    Write-Host "🚀 Installing Ollama..." -ForegroundColor Blue
    
    try {
        if ($isAdmin) {
            # Run installer silently if admin
            Write-Host "   Running silent installation..." -ForegroundColor Gray
            $process = Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait -PassThru
        } else {
            # Run installer with UAC prompt if not admin
            Write-Host "   Running installation (UAC prompt may appear)..." -ForegroundColor Gray
            $process = Start-Process -FilePath $installerPath -Wait -PassThru
        }
        
        if ($process.ExitCode -eq 0) {
            Write-Host "✅ Ollama installation completed" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Installation completed with exit code: $($process.ExitCode)" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Please run the installer manually: $installerPath" -ForegroundColor Yellow
        exit 1
    }
    
    # Clean up installer
    try {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    } catch {
        # Ignore cleanup errors
    }
    
    # Refresh PATH
    Write-Host "🔄 Refreshing environment variables..." -ForegroundColor Blue
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    
    # Verify installation
    Start-Sleep -Seconds 3
    $ollamaPath = where.exe ollama 2>$null
    if ($ollamaPath) {
        Write-Host "✅ Ollama successfully installed at: $ollamaPath" -ForegroundColor Green
        $version = & ollama --version 2>$null
        if ($version) {
            Write-Host "   Version: $version" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️ Ollama installation may need a system restart" -ForegroundColor Yellow
        Write-Host "   Try restarting PowerShell or your computer" -ForegroundColor Gray
    }
}

# Start Ollama service
if ($ollamaPath) {
    Write-Host "🚀 Starting Ollama service..." -ForegroundColor Blue
    
    # Check if already running
    $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($ollamaProcess) {
        Write-Host "✅ Ollama is already running" -ForegroundColor Green
    } else {
        try {
            # Start Ollama in background
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Write-Host "✅ Ollama service started" -ForegroundColor Green
            
            # Wait for service to be ready
            Write-Host "⏳ Waiting for Ollama to be ready..." -ForegroundColor Yellow
            $ready = $false
            $attempts = 0
            while (!$ready -and $attempts -lt 30) {
                try {
                    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
                    $ready = $true
                    Write-Host "✅ Ollama is ready!" -ForegroundColor Green
                } catch {
                    Start-Sleep -Seconds 2
                    $attempts++
                    Write-Host "   Waiting... ($attempts/30)" -ForegroundColor Gray
                }
            }
            
            if (!$ready) {
                Write-Host "⚠️ Ollama service may not be fully ready yet" -ForegroundColor Yellow
            }
            
        } catch {
            Write-Host "⚠️ Could not start Ollama service: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "   Try running manually: ollama serve" -ForegroundColor Gray
        }
    }
}

# Install AI models
if (!$SkipModels -and $Models.Count -gt 0) {
    Write-Host "📚 Installing AI models..." -ForegroundColor Blue
    Write-Host "   Models to install: $($Models -join ', ')" -ForegroundColor Gray
    
    foreach ($model in $Models) {
        Write-Host "📥 Pulling model: $model" -ForegroundColor Blue
        
        try {
            # Check if model already exists
            $existingModels = & ollama list 2>$null
            if ($existingModels -and $existingModels -match [regex]::Escape($model)) {
                Write-Host "   ✅ Model $model already installed" -ForegroundColor Green
                continue
            }
            
            # Pull the model
            Write-Host "   This may take several minutes depending on model size..." -ForegroundColor Gray
            
            $pullProcess = Start-Process -FilePath "ollama" -ArgumentList "pull", $model -Wait -PassThru -NoNewWindow
            
            if ($pullProcess.ExitCode -eq 0) {
                Write-Host "   ✅ Successfully installed $model" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Failed to install $model (Exit code: $($pullProcess.ExitCode))" -ForegroundColor Red
            }
            
        } catch {
            Write-Host "   ❌ Error installing $model`: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Display installed models
Write-Host "📋 Checking installed models..." -ForegroundColor Blue
try {
    $modelList = & ollama list 2>$null
    if ($modelList) {
        Write-Host "✅ Installed models:" -ForegroundColor Green
        Write-Host $modelList -ForegroundColor Gray
    } else {
        Write-Host "ℹ️ No models found or Ollama not responding" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Could not list models" -ForegroundColor Yellow
}

# Configuration recommendations
Write-Host ""
Write-Host "⚙️ Configuration Recommendations:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

$totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
Write-Host "🖥️ System RAM: $totalRAM GB" -ForegroundColor White

if ($totalRAM -ge 64) {
    Write-Host "✅ Excellent! You can run all models including GPT-OSS 120B" -ForegroundColor Green
    Write-Host "   Recommended: Use GPT-OSS 120B for best quality" -ForegroundColor Gray
} elseif ($totalRAM -ge 32) {
    Write-Host "✅ Good! You can run GPT-OSS 20B and smaller models" -ForegroundColor Green
    Write-Host "   Recommended: Use GPT-OSS 20B for good balance" -ForegroundColor Gray
} elseif ($totalRAM -ge 16) {
    Write-Host "⚠️ Limited RAM. Stick to 8B models or smaller" -ForegroundColor Yellow
    Write-Host "   Recommended: Use Llama 3.1 8B" -ForegroundColor Gray
} else {
    Write-Host "❌ Low RAM. May have issues with larger models" -ForegroundColor Red
    Write-Host "   Recommended: Upgrade RAM or use cloud models" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🌐 Environment Variables (optional):" -ForegroundColor Cyan
Write-Host "   OLLAMA_HOST=0.0.0.0:11434  # Allow network access" -ForegroundColor Gray
Write-Host "   OLLAMA_NUM_PARALLEL=1      # Limit concurrent requests" -ForegroundColor Gray
Write-Host "   OLLAMA_NUM_GPU=0           # Use CPU only (for stability)" -ForegroundColor Gray

Write-Host ""
Write-Host "🧪 Testing Ollama installation..." -ForegroundColor Blue

try {
    # Test API endpoint
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✅ Ollama API is responding" -ForegroundColor Green
    
    # Test with a simple query if models are available
    $models = & ollama list 2>$null
    if ($models -and $models -notlike "*No models*") {
        Write-Host "✅ Models are available for use" -ForegroundColor Green
    }
    
} catch {
    Write-Host "⚠️ Ollama API test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   The service may need more time to start" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎉 Ollama installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Configure firewall: .\scripts\setup_firewall.ps1" -ForegroundColor Gray
Write-Host "   2. Start AI Control System: .\scripts\start_stack.ps1" -ForegroundColor Gray
Write-Host "   3. Access web interface: http://localhost:8001" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Useful commands:" -ForegroundColor Cyan
Write-Host "   ollama list                # List installed models" -ForegroundColor Gray
Write-Host "   ollama pull <model>        # Install a model" -ForegroundColor Gray
Write-Host "   ollama rm <model>          # Remove a model" -ForegroundColor Gray
Write-Host "   ollama serve               # Start Ollama server" -ForegroundColor Gray
