# Comprehensive Backend API Test Script
# Usage: cd backend && powershell -ExecutionPolicy Bypass -File test_backend.ps1

Write-Host "=== Backend API Testing ===" -ForegroundColor Cyan
Write-Host ""

$API_BASE = "http://localhost:8000"
$successCount = 0
$failCount = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            UseBasicParsing = $true
            TimeoutSec = 5
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] Status: $($response.StatusCode)" -ForegroundColor Green
            
            try {
                $json = $response.Content | ConvertFrom-Json
                Write-Host "  Response: " -ForegroundColor Gray -NoNewline
                Write-Host ($json | ConvertTo-Json -Depth 2 -Compress) -ForegroundColor White
                return $true
            } catch {
                Write-Host "  Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor White
                return $true
            }
        } else {
            Write-Host "  [WARN] Status: $($response.StatusCode)" -ForegroundColor Yellow
            return $false
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMsg = $_.Exception.Message
        
        if ($statusCode) {
            Write-Host "  [FAIL] HTTP $statusCode" -ForegroundColor Red
            Write-Host "  Error: $errorMsg" -ForegroundColor Red
        } else {
            Write-Host "  [FAIL] Connection failed" -ForegroundColor Red
            Write-Host "  Error: $errorMsg" -ForegroundColor Red
        }
        return $false
    }
    
    Write-Host ""
}

# Test 1: API Health Check
Write-Host "1️⃣ Testing API Health Check" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

if (Test-Endpoint -Name "Root Endpoint" -Url "$API_BASE/") {
    $successCount++
} else {
    $failCount++
    Write-Host ""
    Write-Host "❌ API is not running!" -ForegroundColor Red
    Write-Host "   Start API with: cd backend\scripts && .\start_api_background.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Portfolio Real-Time
Write-Host "2️⃣ Testing Portfolio Endpoints" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

if (Test-Endpoint -Name "Real-Time Portfolio" -Url "$API_BASE/api/portfolio/real-time") {
    $successCount++
} else {
    $failCount++
    Write-Host ""
    Write-Host "⚠️  Portfolio may not be initialized" -ForegroundColor Yellow
    Write-Host "   Run: cd backend && python scripts/init_data.py" -ForegroundColor Yellow
}

Write-Host ""

# Test 3: Equity History
Write-Host "3️⃣ Testing Equity History" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

if (Test-Endpoint -Name "Equity History" -Url "$API_BASE/api/portfolio/equity-history?limit=10") {
    $successCount++
} else {
    $failCount++
}

Write-Host ""

# Test 4: Recent Snapshots
Write-Host "4️⃣ Testing Recent Snapshots" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

if (Test-Endpoint -Name "Recent Snapshots" -Url "$API_BASE/api/portfolio/recent-snapshots?hours=24") {
    $successCount++
} else {
    $failCount++
}

Write-Host ""

# Test 5: Tools List
Write-Host "5️⃣ Testing Tools Endpoint" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

if (Test-Endpoint -Name "Tools List" -Url "$API_BASE/api/tools/list") {
    $successCount++
} else {
    $failCount++
}

Write-Host ""

# Test 6: Agent Status
Write-Host "6️⃣ Testing Agent Status" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

if (Test-Endpoint -Name "Agent Status" -Url "$API_BASE/api/agents/status") {
    $successCount++
} else {
    $failCount++
}

Write-Host ""

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "Test Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Passed: $successCount" -ForegroundColor Green
Write-Host "  ❌ Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "🎉 All tests passed! Backend is working correctly." -ForegroundColor Green
} elseif ($successCount -gt 0) {
    Write-Host "⚠️  Some tests failed. Check the errors above." -ForegroundColor Yellow
} else {
    Write-Host "❌ All tests failed. Check if API is running." -ForegroundColor Red
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. If portfolio endpoints fail, initialize data:" -ForegroundColor White
Write-Host "   cd backend && python scripts/init_data.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Test in browser:" -ForegroundColor White
Write-Host "   http://localhost:8000/" -ForegroundColor Yellow
Write-Host "   http://localhost:8000/api/portfolio/real-time" -ForegroundColor Yellow
Write-Host ""

