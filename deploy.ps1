# Script de deployment para Fly.io
# Versión 1.0

Write-Host "🚀 Ruta de Estrategia Digital - Deployment Script v1.0" -ForegroundColor Cyan
Write-Host "=" * 60

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "app.py")) {
    Write-Host "❌ Error: No se encuentra app.py" -ForegroundColor Red
    Write-Host "Por favor ejecuta este script desde el directorio del proyecto" -ForegroundColor Yellow
    exit 1
}

# Verificar versión
$version = Get-Content "VERSION" -Raw
$version = $version.Trim()
Write-Host "📦 Versión actual: $version" -ForegroundColor Green

# Menú de opciones
Write-Host "`n¿Qué plataforma quieres usar?" -ForegroundColor Yellow
Write-Host "1) Fly.io (Recomendado para producción)" -ForegroundColor White
Write-Host "2) GitHub + Push (para Render/Railway)" -ForegroundColor White
Write-Host "3) Solo Git commit (sin push)" -ForegroundColor White
Write-Host "4) Cancelar" -ForegroundColor White

$choice = Read-Host "`nSelecciona una opción (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n🛫 Preparando deployment a Fly.io..." -ForegroundColor Cyan
        
        # Verificar si fly está instalado
        try {
            $flyVersion = fly version 2>&1
            Write-Host "✅ Fly CLI detectado" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Fly CLI no está instalado" -ForegroundColor Red
            Write-Host "Instálalo con: powershell -Command `"iwr https://fly.io/install.ps1 -useb | iex`"" -ForegroundColor Yellow
            exit 1
        }
        
        # Verificar autenticación
        Write-Host "🔐 Verificando autenticación..." -ForegroundColor Cyan
        $authStatus = fly auth whoami 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ No estás autenticado en Fly.io" -ForegroundColor Red
            Write-Host "Ejecuta: fly auth login" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "✅ Autenticado como: $authStatus" -ForegroundColor Green
        
        # Git commit
        Write-Host "`n📝 Haciendo commit de cambios..." -ForegroundColor Cyan
        git add .
        $commitMsg = "Deploy v$version - Ruta de Estrategia Digital"
        git commit -m $commitMsg
        
        # Deploy
        Write-Host "`n🚀 Desplegando a Fly.io..." -ForegroundColor Cyan
        fly deploy
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Deployment exitoso!" -ForegroundColor Green
            Write-Host "🌐 Abriendo aplicación..." -ForegroundColor Cyan
            fly open
            
            Write-Host "`n📊 Comandos útiles:" -ForegroundColor Yellow
            Write-Host "  fly logs          - Ver logs en tiempo real" -ForegroundColor White
            Write-Host "  fly status        - Ver estado de la app" -ForegroundColor White
            Write-Host "  fly dashboard     - Abrir dashboard" -ForegroundColor White
        }
        else {
            Write-Host "`n❌ Error en el deployment" -ForegroundColor Red
            Write-Host "Revisa los logs con: fly logs" -ForegroundColor Yellow
        }
    }
    
    "2" {
        Write-Host "`n📤 Preparando push a GitHub..." -ForegroundColor Cyan
        
        # Verificar git
        if (-not (Test-Path ".git")) {
            Write-Host "❌ No es un repositorio Git" -ForegroundColor Red
            Write-Host "Inicializa con: git init" -ForegroundColor Yellow
            exit 1
        }
        
        # Git operations
        Write-Host "📝 Añadiendo archivos..." -ForegroundColor Cyan
        git add .
        
        $commitMsg = "Release v$version - Ruta de Estrategia Digital"
        Write-Host "💾 Commit: $commitMsg" -ForegroundColor Cyan
        git commit -m $commitMsg
        
        Write-Host "🔼 Pushing a GitHub..." -ForegroundColor Cyan
        git push origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Push exitoso a GitHub!" -ForegroundColor Green
            Write-Host "Si tienes Render o Railway configurado, el deploy iniciará automáticamente" -ForegroundColor Yellow
        }
        else {
            Write-Host "`n⚠️ Error en el push" -ForegroundColor Red
            Write-Host "Verifica la conexión con el repositorio remoto" -ForegroundColor Yellow
        }
    }
    
    "3" {
        Write-Host "`n📝 Haciendo commit local..." -ForegroundColor Cyan
        
        git add .
        $commitMsg = Read-Host "Mensaje del commit"
        if ([string]::IsNullOrWhiteSpace($commitMsg)) {
            $commitMsg = "Update v$version"
        }
        
        git commit -m $commitMsg
        
        Write-Host "✅ Commit realizado" -ForegroundColor Green
        Write-Host "Para hacer push: git push origin main" -ForegroundColor Yellow
    }
    
    "4" {
        Write-Host "`n👋 Deployment cancelado" -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "`n❌ Opción inválida" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n" + ("=" * 60)
Write-Host "✨ Proceso completado" -ForegroundColor Green
