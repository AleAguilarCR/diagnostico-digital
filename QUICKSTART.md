# 🎯 Quick Start - Deployment Rápido

## Opción Más Rápida: Fly.io

### 1️⃣ Instalar Fly CLI (solo primera vez)

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2️⃣ Login

```powershell
fly auth login
```

### 3️⃣ Deploy Automático

```powershell
.\deploy.ps1
```

Selecciona opción **1** (Fly.io)

---

## ✅ Eso es todo!

El script `deploy.ps1` hace todo automáticamente:
- ✅ Git commit
- ✅ Deploy a Fly.io
- ✅ Abre la app en el navegador

---

## 🔑 Configurar API de Gemini (Opcional)

Para habilitar recomendaciones con IA:

```powershell
fly secrets set GEMINI_API_KEY="tu-api-key-aqui"
```

Obtén tu API key gratis en: https://makersuite.google.com/app/apikey

---

## 📖 Más Información

Ver `DEPLOYMENT_GUIDE.md` para opciones avanzadas y otras plataformas.
