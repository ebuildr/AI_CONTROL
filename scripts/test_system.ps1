# AI Control System - System Test Script
# Comprehensive testing of all components

param(
    [string]$Host = "localhost",
    [string]$Port = "8001",
    [switch]$SkipModels = $false,
    [switch]$SkipWeb = $false,
    [switch]$Verbose = $false
)

Write-Host "🧪 AI Control System - Comprehensive Test Suite" -ForegroundColor Blue
Write-Host "===============================================" -ForegroundColor Blue

$ErrorActionPreference = "Continue"
$testResults = @{}
$totalTests = 0
$passedTests = 0

function Test-Component {
    param(
        [string]$Name,
        [scriptblock]$TestScript
    )
    
    $script:totalTests++
    Write-Host "🔍 Testing: $Name" -ForegroundColor Yellow
    
    try {
        $result = & $TestScript
        if ($result) {
            Write-Host "   ✅ PASS: $Name" -ForegroundColor Green
            $script:testResults[$Name] = "PASS"
            $script:passedTests++
        } else {
            Write-Host "   ❌ FAIL: $Name" -ForegroundColor Red
            $script:testResults[$Name] = "FAIL"
        }
    } catch {
        Write-Host "   ❌ ERROR: $Name - $($_.Exception.Message)" -ForegroundColor Red
        $script:testResults[$Name] = "ERROR: $($_.Exception.Message)"
    }
    
    if ($Verbose) {
        Write-Host ""
    }
}

# Test 1: System Requirements
Test-Component "System Requirements" {
    $ram = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
    $disk = Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | Measure-Object -Property FreeSpace -Sum | Select-Object -ExpandProperty Sum
    $diskGB = [math]::Round($disk / 1GB, 1)
    
    Write-Host "     RAM: $ram GB" -ForegroundColor Gray
    Write-Host "     Free Disk: $diskGB GB" -ForegroundColor Gray
    
    return ($ram -ge 8 -and $diskGB -ge 10)
}

# Test 2: Python Environment
Test-Component "Python Environment" {
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "     Python: $pythonVersion" -ForegroundColor Gray
        
        if (Test-Path ".venv") {
            Write-Host "     Virtual environment: Found" -ForegroundColor Gray
            return $true
        } else {
            Write-Host "     Virtual environment: Not found" -ForegroundColor Gray
            return $false
        }
    } catch {
        Write-Host "     Python: Not found" -ForegroundColor Gray
        return $false
    }
}

# Test 3: Required Dependencies
Test-Component "Python Dependencies" {
    if (!(Test-Path ".venv")) {
        return $false
    }
    
    & .venv\Scripts\Activate.ps1
    
    $requiredPackages = @("fastapi", "uvicorn", "ollama", "playwright", "psutil")
    $allInstalled = $true
    
    foreach ($package in $requiredPackages) {
        try {
            $result = pip show $package 2>$null
            if ($result) {
                Write-Host "     ✅ $package" -ForegroundColor Gray
            } else {
                Write-Host "     ❌ $package" -ForegroundColor Gray
                $allInstalled = $false
            }
        } catch {
            Write-Host "     ❌ $package" -ForegroundColor Gray
            $allInstalled = $false
        }
    }
    
    return $allInstalled
}

# Test 4: Ollama Installation
Test-Component "Ollama Installation" {
    $ollamaPath = where.exe ollama 2>$null
    if ($ollamaPath) {
        $version = & ollama --version 2>$null
        Write-Host "     Path: $ollamaPath" -ForegroundColor Gray
        Write-Host "     Version: $version" -ForegroundColor Gray
        return $true
    } else {
        Write-Host "     Ollama not found in PATH" -ForegroundColor Gray
        return $false
    }
}

# Test 5: Ollama Service
Test-Component "Ollama Service" {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "     Service: Running" -ForegroundColor Gray
        return $true
    } catch {
        Write-Host "     Service: Not responding" -ForegroundColor Gray
        return $false
    }
}

