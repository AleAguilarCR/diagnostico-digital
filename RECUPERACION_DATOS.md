# 🚨 RECUPERACIÓN DE DATOS Y PERSISTENCIA EN RENDER

## ⚠️ SITUACIÓN ACTUAL

**Problema:** SQLite en Render se borra en cada deployment (almacenamiento efímero).
**Resultado:** Se perdieron los datos de producción en el último deployment.

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. Render Disk (Persistencia)
- Configurado disco persistente de 1GB en `render.yaml`
- Ruta: `/opt/render/project/src/data/`
- La base de datos ahora persiste entre deployments

### 2. Función Helper para Conexiones
- Creada función `get_db_connection()` 
- Detecta automáticamente si está en Render o local
- Usa rutas correctas según el entorno

## 📋 PASOS PARA ACTIVAR EN RENDER

### Paso 1: Deployment con Render Disk

**IMPORTANTE:** Render Disk NO está disponible en el plan Free. Tienes dos opciones:

#### Opción A: Upgrade a plan Starter ($7/mes)
1. Ve a Render Dashboard → Tu servicio
2. Settings → Upgrade to Starter
3. Haz deployment (el disco se creará automáticamente)

#### Opción B: Migrar a PostgreSQL (GRATIS en Render)
PostgreSQL SI está incluido gratis en Render y es la solución recomendada.

Te puedo ayudar a migrar ahora mismo.

## 🔄 SI ELIGES POSTGRESQL (Recomendado):

### Ventajas:
- ✅ Gratis en Render
- ✅ Backups automáticos
- ✅ Mejor rendimiento
- ✅ Escalable
- ✅ Industry standard

### Qué necesito hacer:
1. Crear base de datos PostgreSQL en Render
2. Modificar `app.py` para usar PostgreSQL
3. Migrar esquema de SQLite a PostgreSQL
4. Los datos se mantienen permanentemente

## 📊 ESTADO ACTUAL DE DATOS

**Backup local:** diagnostico_PRODUCCION_backup_*.db
**Estado:** Vacío (datos ya se perdieron)
**Acción necesaria:** Reconstruir datos o restaurar de otro backup si existe

## 🎯 PRÓXIMOS PASOS RECOMENDADOS

1. **DECIDIR:** ¿PostgreSQL (gratis) o Render Disk (pagado)?
2. **IMPLEMENTAR:** La solución elegida
3. **CONFIGURAR:** Backups automáticos
4. **DOCUMENTAR:** Proceso de respaldo

## 📞 ¿QUÉ PREFIERES?

A) **PostgreSQL** - Gratis, robusto, recomendado
B) **Render Disk** - Mantener SQLite ($7/mes)
C) **Otra opción** - Railway, Supabase, etc.

Dime cuál prefieres y lo configuro inmediatamente.
