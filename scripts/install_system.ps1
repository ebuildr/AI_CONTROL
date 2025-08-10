# AI Control System - Complete Installation Script
# Automated setup for the entire AI Control System

param(
    [switch]$SkipOllama = $false,
    [switch]$SkipFirewall = $false,
    [switch]$SkipModels = $false,
    [string[]]$Models = @("gpt-oss:20b", "llama3.1:8b"),
    [switch]$Production = $false,
    [switch]$Force = $false
)

Write-Host "🤖 AI Control System - Complete Installation" -ForegroundColor Blue
Write-Host "===========================================" -ForegroundColor Blue

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (!$isAdmin -and !$SkipFirewall) {
    Write-Host "⚠️ Administrator privileges recommended for full installation" -ForegroundColor Yellow
    Write-Host "   Firewall configuration will be skipped" -ForegroundColor Gray
    $SkipFirewall = $true
}

$installationSteps = @()
$currentStep = 0

# Define installation steps
if (!$SkipOllama) { $installationSteps += "Ollama Installation" }
$installationSteps += "Python Environment"
$installationSteps += "Dependencies"
$installationSteps += "Browser Automation"
if (!$SkipFirewall) { $installationSteps += "Firewall Configuration" }
if (!$SkipModels) { $installationSteps += "AI Models" }
$installationSteps += "System Test"

$totalSteps = $installationSteps.Count

function Show-Progress {
    param([string]$StepName)
    $script:currentStep++
    Write-Host ""
    Write-Host "📋 Step $currentStep of $totalSteps`: $StepName" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Gray
}

function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Blue
    
    # Check Windows version
    $osInfo = Get-CimInstance Win32_OperatingSystem
    $osVersion = [Version]$osInfo.Version
    Write-Host "   OS: $($osInfo.Caption) ($($osInfo.Version))" -ForegroundColor Gray
    
    if ($osVersion.Major -lt 10) {
        Write-Host "❌ Windows 10 or later required" -ForegroundColor Red
        exit 1
    }
    
    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    Write-Host "   PowerShell: $psVersion" -ForegroundColor Gray
    
    if ($psVersion.Major -lt 5) {
        Write-Host "❌ PowerShell 5.0 or later required" -ForegroundColor Red
        exit 1
    }
    
    # Check available RAM
    $totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
    Write-Host "   RAM: $totalRAM GB" -ForegroundColor Gray
    
    if ($totalRAM -lt 8) {
        Write-Host "⚠️ Warning: Only $totalRAM GB RAM available. 8GB+ recommended" -ForegroundColor Yellow
    }
    
    # Check available disk space
    $disk = Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | Select-Object -First 1
    $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 1)
    Write-Host "   Free Disk Space: $freeSpaceGB GB" -ForegroundColor Gray
    
    if ($freeSpaceGB -lt 20) {
        Write-Host "⚠️ Warning: Only $freeSpaceGB GB free space. 50GB+ recommended" -ForegroundColor Yellow
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        Write-Host "   Python: $pythonVersion" -ForegroundColor Gray
    } catch {
        Write-Host "❌ Python not found. Please install Python 3.10+ first" -ForegroundColor Red
        Write-Host "   Download from: https://python.org/downloads" -ForegroundColor Gray
        exit 1
    }
    
    # Check Git
    try {
        $gitVersion = git --version 2>$null
        Write-Host "   Git: $gitVersion" -ForegroundColor Gray
    } catch {
        Write-Host "⚠️ Git not found. Some features may not work" -ForegroundColor Yellow
    }
    
    Write-Host "✅ Prerequisites check complete" -ForegroundColor Green
}

# Start installation
Test-Prerequisites

# Step 1: Ollama Installation
if (!$SkipOllama) {
    Show-Progress "Ollama Installation"
    
    try {
        & .\scripts\install_ollama.ps1 -Models $Models -Force:$Force
        if ($LASTEXITCODE -ne 0) {
            throw "Ollama installation failed"
        }
        Write-Host "✅ Ollama installation completed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Ollama installation failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   You can install manually later with: .\scripts\install_ollama.ps1" -ForegroundColor Yellow
    }
}

# Step 2: Python Environment
Show-Progress "Python Environment"

try {
    if (Test-Path ".venv") {
        if ($Force) {
            Write-Host "🔄 Removing existing virtual environment..." -ForegroundColor Yellow
            Remove-Item ".venv" -Recurse -Force
        } else {
            Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
        }
    }
    
    if (!(Test-Path ".venv")) {
        Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Blue
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            throw "Virtual environment creation failed"
        }
    }
    
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Blue
    & .venv\Scripts\Activate.ps1
    
    Write-Host "✅ Python environment ready" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Python environment setup failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Dependencies
Show-Progress "Dependencies"

try {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Blue
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed"
    }
    
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Dependency installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Try: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Step 4: Browser Automation
Show-Progress "Browser Automation"

try {
    Write-Host "🎭 Installing Playwright browsers..." -ForegroundColor Blue
    playwright install chromium
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Browser automation ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Browser installation had issues - web features may be limited" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "⚠️ Browser automation setup failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   Web browsing features may not work properly" -ForegroundColor Gray
}

# Step 5: Firewall Configuration
if (!$SkipFirewall) {
    Show-Progress "Firewall Configuration"
    
    try {
        Write-Host "🛡️ Configuring Windows Firewall..." -ForegroundColor Blue
        & .\scripts\setup_firewall.ps1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Firewall configured for network access" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Firewall configuration had issues" -ForegroundColor Yellow
            Write-Host "   You may need to configure manually" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "⚠️ Firewall configuration failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   Network access may be limited" -ForegroundColor Gray
    }
}

