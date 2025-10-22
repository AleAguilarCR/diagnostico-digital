@echo off
echo ========================================
echo  DIAGNOSTICO DE MADUREZ DIGITAL v1.5
echo  Instalador Automatico para Windows
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Por favor instala Python 3.8+ desde python.org
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

REM Crear entorno virtual
echo 📦 Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ❌ Error creando entorno virtual
    pause
    exit /b 1
)

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo 📚 Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)

echo.
echo ✅ Instalación completada exitosamente!
echo.
echo 🚀 Para ejecutar la aplicación:
echo    1. Ejecutar: ejecutar.bat
echo    2. Abrir navegador en: http://localhost:5000
echo.
echo 📋 Credenciales de consultor:
echo    Email: alejandroaguilar1000@gmail.com
echo    Empresa: consultor1
echo.
pause