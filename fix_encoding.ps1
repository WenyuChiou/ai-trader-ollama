# Fix PowerShell encoding for Chinese characters
# Run this before running other scripts if you see garbled text

# Set console encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Set code page to UTF-8
chcp 65001 | Out-Null

Write-Host "Encoding fixed to UTF-8" -ForegroundColor Green
Write-Host "You can now run other scripts without encoding issues" -ForegroundColor Cyan

