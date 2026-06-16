param(
    [string]$TaskName = "OMEGA_PSA_WIND_AUTO_EXEC_POST_OPEN",
    [string]$WorkDir = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE",
    [string]$StartTimeLocal = "20:55"
)

$ScriptPath = Join-Path $WorkDir "scripts\psa_wind_auto_exec_post_open.ps1"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -WorkDir `"$WorkDir`""
$Trigger = New-ScheduledTaskTrigger -Daily -At $StartTimeLocal
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest -LogonType Interactive
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
Write-Host "Registered task: $TaskName at $StartTimeLocal local time"
