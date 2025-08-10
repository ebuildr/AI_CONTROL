# AI Control System - Firewall Setup Script
# Configures Windows Firewall rules for AI Control System

param(
    [switch]$Remove = $false,
    [string]$Port = "8001",
    [string]$OllamaPort = "11434"
)

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (!$isAdmin) {
    Write-Host "❌ This script must be run as Administrator" -ForegroundColor Red
    Write-Host "   Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "🛡️ Configuring Windows Firewall for AI Control System..." -ForegroundColor Blue

# Define rule names
$rules = @{
    "AI Control System - Web Interface" = @{
        Port = $Port
        Protocol = "TCP"
        Direction = "Inbound"
        Description = "Allow access to AI Control System web interface"
    }
    "AI Control System - Ollama API" = @{
        Port = $OllamaPort
        Protocol = "TCP"
        Direction = "Inbound"
        Description = "Allow access to Ollama API server"
    }
    "AI Control System - Web Interface Outbound" = @{
        Port = $Port
        Protocol = "TCP"
        Direction = "Outbound"
        Description = "Allow outbound connections from AI Control System"
    }
    "AI Control System - Ollama Outbound" = @{
        Port = $OllamaPort
        Protocol = "TCP"
        Direction = "Outbound"
        Description = "Allow outbound connections from Ollama"
    }
}

if ($Remove) {
    Write-Host "🗑️ Removing firewall rules..." -ForegroundColor Yellow
    
    foreach ($ruleName in $rules.Keys) {
        try {
            $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            if ($existingRule) {
                Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction Stop
                Write-Host "   ✅ Removed rule: $ruleName" -ForegroundColor Green
            } else {
                Write-Host "   ℹ️ Rule not found: $ruleName" -ForegroundColor Gray
            }
        } catch {
            Write-Host "   ❌ Failed to remove rule $ruleName`: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "✅ Firewall rules removal complete" -ForegroundColor Green
    exit 0
}

# Add firewall rules
Write-Host "➕ Adding firewall rules..." -ForegroundColor Blue

foreach ($ruleName in $rules.Keys) {
    $rule = $rules[$ruleName]
    
    try {
        # Remove existing rule if it exists
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if ($existingRule) {
            Write-Host "   🔄 Updating existing rule: $ruleName" -ForegroundColor Yellow
            Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        }
        
        # Create new rule
        $params = @{
            DisplayName = $ruleName
            Direction = $rule.Direction
            LocalPort = $rule.Port
            Protocol = $rule.Protocol
            Action = "Allow"
            Description = $rule.Description
            Enabled = "True"
        }
        
        New-NetFirewallRule @params -ErrorAction Stop | Out-Null
        Write-Host "   ✅ Added rule: $ruleName (Port $($rule.Port)/$($rule.Direction))" -ForegroundColor Green
        
    } catch {
        Write-Host "   ❌ Failed to add rule $ruleName`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Add rules for common web browsing automation
Write-Host "🌐 Adding web browsing automation rules..." -ForegroundColor Blue

$webRules = @{
    "AI Control System - HTTP Outbound" = @{
        Port = "80"
        Protocol = "TCP"
        Direction = "Outbound"
        Description = "Allow HTTP connections for web browsing automation"
    }
    "AI Control System - HTTPS Outbound" = @{
        Port = "443"
        Protocol = "TCP" 
        Direction = "Outbound"
        Description = "Allow HTTPS connections for web browsing automation"
    }
    "AI Control System - DNS Outbound" = @{
        Port = "53"
        Protocol = "UDP"
        Direction = "Outbound"
        Description = "Allow DNS resolution for web browsing"
    }
}

foreach ($ruleName in $webRules.Keys) {
    $rule = $webRules[$ruleName]
    
    try {
        # Remove existing rule if it exists
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if ($existingRule) {
            Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        }
        
        # Create new rule
        $params = @{
            DisplayName = $ruleName
            Direction = $rule.Direction
            LocalPort = $rule.Port
            Protocol = $rule.Protocol
            Action = "Allow"
            Description = $rule.Description
            Enabled = "True"
        }
        
        New-NetFirewallRule @params -ErrorAction Stop | Out-Null
        Write-Host "   ✅ Added web rule: $ruleName (Port $($rule.Port))" -ForegroundColor Green
        
    } catch {
        Write-Host "   ❌ Failed to add web rule $ruleName`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Configure Windows Defender exclusions for better performance
Write-Host "🛡️ Configuring Windows Defender exclusions..." -ForegroundColor Blue

$exclusions = @(
    (Get-Location).Path  # Current directory
    "$env:USERPROFILE\.ollama"  # Ollama models directory
    "$env:LOCALAPPDATA\Programs\ollama"  # Ollama installation
)

foreach ($exclusion in $exclusions) {
    try {
        if (Test-Path $exclusion) {
            Add-MpPreference -ExclusionPath $exclusion -ErrorAction Stop
            Write-Host "   ✅ Added exclusion: $exclusion" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️ Path not found: $exclusion" -ForegroundColor Yellow
        }
    } catch {
        if ($_.Exception.Message -like "*already exists*") {
            Write-Host "   ℹ️ Exclusion already exists: $exclusion" -ForegroundColor Gray
        } else {
            Write-Host "   ⚠️ Could not add exclusion $exclusion`: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# Get network information for verification
Write-Host "🌐 Network Information:" -ForegroundColor Cyan

try {
    # Get local IP addresses
    $networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
        $_.IPAddress -ne "127.0.0.1" -and $_.IPAddress -ne "169.254.*" 
    }
    
    foreach ($adapter in $networkAdapters) {
        $adapterName = (Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex).Name
        Write-Host "   📡 $adapterName`: $($adapter.IPAddress)" -ForegroundColor White
        
        # Check if this might be a Meshnet IP
        if ($adapter.IPAddress -like "100.*") {
            Write-Host "     🌍 Potential Meshnet IP - Access from anywhere!" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "   ⚠️ Could not retrieve network information" -ForegroundColor Yellow
}

# Test firewall rules
Write-Host "🧪 Testing firewall configuration..." -ForegroundColor Blue

try {
    # Test if we can create a listener on the specified ports
    $ports = @($Port, $OllamaPort)
    
    foreach ($testPort in $ports) {
        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $testPort)
            $listener.Start()
            $listener.Stop()
            Write-Host "   ✅ Port $testPort is accessible" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️ Port $testPort may be blocked or in use" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ⚠️ Could not test firewall configuration" -ForegroundColor Yellow
}

# Show firewall status
Write-Host "🔍 Current firewall status:" -ForegroundColor Cyan

try {
    $firewallProfiles = Get-NetFirewallProfile
    foreach ($profile in $firewallProfiles) {
        $status = if ($profile.Enabled) { "Enabled" } else { "Disabled" }
        $color = if ($profile.Enabled) { "Green" } else { "Red" }
        Write-Host "   $($profile.Name): $status" -ForegroundColor $color
    }
} catch {
    Write-Host "   ⚠️ Could not retrieve firewall status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Firewall configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌍 Access URLs:" -ForegroundColor Cyan
Write-Host "   Local:      http://localhost:$Port" -ForegroundColor White
Write-Host "   Network:    http://YOUR_IP:$Port" -ForegroundColor White
Write-Host "   Meshnet:    http://MESHNET_IP:$Port (if available)" -ForegroundColor White
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Start the AI Control System: .\scripts\start_stack.ps1" -ForegroundColor Gray
Write-Host "   2. Test local access: http://localhost:$Port/health" -ForegroundColor Gray
Write-Host "   3. Test network access from another device" -ForegroundColor Gray
Write-Host ""
Write-Host "🗑️ To remove rules: .\scripts\setup_firewall.ps1 -Remove" -ForegroundColor Gray
