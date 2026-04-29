@echo off
chcp 65001 >nul
:: Yönetici yetkisi kontrolü
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :Run
) else (
    echo =======================================================
    echo [HATA] Bu islem icin Yonetici izinleri gerekiyor!
    echo Lutfen bu dosyaya SAG TIKLAYIP "Yonetici Olarak Calistir" deyin.
    echo =======================================================
    pause
    exit
)

:Run
echo =======================================================
echo HONEYPOT OTOMATIK BASLATMA KURULUMU
echo =======================================================
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%Catchmebro.py"

:: VBS dosyasini siliyoruz cunku artik gerek yok
if exist "%SCRIPT_DIR%Tuzagi_Baslat.vbs" del /f /q "%SCRIPT_DIR%Tuzagi_Baslat.vbs"

:: Gecici PowerShell betigi olustur
set "PS_SCRIPT=%temp%\honeypot_install.ps1"
echo $ErrorActionPreference = 'Stop' > "%PS_SCRIPT%"
echo $interactiveUser = (Get-CimInstance Win32_ComputerSystem).UserName >> "%PS_SCRIPT%"
echo if (-not $interactiveUser) { $interactiveUser = $env:USERNAME } >> "%PS_SCRIPT%"
echo $pythonPath = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source >> "%PS_SCRIPT%"
echo if (-not $pythonPath) { >> "%PS_SCRIPT%"
echo     $pythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source >> "%PS_SCRIPT%"
echo     if ($pythonExe) { $pythonPath = Join-Path (Split-Path $pythonExe) 'pythonw.exe' } >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"
echo if (-not $pythonPath -or -not (Test-Path $pythonPath)) { >> "%PS_SCRIPT%"
echo     Write-Host '[HATA] Python bulunamadi! Lutfen Python yuklu oldugundan emin olun.' -ForegroundColor Red >> "%PS_SCRIPT%"
echo     exit 1 >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"
echo $action = New-ScheduledTaskAction -Execute $pythonPath -Argument '"%SCRIPT_PATH%"' -WorkingDirectory '%SCRIPT_DIR%' >> "%PS_SCRIPT%"
echo $trigger = New-ScheduledTaskTrigger -AtLogon >> "%PS_SCRIPT%"
echo $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0 >> "%PS_SCRIPT%"
echo $principal = New-ScheduledTaskPrincipal -UserId $interactiveUser -LogonType Interactive -RunLevel Highest >> "%PS_SCRIPT%"
echo Register-ScheduledTask -TaskName 'Honeypot_Catchmebro' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force ^| Out-Null >> "%PS_SCRIPT%"
echo Write-Host '[BASARILI] Kurulum Tamamlandi!' -ForegroundColor Green >> "%PS_SCRIPT%"

:: Betigi calistir
PowerShell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set PS_RESULT=%errorlevel%

:: Gecici betigi sil
del /f /q "%PS_SCRIPT%"

if %PS_RESULT% neq 0 (
    echo.
    echo [HATA] Kurulum sirasinda bir sorun olustu.
) else (
    echo.
    echo Artik bilgisayar her acildiginda UAC uyarisi SORMADAN, sessizce arkaplanda calisacak.
    echo Pilde calisirken bile baslatilacak sekilde ayarlandi.
    echo.
    echo DİKKAT: Eger daha once "shell:startup" (Baslangic) klasorune kisayol attiysaniz, lutfen silin.
)
echo.
pause
