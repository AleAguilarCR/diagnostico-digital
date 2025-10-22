@echo off
echo ========================================
echo  DIAGNOSTICO DE MADUREZ DIGITAL v1.5
echo  Iniciando aplicacion...
echo ========================================
echo.

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Ejecutar aplicación
echo 🚀 Iniciando servidor...
echo 🌐 La aplicación estará disponible en: http://localhost:5000
echo 💡 Presiona Ctrl+C para detener
echo.
python app.py