# Test 6: Ollama Models
if (!$SkipModels) {
    Test-Component "Ollama Models" {
        try {
            $models = & ollama list 2>$null
            if ($models -and $models -notlike "*No models*") {
                $modelLines = $models.Split("`n") | Where-Object { $_ -and $_ -notlike "NAME*" -and $_.Trim() }
                Write-Host "     Models found: $($modelLines.Count)" -ForegroundColor Gray
                foreach ($model in $modelLines | Select-Object -First 3) {
                    Write-Host "       - $($model.Split()[0])" -ForegroundColor Gray
                }
                return $true
            } else {
                Write-Host "     No models installed" -ForegroundColor Gray
                return $false
            }
        } catch {
            return $false
        }
    }
}

# Test 7: Port Availability
Test-Component "Port Availability" {
    $ports = @($Port, 11434)
    $allAvailable = $true
    
    foreach ($testPort in $ports) {
        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $testPort)
            $listener.Start()
            $listener.Stop()
            Write-Host "     Port $testPort`: Available" -ForegroundColor Gray
        } catch {
            Write-Host "     Port $testPort`: In use or blocked" -ForegroundColor Gray
            $allAvailable = $false
        }
    }
    
    return $allAvailable
}

# Test 8: Firewall Rules
Test-Component "Firewall Rules" {
    try {
        $rules = Get-NetFirewallRule -DisplayName "*AI Control System*" -ErrorAction SilentlyContinue
        if ($rules) {
            Write-Host "     Firewall rules: $($rules.Count) found" -ForegroundColor Gray
            return $true
        } else {
            Write-Host "     Firewall rules: Not configured" -ForegroundColor Gray
            return $false
        }
    } catch {
        Write-Host "     Firewall rules: Cannot check" -ForegroundColor Gray
        return $false
    }
}

# Test 9: Network Configuration
Test-Component "Network Configuration" {
    try {
        $adapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
            $_.IPAddress -ne "127.0.0.1" -and $_.IPAddress -notlike "169.254.*" 
        }
        
        $lanIP = $adapters | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*" } | Select-Object -First 1
        $meshnetIP = $adapters | Where-Object { $_.IPAddress -like "100.*" } | Select-Object -First 1
        
        if ($lanIP) {
            Write-Host "     LAN IP: $($lanIP.IPAddress)" -ForegroundColor Gray
        }
        
        if ($meshnetIP) {
            Write-Host "     Meshnet IP: $($meshnetIP.IPAddress)" -ForegroundColor Gray
        }
        
        return ($adapters.Count -gt 0)
    } catch {
        return $false
    }
}

# Test 10: Start FastAPI Server (if not running)
Test-Component "FastAPI Server Startup" {
    try {
        # Check if already running
        $response = Invoke-RestMethod -Uri "http://$Host`:$Port/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response) {
            Write-Host "     Server already running" -ForegroundColor Gray
            return $true
        }
    } catch {
        # Server not running, try to start it
    }
    
    # Try to start server in background for testing
    try {
        & .venv\Scripts\Activate.ps1
        $env:PYTHONPATH = (Get-Location).Path
        
        $job = Start-Job -ScriptBlock {
            param($Host, $Port, $WorkingDir)
            Set-Location $WorkingDir
            & .venv\Scripts\Activate.ps1
            $env:PYTHONPATH = $WorkingDir
            uvicorn app.main:app --host $Host --port $Port --log-level warning
        } -ArgumentList $Host, $Port, (Get-Location).Path
        
        # Wait for server to start
        Start-Sleep -Seconds 10
        
        $response = Invoke-RestMethod -Uri "http://$Host`:$Port/health" -TimeoutSec 5 -ErrorAction Stop
        
        # Stop the test server
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        
        Write-Host "     Server started successfully" -ForegroundColor Gray
        return $true
        
    } catch {
        # Clean up job if it exists
        try {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        } catch {}
        
        Write-Host "     Server failed to start" -ForegroundColor Gray
        return $false
    }
}

# Test 11: Web Browser Automation (if not skipped)
if (!$SkipWeb) {
    Test-Component "Browser Automation" {
        try {
            & .venv\Scripts\Activate.ps1
            
            # Test Playwright
            $playwrightTest = python -c "
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('data:text/html,<h1>Test</h1>')
        content = page.content()
        browser.close()
        print('Playwright: OK')
except Exception as e:
    print(f'Playwright: Error - {e}')
"
            
            Write-Host "     $playwrightTest" -ForegroundColor Gray
            return ($playwrightTest -like "*OK*")
            
        } catch {
            Write-Host "     Browser automation: Failed" -ForegroundColor Gray
            return $false
        }
    }
}

