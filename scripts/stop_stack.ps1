# AI Control System - Stop Stack Script
# Stops all AI Control System services

param(
    [switch]$Force = $false,
    [switch]$KeepOllama = $false
)

Write-Host "🛑 Stopping AI Control System..." -ForegroundColor Yellow

# Function to stop processes gracefully
function Stop-ProcessGracefully {
    param(
        [string]$ProcessName,
        [int]$TimeoutSeconds = 10
    )
    
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "🔄 Stopping $ProcessName processes..." -ForegroundColor Blue
        
        foreach ($process in $processes) {
            try {
                if (!$process.HasExited) {
                    Write-Host "   Stopping PID $($process.Id)..." -ForegroundColor Gray
                    
                    if ($Force) {
                        $process.Kill()
                        Write-Host "   ✅ Force killed $($process.Id)" -ForegroundColor Yellow
                    } else {
                        # Try graceful shutdown first
                        $process.CloseMainWindow() | Out-Null
                        
                        # Wait for graceful shutdown
                        $waited = 0
                        while (!$process.HasExited -and $waited -lt $TimeoutSeconds) {
                            Start-Sleep -Milliseconds 500
                            $waited += 0.5
                        }
                        
                        # Force kill if still running
                        if (!$process.HasExited) {
                            Write-Host "   ⏰ Timeout reached, force killing..." -ForegroundColor Yellow
                            $process.Kill()
                        }
                        
                        Write-Host "   ✅ Stopped $($process.Id)" -ForegroundColor Green
                    }
                }
            } catch {
                Write-Host "   ⚠️ Could not stop process $($process.Id): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "ℹ️ No $ProcessName processes found" -ForegroundColor Gray
    }
}

# Function to stop processes using specific ports
function Stop-ProcessOnPort {
    param(
        [int]$Port,
        [string]$Description = ""
    )
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connections) {
            Write-Host "🔄 Stopping processes on port $Port $(if($Description){"($Description)"})..." -ForegroundColor Blue
            
            foreach ($conn in $connections) {
                $processId = $conn.OwningProcess
                if ($processId -and $processId -ne 0) {
                    try {
                        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                        if ($process) {
                            Write-Host "   Stopping $($process.Name) (PID: $processId)" -ForegroundColor Gray
                            
                            if ($Force) {
                                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                            } else {
                                # Try graceful first
                                $process.CloseMainWindow() | Out-Null
                                Start-Sleep -Seconds 3
                                
                                if (!$process.HasExited) {
                                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                                }
                            }
                            
                            Write-Host "   ✅ Stopped process on port $Port" -ForegroundColor Green
                        }
                    } catch {
                        Write-Host "   ⚠️ Could not stop process $processId" -ForegroundColor Red
                    }
                }
            }
        } else {
            Write-Host "ℹ️ No processes found on port $Port" -ForegroundColor Gray
        }
    } catch {
        Write-Host "⚠️ Error checking port $Port`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Stop FastAPI server (uvicorn)
Write-Host "🌐 Stopping FastAPI server..." -ForegroundColor Blue
Stop-ProcessGracefully -ProcessName "python" -TimeoutSeconds 5

# Also check port 8001 specifically
Stop-ProcessOnPort -Port 8001 -Description "FastAPI"

# Stop background jobs
$jobs = Get-Job | Where-Object { $_.Name -like "*AI*" -or $_.State -eq "Running" }
if ($jobs) {
    Write-Host "🔄 Stopping background jobs..." -ForegroundColor Blue
    foreach ($job in $jobs) {
        Write-Host "   Stopping job: $($job.Name)" -ForegroundColor Gray
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ Background jobs stopped" -ForegroundColor Green
}

# Stop Ollama server (unless keeping it)
if (!$KeepOllama) {
    Write-Host "🧠 Stopping Ollama server..." -ForegroundColor Blue
    Stop-ProcessGracefully -ProcessName "ollama" -TimeoutSeconds 10
    Stop-ProcessOnPort -Port 11434 -Description "Ollama"
} else {
    Write-Host "🧠 Keeping Ollama server running" -ForegroundColor Yellow
}

# Stop any remaining Python processes that might be related
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or 
    $_.CommandLine -like "*app.main*" -or
    $_.CommandLine -like "*ai_control*"
}

if ($pythonProcesses) {
    Write-Host "🐍 Stopping related Python processes..." -ForegroundColor Blue
    foreach ($process in $pythonProcesses) {
        try {
            Write-Host "   Stopping Python process: $($process.Id)" -ForegroundColor Gray
            if ($Force) {
                $process.Kill()
            } else {
                $process.CloseMainWindow() | Out-Null
                Start-Sleep -Seconds 2
                if (!$process.HasExited) {
                    $process.Kill()
                }
            }
            Write-Host "   ✅ Stopped Python process" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️ Could not stop Python process: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Clean up any browser processes that might be left running
$browserProcesses = Get-Process -Name "chrome", "chromium", "msedge", "firefox" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*playwright*" -or 
    $_.CommandLine -like "*selenium*" -or
    $_.CommandLine -like "*headless*"
}

if ($browserProcesses) {
    Write-Host "🌐 Stopping browser automation processes..." -ForegroundColor Blue
    foreach ($process in $browserProcesses) {
        try {
            Write-Host "   Stopping browser process: $($process.Name) ($($process.Id))" -ForegroundColor Gray
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "   ⚠️ Could not stop browser process" -ForegroundColor Red
        }
    }
    Write-Host "✅ Browser processes cleaned up" -ForegroundColor Green
}

# Check if ports are now free
Write-Host "🔍 Verifying ports are free..." -ForegroundColor Blue
$portsToCheck = @(8001)
if (!$KeepOllama) {
    $portsToCheck += 11434
}

foreach ($port in $portsToCheck) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $port)
        $listener.Start()
        $listener.Stop()
        Write-Host "   ✅ Port $port is free" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Port $port may still be in use" -ForegroundColor Yellow
    }
}

# Clean up log files if requested
if ($Force) {
    Write-Host "🧹 Cleaning up log files..." -ForegroundColor Blue
    try {
        $logFiles = Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue
        if ($logFiles) {
            $oldLogs = $logFiles | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
            if ($oldLogs) {
                $oldLogs | Remove-Item -Force
                Write-Host "   ✅ Cleaned up $($oldLogs.Count) old log files" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "   ⚠️ Could not clean up log files" -ForegroundColor Yellow
    }
}

# Final status
Write-Host ""
Write-Host "✅ AI Control System stopped" -ForegroundColor Green

if (!$KeepOllama) {
    Write-Host "   🧠 Ollama server stopped" -ForegroundColor Gray
} else {
    Write-Host "   🧠 Ollama server still running" -ForegroundColor Gray
}

Write-Host "   🌐 FastAPI server stopped" -ForegroundColor Gray
Write-Host "   🐍 Python processes stopped" -ForegroundColor Gray
Write-Host "   🌐 Browser automation stopped" -ForegroundColor Gray

Write-Host ""
Write-Host "🚀 To restart: .\scripts\start_stack.ps1" -ForegroundColor Cyan
