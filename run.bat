@echo off
echo ========================================
echo   DIAGNOSTICO DE MADUREZ DIGITAL
echo   Herramienta para PYMEs Centroamerica
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python 3.8+ desde https://python.org
    pause
    exit /b 1
)

REM Verificar si existe el entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
)

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Verificar si existen las dependencias
if not exist "venv\Lib\site-packages\flask" (
    echo Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias
        pause
        exit /b 1
    )
)

REM Verificar si existe la base de datos
if not exist "diagnostico.db" (
    echo Inicializando base de datos...
    python setup.py
)

REM Verificar configuración de Gemini
findstr /C:"TU_API_KEY_DE_GEMINI" app.py >nul
if not errorlevel 1 (
    echo.
    echo ⚠️  ATENCION: Debes configurar tu API Key de Gemini
    echo    1. Ve a: https://makersuite.google.com/app/apikey
    echo    2. Crea una nueva API Key
    echo    3. Edita app.py linea 15 y reemplaza TU_API_KEY_DE_GEMINI
    echo.
    echo ¿Deseas continuar sin configurar Gemini? (s/n)
    set /p continuar=
    if /i not "%continuar%"=="s" (
        echo Configuracion cancelada
        pause
        exit /b 1
    )
)

echo.
echo 🚀 Iniciando aplicacion...
echo    Accede a: http://localhost:5000
echo    Presiona Ctrl+C para detener
echo.

REM Ejecutar la aplicación
python app.py

pause