# Step 6: AI Models
if (!$SkipModels) {
    Show-Progress "AI Models"
    
    try {
        Write-Host "🧠 Verifying AI models..." -ForegroundColor Blue
        
        # Check if Ollama is running
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
            $installedModels = & ollama list 2>$null
            
            if ($installedModels -and $installedModels -notlike "*No models*") {
                Write-Host "✅ AI models are available" -ForegroundColor Green
                $modelLines = $installedModels.Split("`n") | Where-Object { $_ -and $_ -notlike "NAME*" -and $_.Trim() }
                Write-Host "   Models: $($modelLines.Count) installed" -ForegroundColor Gray
            } else {
                Write-Host "⚠️ No models found - you may need to install them manually" -ForegroundColor Yellow
                Write-Host "   Run: ollama pull gpt-oss:20b" -ForegroundColor Gray
            }
            
        } catch {
            Write-Host "⚠️ Ollama not responding - models cannot be verified" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "⚠️ Model verification failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 7: System Test
Show-Progress "System Test"

try {
    Write-Host "🧪 Running system tests..." -ForegroundColor Blue
    & .\scripts\test_system.ps1 -SkipWeb
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ System tests passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Some tests failed - system may have limitations" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "⚠️ System testing failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create desktop shortcut
try {
    Write-Host "🔗 Creating desktop shortcuts..." -ForegroundColor Blue
    
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $currentDir = Get-Location
    
    # Create batch file for easy startup
    $batchContent = @"
@echo off
cd /d "$currentDir"
powershell -ExecutionPolicy Bypass -File "scripts\start_stack.ps1"
pause
"@
    
    $batchFile = Join-Path $currentDir "Start_AI_Control.bat"
    $batchContent | Out-File -FilePath $batchFile -Encoding ASCII
    
    # Create shortcut
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut("$desktopPath\AI Control System.lnk")
    $shortcut.TargetPath = $batchFile
    $shortcut.WorkingDirectory = $currentDir
    $shortcut.Description = "Start AI Control System"
    $shortcut.Save()
    
    Write-Host "✅ Desktop shortcut created" -ForegroundColor Green
    
} catch {
    Write-Host "⚠️ Could not create desktop shortcut" -ForegroundColor Yellow
}

# Installation Summary
Write-Host ""
Write-Host "🎉 Installation Complete!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

# Check what was installed
$summary = @()

if (Test-Path ".venv") {
    $summary += "✅ Python virtual environment"
}

$ollamaPath = where.exe ollama 2>$null
if ($ollamaPath) {
    $summary += "✅ Ollama AI platform"
}

try {
    $models = & ollama list 2>$null
    if ($models -and $models -notlike "*No models*") {
        $modelCount = ($models.Split("`n") | Where-Object { $_ -and $_ -notlike "NAME*" -and $_.Trim() }).Count
        $summary += "✅ AI models ($modelCount installed)"
    }
} catch {}

try {
    $firewallRules = Get-NetFirewallRule -DisplayName "*AI Control System*" -ErrorAction SilentlyContinue
    if ($firewallRules) {
        $summary += "✅ Firewall configuration"
    }
} catch {}

foreach ($item in $summary) {
    Write-Host "   $item" -ForegroundColor White
}

# Next Steps
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Start the system:" -ForegroundColor White
Write-Host "   .\scripts\start_stack.ps1" -ForegroundColor Gray

Write-Host "2. Access the web interface:" -ForegroundColor White
Write-Host "   http://localhost:8001" -ForegroundColor Gray

Write-Host "3. Test the installation:" -ForegroundColor White
Write-Host "   .\scripts\test_system.ps1" -ForegroundColor Gray

if (!$SkipModels -and !$Models) {
    Write-Host "4. Install additional models:" -ForegroundColor White
    Write-Host "   ollama pull gpt-oss:120b" -ForegroundColor Gray
}

# Configuration recommendations
Write-Host ""
Write-Host "⚙️ Configuration Tips:" -ForegroundColor Yellow

$totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)

if ($totalRAM -ge 64) {
    Write-Host "   🎯 With $totalRAM GB RAM, you can run GPT-OSS 120B for best quality" -ForegroundColor Green
} elseif ($totalRAM -ge 32) {
    Write-Host "   🎯 With $totalRAM GB RAM, GPT-OSS 20B is recommended" -ForegroundColor Green
} elseif ($totalRAM -ge 16) {
    Write-Host "   🎯 With $totalRAM GB RAM, stick to 8B models for best performance" -ForegroundColor Yellow
} else {
    Write-Host "   ⚠️ With $totalRAM GB RAM, consider upgrading for better performance" -ForegroundColor Yellow
}

# Network information
try {
    $networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
        $_.IPAddress -ne "127.0.0.1" -and $_.IPAddress -notlike "169.254.*" 
    }
    
    if ($networkAdapters) {
        Write-Host ""
        Write-Host "🌐 Network Access:" -ForegroundColor Cyan
        foreach ($adapter in $networkAdapters) {
            $adapterName = (Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex).Name
            Write-Host "   $adapterName`: http://$($adapter.IPAddress):8001" -ForegroundColor White
            
            if ($adapter.IPAddress -like "100.*") {
                Write-Host "     ^ Meshnet IP - Access from anywhere!" -ForegroundColor Green
            }
        }
    }
} catch {
    # Ignore network info errors
}

Write-Host ""
Write-Host "📚 Documentation: README.md" -ForegroundColor Cyan
Write-Host "🆘 Support: Check README.md for troubleshooting" -ForegroundColor Cyan

if ($Production) {
    Write-Host ""
    Write-Host "🔒 Production Mode Enabled" -ForegroundColor Yellow
    Write-Host "   Remember to configure authentication and HTTPS" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Happy AI controlling! 🤖✨" -ForegroundColor Green
