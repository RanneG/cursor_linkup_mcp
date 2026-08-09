# Register weekday 07:30 daily brief cron on Windows PC Hermes.
param(
    # Required: numeric Telegram user id for --deliver / TELEGRAM_HOME_CHANNEL.
    # No hardcoded default — a wrong default would DM briefs to someone else's chat.
    [Parameter(Mandatory = $false)]
    [string]$TelegramUserId = "",
    [string]$Schedule = "every weekday at 07:30",
    [string]$JobName = "nami-daily-brief"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
    Write-Error "hermes not on PATH. Open a new terminal after install."
}

if (-not $TelegramUserId) {
    $existingHome = (& hermes config get TELEGRAM_HOME_CHANNEL 2>$null | Out-String).Trim()
    if ($existingHome -match '^\d+$') {
        $TelegramUserId = $existingHome
        Write-Host "Using existing TELEGRAM_HOME_CHANNEL=$TelegramUserId" -ForegroundColor Cyan
    }
}

if (-not ($TelegramUserId -match '^\d+$')) {
    Write-Error @"
Telegram user id required. Pass -TelegramUserId <digits> (from Telegram pairing / @userinfobot).
Refusing to create cron delivery without an explicit chat id.
Example: .\scripts\Setup-NamiDailyBrief.ps1 -TelegramUserId 123456789
"@
}

Write-Host "=== Sync Nami skills ===" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "install-nami-hermes.ps1")

Write-Host ""
Write-Host "=== Home channel ===" -ForegroundColor Cyan
& hermes config set TELEGRAM_HOME_CHANNEL $TelegramUserId
Write-Host "TELEGRAM_HOME_CHANNEL=$TelegramUserId"

$prompt = @"
Run daily-brief-loop skill exactly: 3 bullets (Build, Products, This week), read-only.
Use /loop-checker before sending. Turn cap 8. Append LOOP_LOG.md on PASS or FAIL.
Skip web_search unless USER.md says otherwise.
"@

Write-Host ""
Write-Host "=== Cron job: $JobName ===" -ForegroundColor Cyan
$existing = & hermes cron list 2>&1 | Out-String
if ($existing -match $JobName) {
    Write-Host "Job '$JobName' already exists. Edit with: hermes cron edit $JobName --schedule `"$Schedule`"" -ForegroundColor Yellow
} else {
    & hermes cron create $Schedule $prompt `
        --skill brief `
        --skill loop-checker `
        --name $JobName `
        --deliver "telegram:$TelegramUserId"
}

Write-Host ""
Write-Host "=== Test now ===" -ForegroundColor Cyan
Write-Host "  hermes cron run $JobName"
Write-Host "  Or Telegram: /brief"
Write-Host ""
Write-Host "Docs: docs/hermes/DAILY_BRIEF.md"
