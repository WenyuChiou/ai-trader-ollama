# Test All API Endpoints
# This script tests all available API endpoints to ensure they work correctly

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Testing All API Endpoints" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$results = @()

# Test 1: Root endpoint
Write-Host "Test 1: Root endpoint (/)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        Write-Host "  Status: OK" -ForegroundColor Green
        Write-Host "  Message: $($json.message)" -ForegroundColor White
        Write-Host "  Version: $($json.version)" -ForegroundColor White
        $results += @{Test="Root Endpoint"; Status="PASS"; Details="Version $($json.version)"}
    }
} catch {
    Write-Host "  Status: FAILED - $_" -ForegroundColor Red
    $results += @{Test="Root Endpoint"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 2: Portfolio Real-Time
Write-Host "Test 2: Portfolio Real-Time (/api/portfolio/real-time)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/portfolio/real-time" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        if ($json.ok) {
            Write-Host "  Status: OK" -ForegroundColor Green
            Write-Host "  Total Value: `$$($json.total_value)" -ForegroundColor White
            Write-Host "  Cash: `$$($json.cash)" -ForegroundColor White
            $results += @{Test="Portfolio Real-Time"; Status="PASS"; Details="Total: `$$($json.total_value)"}
        } else {
            Write-Host "  Status: OK (but error message: $($json.error))" -ForegroundColor Yellow
            $results += @{Test="Portfolio Real-Time"; Status="WARN"; Details=$json.error}
        }
    }
} catch {
    Write-Host "  Status: FAILED - $_" -ForegroundColor Red
    $results += @{Test="Portfolio Real-Time"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 3: Equity History
Write-Host "Test 3: Equity History (/api/portfolio/equity-history)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/portfolio/equity-history?limit=5" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        if ($json.ok) {
            $count = if ($json.records) { $json.records.Count } else { 0 }
            Write-Host "  Status: OK" -ForegroundColor Green
            Write-Host "  Records: $count" -ForegroundColor White
            $results += @{Test="Equity History"; Status="PASS"; Details="$count records"}
        } else {
            Write-Host "  Status: OK (but error: $($json.error))" -ForegroundColor Yellow
            $results += @{Test="Equity History"; Status="WARN"; Details=$json.error}
        }
    }
} catch {
    Write-Host "  Status: FAILED - $_" -ForegroundColor Red
    $results += @{Test="Equity History"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 4: Agent Status
Write-Host "Test 4: Agent Status (/api/agents/status)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/agents/status" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        Write-Host "  Status: OK" -ForegroundColor Green
        $agentCount = if ($json.agents) { $json.agents.Count } else { 0 }
        Write-Host "  Agents: $agentCount" -ForegroundColor White
        $results += @{Test="Agent Status"; Status="PASS"; Details="$agentCount agents"}
    }
} catch {
    Write-Host "  Status: FAILED - $_" -ForegroundColor Red
    $results += @{Test="Agent Status"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 5: Recent Snapshots
Write-Host "Test 5: Recent Snapshots (/api/portfolio/recent-snapshots)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/portfolio/recent-snapshots?limit=5" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        if ($json.ok) {
            $count = if ($json.snapshots) { $json.snapshots.Count } else { 0 }
            Write-Host "  Status: OK" -ForegroundColor Green
            Write-Host "  Snapshots: $count" -ForegroundColor White
            $results += @{Test="Recent Snapshots"; Status="PASS"; Details="$count snapshots"}
        } else {
            Write-Host "  Status: OK (but error: $($json.error))" -ForegroundColor Yellow
            $results += @{Test="Recent Snapshots"; Status="WARN"; Details=$json.error}
        }
    }
} catch {
    Write-Host "  Status: FAILED - $_" -ForegroundColor Red
    $results += @{Test="Recent Snapshots"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Summary
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$passed = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$warned = ($results | Where-Object { $_.Status -eq "WARN" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

foreach ($result in $results) {
    $color = switch ($result.Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
    }
    $icon = switch ($result.Status) {
        "PASS" { "[OK]" }
        "WARN" { "[WARN]" }
        "FAIL" { "[FAIL]" }
    }
    Write-Host "$icon $($result.Test): $($result.Status)" -ForegroundColor $color
    Write-Host "   $($result.Details)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Total: $passed passed, $warned warnings, $failed failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })

if ($failed -eq 0) {
    Write-Host ""
    Write-Host "API is working correctly!" -ForegroundColor Green
    Write-Host "You can now start the frontend to connect to the API." -ForegroundColor Cyan
}

Write-Host ""
Read-Host "Press Enter to exit"

