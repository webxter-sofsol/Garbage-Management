# ============================================================
# clean_sessions.ps1
# Cleans expired Django sessions and used/expired OTPs from
# the database to resolve "Session Expired" login errors.
#
# Usage:
#   .\clean_sessions.ps1              # normal run
#   .\clean_sessions.ps1 -DryRun      # preview only, no changes
#   .\clean_sessions.ps1 -Verbose     # show extra detail
# ============================================================

param(
    [switch]$DryRun,
    [switch]$Verbose
)

# ── Config ───────────────────────────────────────────────────
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
$FallbackPy = "python"

# ── Resolve Python executable ────────────────────────────────
if (Test-Path $VenvPython) {
    $Python = $VenvPython
    Write-Host "  Using venv Python: $Python" -ForegroundColor DarkGray
} else {
    $Python = $FallbackPy
    Write-Host "  Venv not found, using system Python" -ForegroundColor Yellow
}

# ── Header ───────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  GCMS - Session and OTP Database Cleaner  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  MODE: DRY RUN - no changes will be made" -ForegroundColor Yellow
}
Write-Host ""

# ── Write temp Python script to a file (avoids quoting issues) ──
$TempScript = Join-Path $env:TEMP "gcms_clean_sessions.py"

$PythonCode = @"
import os, sys, django
from datetime import timedelta

PROJECT_DIR = r'$ScriptDir'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gcms.settings')
django.setup()
"@

$PythonCode += @'

from django.utils import timezone
from django.contrib.sessions.models import Session
from authentication.models import OTP

dry_run = '--dry-run' in sys.argv
now = timezone.now()

# Expired sessions
expired_sessions = Session.objects.filter(expire_date__lt=now)
session_count = expired_sessions.count()
if not dry_run:
    expired_sessions.delete()

# Used OTPs
used_otps = OTP.objects.filter(is_used=True)
used_count = used_otps.count()
if not dry_run:
    used_otps.delete()

# Expired unused OTPs
expired_otps = OTP.objects.filter(is_used=False, expires_at__lt=now)
expired_count = expired_otps.count()
if not dry_run:
    expired_otps.delete()

# Stale sessions older than 24 hours
stale_cutoff = now - timedelta(hours=24)
stale_sessions = Session.objects.filter(expire_date__lt=stale_cutoff)
stale_count = stale_sessions.count()
if not dry_run:
    stale_sessions.delete()

action = 'WOULD_REMOVE' if dry_run else 'REMOVED'
print(f"RESULT|{action}|{session_count}|{used_count}|{expired_count}|{stale_count}")
'@

Set-Content -Path $TempScript -Value $PythonCode -Encoding UTF8

# ── Build args ───────────────────────────────────────────────
$PyArgs = @($TempScript)
if ($DryRun) { $PyArgs += "--dry-run" }

# ── Run ──────────────────────────────────────────────────────
Write-Host "  Connecting to database..." -ForegroundColor Gray

try {
    $PrevDir = Get-Location
    Set-Location $ScriptDir
    $Output   = & $Python @PyArgs 2>&1
    $ExitCode = $LASTEXITCODE
    Set-Location $PrevDir
} catch {
    Write-Host ""
    Write-Host "  ERROR: Failed to run Python." -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Remove-Item $TempScript -ErrorAction SilentlyContinue
    exit 1
}

Remove-Item $TempScript -ErrorAction SilentlyContinue

# ── Parse output ─────────────────────────────────────────────
$ResultLine = $Output | Where-Object { $_ -match "^RESULT\|" }
$OtherLines = $Output | Where-Object { $_ -notmatch "^RESULT\|" }

if ($Verbose -and $OtherLines) {
    Write-Host ""
    Write-Host "  Python output:" -ForegroundColor DarkGray
    $OtherLines | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
}

if ($ExitCode -ne 0 -or -not $ResultLine) {
    Write-Host ""
    Write-Host "  ERROR: Script failed (exit code $ExitCode)" -ForegroundColor Red
    if ($OtherLines) { $OtherLines | ForEach-Object { Write-Host "  $_" -ForegroundColor Red } }
    exit 1
}

# ── Display results ──────────────────────────────────────────
$Parts        = $ResultLine -split "\|"
$Action       = $Parts[1]
$Sessions     = [int]$Parts[2]
$UsedOtps     = [int]$Parts[3]
$ExpiredOtps  = [int]$Parts[4]
$StaleSession = [int]$Parts[5]
$TotalOtps    = $UsedOtps + $ExpiredOtps
$TotalCleaned = $Sessions + $StaleSession + $TotalOtps

Write-Host "  Results:" -ForegroundColor White
Write-Host ""

$Rows = @(
    @{ Label = "Expired sessions";         Count = $Sessions     },
    @{ Label = "Stale sessions (>24 h)";   Count = $StaleSession },
    @{ Label = "Used OTPs";                Count = $UsedOtps     },
    @{ Label = "Expired unused OTPs";      Count = $ExpiredOtps  }
)

foreach ($Row in $Rows) {
    $Color = if ($Row.Count -gt 0) { "Yellow" } else { "Gray" }
    Write-Host ("  {0,-38} {1,6}" -f $Row.Label, $Row.Count) -ForegroundColor $Color
}

Write-Host ""

if ($TotalCleaned -eq 0) {
    Write-Host "  Database is already clean - nothing to remove." -ForegroundColor Green
} elseif ($DryRun) {
    Write-Host ("  Dry run complete. Would remove {0} records total." -f $TotalCleaned) -ForegroundColor Yellow
    Write-Host "  Run without -DryRun to apply changes." -ForegroundColor Yellow
} else {
    Write-Host ("  Done. {0} records removed." -f $TotalCleaned) -ForegroundColor Green
    Write-Host "  Session Expired errors should be resolved." -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