# Test 12: AI Chat Functionality (if server is available)
Test-Component "AI Chat Functionality" {
    try {
        # First check if server is running
        $healthResponse = Invoke-RestMethod -Uri "http://$Host`:$Port/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if (!$healthResponse) {
            Write-Host "     Server not available for testing" -ForegroundColor Gray
            return $false
        }
        
        # Get available models
        $modelsResponse = Invoke-RestMethod -Uri "http://$Host`:$Port/models" -TimeoutSec 10 -ErrorAction Stop
        if (!$modelsResponse.models -or $modelsResponse.models.Count -eq 0) {
            Write-Host "     No models available" -ForegroundColor Gray
            return $false
        }
        
        $testModel = $modelsResponse.models[0]
        Write-Host "     Testing with model: $testModel" -ForegroundColor Gray
        
        # Test chat endpoint
        $chatRequest = @{
            model = $testModel
            prompt = "Say 'test successful' if you can understand this message"
            temperature = 0.1
            stream = $false
        }
        
        $chatResponse = Invoke-RestMethod -Uri "http://$Host`:$Port/chat" -Method POST -Body ($chatRequest | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30 -ErrorAction Stop
        
        if ($chatResponse.response) {
            Write-Host "     AI response received" -ForegroundColor Gray
            return $true
        } else {
            Write-Host "     No AI response" -ForegroundColor Gray
            return $false
        }
        
    } catch {
        Write-Host "     Chat test failed: $($_.Exception.Message)" -ForegroundColor Gray
        return $false
    }
}

# Test 13: PC Control Functions
Test-Component "PC Control Functions" {
    try {
        # Test basic system info
        $cpu = Get-WmiObject -Class Win32_Processor | Select-Object -First 1
        $memory = Get-WmiObject -Class Win32_ComputerSystem
        
        if ($cpu -and $memory) {
            Write-Host "     System info accessible" -ForegroundColor Gray
            
            # Test process listing
            $processes = Get-Process | Select-Object -First 5
            if ($processes) {
                Write-Host "     Process listing works" -ForegroundColor Gray
                return $true
            }
        }
        
        return $false
    } catch {
        return $false
    }
}

# Summary
Write-Host ""
Write-Host "📊 Test Results Summary" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $($totalTests - $passedTests)" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round(($passedTests / $totalTests) * 100, 1))%" -ForegroundColor Yellow

Write-Host ""
Write-Host "📋 Detailed Results:" -ForegroundColor Cyan
foreach ($test in $testResults.Keys) {
    $result = $testResults[$test]
    $color = if ($result -eq "PASS") { "Green" } else { "Red" }
    Write-Host "   $test`: $result" -ForegroundColor $color
}

# Recommendations
Write-Host ""
Write-Host "💡 Recommendations:" -ForegroundColor Yellow

if ($testResults["Ollama Installation"] -ne "PASS") {
    Write-Host "   🔧 Install Ollama: .\scripts\install_ollama.ps1" -ForegroundColor Gray
}

if ($testResults["Python Dependencies"] -ne "PASS") {
    Write-Host "   🐍 Install dependencies: pip install -r requirements.txt" -ForegroundColor Gray
}

if ($testResults["Firewall Rules"] -ne "PASS") {
    Write-Host "   🛡️ Configure firewall: .\scripts\setup_firewall.ps1" -ForegroundColor Gray
}

if ($testResults["Ollama Models"] -ne "PASS" -and !$SkipModels) {
    Write-Host "   📚 Install models: ollama pull gpt-oss:20b" -ForegroundColor Gray
}

if ($passedTests -eq $totalTests) {
    Write-Host ""
    Write-Host "🎉 All tests passed! Your AI Control System is ready to use." -ForegroundColor Green
    Write-Host "   Start the system: .\scripts\start_stack.ps1" -ForegroundColor Gray
    Write-Host "   Access web interface: http://localhost:$Port" -ForegroundColor Gray
} elseif ($passedTests / $totalTests -gt 0.7) {
    Write-Host ""
    Write-Host "✅ Most tests passed. System should work with minor limitations." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Multiple test failures. Please address the issues above." -ForegroundColor Red
}

Write-Host ""
Write-Host "🔧 For detailed setup help, see README.md or run individual scripts." -ForegroundColor Cyan
