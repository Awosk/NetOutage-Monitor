@echo off
:: NetOutageMonitor Kurulum / Kaldırma Scripti
:: Yönetici olarak çalıştırın!

:: --- AYARLAR ---
set "SERVICE_NAME=NetOutageMonitorService"
set "WORKER_SCRIPT=%~dp0worker.py"
:: ---------------

NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo HATA: Bu scripti Yonetici olarak calistirin!
    echo Sag tik ^> "Yonetici olarak calistir"
    pause
    exit /b 1
)

:: Python yüklü mü kontrolü
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo HATA: Python yuklu degil veya sistem PATH degiskenine eklenmemis!
    echo Lutfen Python'u kurup "Add to PATH" secenegini isaretlediginizden emin olun.
    pause
    exit /b 1
)

:MENU
cls
echo ============================================
echo   NetOutageMonitor - Servis Yonetimi
echo ============================================
echo.
echo  [1] Servisi Kur ve Baslat
echo  [2] Servisi Durdur ve Kaldir
echo  [3] Servis Durumunu Goster
echo  [4] Cikis
echo.
set /p SECIM="Seciminiz (1-4): "

IF "%SECIM%"=="1" GOTO INSTALL
IF "%SECIM%"=="2" GOTO REMOVE
IF "%SECIM%"=="3" GOTO STATUS
IF "%SECIM%"=="4" GOTO END
GOTO MENU

:INSTALL
echo.
echo Bagimliliklar kontrol ediliyor (pywin32)...
pip install pywin32 -q
IF %ERRORLEVEL% NEQ 0 (
    echo HATA: pywin32 modulu kurulamadi! Lutfen internet baglantinizi kontrol edin.
    pause
    GOTO MENU
)

echo.
echo Servis kuruluyor...
python "%WORKER_SCRIPT%" install
IF %ERRORLEVEL% NEQ 0 (
    echo HATA: Servis kurulamadi!
    pause
    GOTO MENU
)

echo Servis otomatik baslama olarak ayarlaniyor...
sc config %SERVICE_NAME% start= auto
echo Servis baslatiliyor...
net start %SERVICE_NAME%
echo.
echo ✓ Servis basariyla kuruldu ve baslatildi.
pause
GOTO MENU

:REMOVE
echo.
echo Servis durduruluyor...
:: Eğer servis zaten durmuşsa hata vermemesi için çıktıyı gizliyoruz
net stop %SERVICE_NAME% >nul 2>&1

echo Servis kaldiriliyor...
python "%WORKER_SCRIPT%" remove
echo.
echo ✓ Servis kaldirildi.
pause
GOTO MENU

:STATUS
echo.
sc query %SERVICE_NAME%
echo.
pause
GOTO MENU

:END
exit /b 0