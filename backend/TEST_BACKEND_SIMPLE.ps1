# Simple Backend Test - English only to avoid encoding issues
# Usage: cd backend && powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1

$API_BASE = "http://localhost:8000"
$passed = 0
$failed = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Backend API Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Test-Endpoint {
    param([string]$Name, [string]$Url)
    
    Write-Host "[TEST] $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] Status: 200" -ForegroundColor Green
            
            try {
                $json = $response.Content | ConvertFrom-Json
                if ($json.message) {
                    Write-Host "  Message: $($json.message)" -ForegroundColor White
                }
                if ($json.version) {
                    Write-Host "  Version: $($json.version)" -ForegroundColor White
                }
                if ($json.ok -ne $null) {
                    if ($json.ok) {
                        Write-Host "  Result: OK" -ForegroundColor Green
                        if ($json.total_value) {
                            Write-Host "  Total Value: `$$([math]::Round($json.total_value, 2))" -ForegroundColor White
                        }
                        if ($json.cash) {
                            Write-Host "  Cash: `$$([math]::Round($json.cash, 2))" -ForegroundColor White
                        }
                        if ($json.count) {
                            Write-Host "  Count: $($json.count)" -ForegroundColor White
                        }
                    } else {
                        Write-Host "  Result: ERROR - $($json.error)" -ForegroundColor Yellow
                    }
                }
            } catch {
                Write-Host "  Response: $($response.Content.Substring(0, [Math]::Min(80, $response.Content.Length)))..." -ForegroundColor White
            }
            
            Write-Host ""
            return $true
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  [FAIL] HTTP $statusCode" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# Test 1: Health Check
if (Test-Endpoint -Name "1. API Health Check" -Url "$API_BASE/") {
    $passed++
} else {
    $failed++
    Write-Host "ERROR: API is not running!" -ForegroundColor Red
    Write-Host "Start API: cd backend\scripts && .\start_api_background.ps1" -ForegroundColor Yellow
    exit 1
}

# Test 2: Real-Time Portfolio
if (Test-Endpoint -Name "2. Real-Time Portfolio" -Url "$API_BASE/api/portfolio/real-time") {
    $passed++
} else {
    $failed++
}

# Test 3: Equity History
if (Test-Endpoint -Name "3. Equity History" -Url "$API_BASE/api/portfolio/equity-history?limit=5") {
    $passed++
} else {
    $failed++
}

# Test 4: Tools List
if (Test-Endpoint -Name "4. Tools List" -Url "$API_BASE/api/tools/list") {
    $passed++
} else {
    $failed++
}

# Test 5: Agent Status
if (Test-Endpoint -Name "5. Agent Status" -Url "$API_BASE/api/agents/status") {
    $passed++
} else {
    $failed++
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "SUCCESS: All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Test in browser: http://localhost:8000/" -ForegroundColor White
    Write-Host "  2. View preview: frontend/preview.html" -ForegroundColor White
    Write-Host "  3. Start frontend: cd frontend && npm run dev" -ForegroundColor White
} else {
    Write-Host "WARNING: Some tests failed" -ForegroundColor Yellow
}

Write-Host ""

