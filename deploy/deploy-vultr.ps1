# Deploy NextStop to the Vultr server from YOUR PC.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File deploy\deploy-vultr.ps1 -Ip 45.77.94.140
# Optional: -Domain "nextstopmdc.xyz, www.nextstopmdc.xyz" once GoDaddy DNS points at the server.
param(
    [Parameter(Mandatory = $true)][string]$Ip,
    [string]$Key = "$HOME\.ssh\nextstop_vultr",
    [string]$Domain = ":80"
)
$ErrorActionPreference = "Stop"
$envFile = Join-Path $PSScriptRoot "..\backend\.env"
if (-not (Test-Path $envFile)) { throw "backend\.env not found. Copy backend\.env.example and fill it in first." }
$ssh = @("-i", $Key, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15")

Write-Host "1/4 Waiting for the server to finish first-boot setup (Docker install + git clone)..." -ForegroundColor Cyan
for ($i = 0; $i -lt 40; $i++) {
    $state = ssh @ssh "root@$Ip" "test -f /opt/cloud-init-done && echo READY || echo WAIT" 2>$null
    if ($state -eq "READY") { break }
    Write-Host "   not ready yet ($($i + 1)/40), waiting 15s..."
    Start-Sleep 15
}
if ($state -ne "READY") {
    Write-Host "Setup marker not found. Showing the setup log:" -ForegroundColor Yellow
    ssh @ssh "root@$Ip" "tail -30 /var/log/cloud-init-output.log"
    throw "First-boot setup did not finish."
}

Write-Host "2/4 Updating code and copying backend\.env (secrets go over SSH only)..." -ForegroundColor Cyan
ssh @ssh "root@$Ip" "cd /opt/MDC-Advisor && git fetch -q origin && git checkout -q Ricardo_2026 && git pull -q origin Ricardo_2026"
scp @ssh $envFile "root@${Ip}:/opt/MDC-Advisor/backend/.env"
ssh @ssh "root@$Ip" "chmod 600 /opt/MDC-Advisor/backend/.env"

Write-Host "3/4 Building and starting containers (first build takes ~3-5 minutes)..." -ForegroundColor Cyan
ssh @ssh "root@$Ip" "cd /opt/MDC-Advisor/deploy && DOMAIN='$Domain' docker compose up -d --build 2>&1 | tail -15"

Write-Host "4/4 Checking health..." -ForegroundColor Cyan
Start-Sleep 10
$url = if ($Domain -eq ":80") { "http://$Ip" } else { "https://" + ($Domain.Split(",")[0].Trim()) }
try {
    $h = Invoke-RestMethod "$url/api/health" -TimeoutSec 20
    Write-Host ("LIVE: $url   providers=" + ($h.llmProviders -join ",") + "  swarms=$($h.swarms)  storage=$($h.storage)") -ForegroundColor Green
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Yellow
    ssh @ssh "root@$Ip" "cd /opt/MDC-Advisor/deploy && docker compose ps && docker compose logs --tail 40 app"
}
