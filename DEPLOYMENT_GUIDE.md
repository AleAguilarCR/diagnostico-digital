# 🚀 Guía de Deployment - Ruta de Estrategia Digital v1.0

## Opciones de Deployment

### Opción 1: Fly.io (Recomendado) ⭐

Fly.io ofrece:
- ✅ Tier gratuito generoso
- ✅ Deploy automático desde GitHub
- ✅ Base de datos SQLite persistente
- ✅ CDN global incluido
- ✅ SSL automático

#### Pasos para Fly.io:

**1. Instalar Fly CLI:**

```powershell
# Opción A: Con instalador de Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Opción B: Con Chocolatey
choco install flyctl
```

**2. Autenticarse:**

```powershell
fly auth login
```

**3. Crear la aplicación (primera vez):**

```powershell
cd C:\Users\aaguil5\Documents\ruta-digital
fly launch
```

Cuando pregunte:
- App name: `ruta-digital` (o el que prefieras)
- Region: `mia` (Miami - más cercano a LATAM)
- PostgreSQL database: `No` (usamos SQLite)
- Redis database: `No`

**4. Configurar variables de entorno:**

```powershell
# Secret key para Flask
fly secrets set SECRET_KEY="tu-clave-secreta-super-segura-aqui-$(Get-Random)"

# API Key de Gemini (opcional pero recomendado)
fly secrets set GEMINI_API_KEY="tu-api-key-de-gemini"
```

**5. Crear volumen para persistencia de la base de datos:**

```powershell
fly volumes create ruta_digital_data --region mia --size 1
```

Luego actualizar `fly.toml` para incluir el volumen:

```toml
[mounts]
  source = "ruta_digital_data"
  destination = "/app/data"
```

Y modificar `config.py` para usar `/app/data/diagnostico.db` en producción.

**6. Desplegar:**

```powershell
fly deploy
```

**7. Verificar:**

```powershell
fly status
fly logs
fly open
```

---

### Opción 2: GitHub + Render

Render ofrece deployment automático desde GitHub:

**1. Subir código a GitHub:**

```powershell
cd C:\Users\aaguil5\Documents\ruta-digital

# Inicializar repo si no existe
git init
git add .
git commit -m "Release v1.0 - Ruta de Estrategia Digital"

# Conectar con tu repo en GitHub
git remote add origin https://github.com/AleAguilarCR/diagnostico-digital.git
git branch -M main
git push -u origin main
```

**2. Crear Web Service en Render:**

- Ve a https://dashboard.render.com/
- Click "New +" → "Web Service"
- Conecta tu repositorio GitHub
- Configuración:
  - **Name:** `ruta-digital`
  - **Region:** Oregon (US West) - más cercano a LATAM
  - **Branch:** `main`
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `gunicorn app:app`
  - **Instance Type:** Free

**3. Variables de Entorno en Render:**

En el dashboard de Render, agrega:
- `SECRET_KEY`: (genera una clave segura)
- `GEMINI_API_KEY`: (tu API key de Gemini)
- `FLASK_ENV`: `production`

**4. Deploy Automático:**

Cada push a `main` desplegará automáticamente.

---

### Opción 3: GitHub + Railway

Similar a Render pero con mejor tier gratuito:

**1. Subir código a GitHub** (igual que opción 2)

**2. Deployment en Railway:**

- Ve a https://railway.app/
- "Start a New Project"
- "Deploy from GitHub repo"
- Selecciona `diagnostico-digital`
- Railway detectará automáticamente Python/Flask
- Agrega variables de entorno en Settings

---

## 📋 Checklist Pre-Deployment

- [x] Versión actualizada a 1.0
- [x] `requirements.txt` tiene gunicorn
- [x] `Procfile` creado
- [x] `Dockerfile` creado
- [x] `fly.toml` configurado
- [ ] Variables de entorno configuradas
- [ ] Base de datos respaldada
- [ ] Dominio personalizado (opcional)

---

## 🔧 Configuración Post-Deployment

### Configurar Gemini API Key

Para habilitar recomendaciones con IA:

1. Obtén API key gratuita: https://makersuite.google.com/app/apikey
2. Configura en tu plataforma:

**Fly.io:**
```powershell
fly secrets set GEMINI_API_KEY="tu-api-key"
```

**Render/Railway:**
Agregar en el dashboard web como variable de entorno

### Verificar Funcionamiento

1. Acceder a la URL de producción
2. Crear un usuario de prueba
3. Completar una evaluación
4. Verificar que genera recomendaciones
5. Descargar PDF para probar generación

---

## 🆘 Troubleshooting

### Error: Base de datos no se crea

**Fly.io:**
```powershell
fly ssh console
cd /app
python -c "from app import init_db; init_db()"
```

### Error: Aplicación no inicia

Verificar logs:

**Fly.io:**
```powershell
fly logs
```

**Render:**
Ver logs en el dashboard

### Error: 502 Bad Gateway

Usualmente significa que la app crasheó. Verifica:
1. Logs de error
2. Variables de entorno configuradas
3. Puerto correcto (8080 para Fly.io, puerto dinámico para Render)

---

## 📊 Monitoreo

### Fly.io

```powershell
# Ver estado
fly status

# Ver logs en tiempo real
fly logs

# Ver métricas
fly dashboard
```

### Render

Dashboard web: https://dashboard.render.com/

---

## 🔄 Actualizaciones Futuras

### Fly.io

```powershell
# Hacer cambios en el código
git add .
git commit -m "Actualización: descripción"

# Desplegar
fly deploy
```

### Render (con GitHub)

```powershell
git add .
git commit -m "Actualización: descripción"
git push origin main
# Deploy automático en Render
```

---

## 💰 Costos Estimados

### Fly.io (Gratis hasta)
- 3 VMs compartidas (256MB RAM)
- 160GB ancho de banda
- Suficiente para 100-200 usuarios beta

### Render (Gratis)
- 750 horas/mes (suficiente para 1 servicio 24/7)
- Se apaga después de 15 min de inactividad
- Bueno para testing inicial

### Railway (Crédito inicial)
- $5 de crédito gratis mensual
- Mejor performance que Render
- No se apaga por inactividad

---

## 🎯 Recomendación

Para **usuarios beta**: **Fly.io** es la mejor opción por:
1. No se apaga por inactividad
2. Base de datos persistente
3. Mejor latencia para LATAM
4. Configuración más completa

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs
2. Verifica variables de entorno
3. Consulta la documentación oficial de la plataforma elegida
