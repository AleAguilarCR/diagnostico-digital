# 🚀 Guía de Deployment en Render

## ✅ Cambios Aplicados (Versión 1.5.1)

### Corrección de Error 404
- ✅ Función `generar_informe_cliente()` corregida
- ✅ Función `generar_plan_consultoria()` corregida
- ✅ Nuevo template `templates/error.html` agregado
- ✅ Mensaje claro: "Usuario no ha llenado la información"

### Archivos Actualizados
- `app.py` - Validaciones mejoradas con páginas HTML en lugar de JSON
- `templates/error.html` - Nuevo template de error
- `requirements.txt` - Agregado `gunicorn==21.2.0`
- `render.yaml` - Configuración de Render (nuevo)

---

## 📋 Pasos para Desplegar en Render

### Opción 1: Deployment Manual (Recomendado)

1. **Commitear los cambios al repositorio Git:**

```powershell
# En PowerShell, desde C:\diagnostico-digital
git status
git add app.py templates/error.html requirements.txt render.yaml
git commit -m "Fix: Agregar mensaje de error para usuarios sin evaluaciones"
git push origin main
```

2. **Actualizar en Render Dashboard:**
   - Ve a https://dashboard.render.com
   - Busca tu servicio "diagnostico-digital"
   - Render detectará automáticamente el push y desplegará
   - O haz clic en "Manual Deploy" → "Deploy latest commit"

3. **Verificar el deployment:**
   - Espera 2-5 minutos
   - Verifica logs en Render Dashboard
   - Prueba la URL de producción

### Opción 2: Deployment desde CLI de Render

```powershell
# Instalar Render CLI (si no la tienes)
npm install -g @render/cli

# Login
render login

# Deploy
render deploy
```

---

## 🧪 Verificación Post-Deployment

### URLs a Probar:

1. **Login como consultor:**
   - Email: `alejandroaguilar1000@gmail.com`
   - Empresa: `consultor1`

2. **Ir a "Reportes del Consultor"**

3. **Probar con usuario sin evaluaciones:**
   - Buscar usuario con "0 ejes"
   - Clic en 📄 Informe Cliente o 📋 Plan Consultoría
   - **Resultado esperado:** Página de error elegante con mensaje claro

### Comandos de Verificación:

```powershell
# Verificar que la app responde
curl https://tu-app.onrender.com/

# Verificar endpoint específico (reemplazar ID)
curl https://tu-app.onrender.com/generar_informe_cliente/3
```

---

## 🔧 Configuración de Variables de Entorno en Render

En el Dashboard de Render → Tu servicio → Environment:

```
SECRET_KEY = [genera uno nuevo desde Render]
GEMINI_API_KEY = tu-api-key-real-de-gemini
FLASK_ENV = production
```

---

## 📊 Monitoreo Post-Deployment

### Verificar Logs:
1. Ve a Render Dashboard → Tu servicio → Logs
2. Busca:
   - ✅ "Starting gunicorn"
   - ✅ "Booting worker"
   - ❌ Errores 500 o tracebacks

### Verificar Métricas:
- CPU y memoria dentro de límites del plan Free
- Respuestas HTTP 200 para endpoints normales
- Respuestas HTTP 404 con HTML para usuarios sin evaluaciones

---

## 🐛 Troubleshooting

### Problema: Error 500 después del deployment
**Solución:**
- Verifica logs en Render Dashboard
- Asegúrate que `GEMINI_API_KEY` esté configurada (o que el código maneje su ausencia)
- Verifica que `diagnostico.db` se recree automáticamente

### Problema: Template error.html no se encuentra
**Solución:**
```powershell
# Verificar que el archivo existe
git ls-files templates/error.html

# Si no existe, agregarlo:
git add templates/error.html
git commit -m "Add error template"
git push
```

### Problema: Base de datos SQLite se borra en cada deployment
**Solución (Render Free Tier):**
- SQLite no persiste en Render Free
- Considera migrar a PostgreSQL (incluido gratis en Render)
- O usar Render Disks (plan pagado)

---

## 🔄 Rollback (si algo falla)

```powershell
# Volver al commit anterior
git log --oneline -5
git revert HEAD
git push origin main
```

O en Render Dashboard:
- Ve a "Events"
- Encuentra el deployment anterior exitoso
- Haz clic en "Redeploy"

---

## ✅ Checklist Final

- [ ] Código commiteado a Git
- [ ] Push a repositorio remoto
- [ ] Render detectó cambios y desplegó
- [ ] Logs muestran deployment exitoso
- [ ] App responde en URL de producción
- [ ] Login funciona
- [ ] Reportes de consultor funcionan
- [ ] Error 404 muestra mensaje correcto
- [ ] Variables de entorno configuradas

---

## 📞 Contacto y Soporte

**Versión:** 1.5.1  
**Fecha:** 21 de noviembre de 2025  
**Corrección:** Error 404 para usuarios sin evaluaciones

Si encuentras problemas, verifica los logs en Render Dashboard primero.
