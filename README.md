# Diagnóstico de Madurez Digital para PYMEs

Una herramienta robusta de auto-diagnóstico de madurez digital diseñada específicamente para pequeñas y medianas empresas (PYMEs) en Costa Rica y Centroamérica.

## 🚀 Características Principales

### Módulo del Cliente
- **Acceso seguro**: Registro con email, nombre de empresa y tipo de negocio
- **Sesiones persistentes**: Continuación automática de evaluaciones previas
- **10 Ejes de Evaluación**: Basados en definiciones de Gartner y McKinsey
- **Interfaz elegante**: Diseño responsive con botones interactivos
- **Evaluaciones personalizadas**: Preguntas tipo Likert (1-5) y Sí/No

### 10 Ejes de Evaluación
1. **Cultura Digital Empresarial** 🏢
2. **Presencia en Internet y Redes Sociales** 🌐
3. **Adopción de Tecnologías Emergentes** 🚀
4. **Digitalización de Procesos Empresariales** ⚙️
5. **Competencia Digital de Colaboradores** 👥
6. **Gestión de Información y Toma de Decisiones** 📊
7. **Canales de Venta Online y Experiencia del Usuario** 🛒
8. **Gestión de Calidad y Ciberseguridad** 🔒
9. **Inversión en Tecnología** 💰
10. **Protección de Datos y Propiedad Intelectual** 🛡️

### Funcionalidades Avanzadas
- **Generación de PDFs**: Informes individuales por eje con recomendaciones
- **IA Integrada**: Recomendaciones personalizadas usando Google Gemini
- **Sistema de puntuación**: Indicadores visuales de nivel de madurez
- **Informe ejecutivo**: Resumen completo al completar 3+ ejes
- **Descarga y envío**: PDFs descargables y envío por correo

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de datos**: SQLite
- **IA**: Google Gemini API
- **Generación PDF**: ReportLab
- **Estilos**: Font Awesome, CSS personalizado

## 📋 Requisitos del Sistema

- Python 3.8+
- Navegador web moderno
- Conexión a internet (para IA)
- API Key de Google Gemini

## 🚀 Instalación y Configuración

### 1. Clonar o descargar el proyecto
```bash
cd diagnostico-digital
```

### 2. Crear entorno virtual
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar API de Gemini
1. Obtener API Key de Google AI Studio
2. Editar `app.py` línea 15:
```python
genai.configure(api_key='TU_API_KEY_AQUI')
```

### 5. Ejecutar la aplicación
```bash
python app.py
```

### 6. Acceder a la aplicación
Abrir navegador en: `http://localhost:5000`

## 📁 Estructura del Proyecto

```
diagnostico-digital/
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuraciones
├── requirements.txt      # Dependencias
├── README.md            # Documentación
├── diagnostico.db       # Base de datos SQLite (se crea automáticamente)
├── static/
│   ├── css/
│   │   └── style.css    # Estilos personalizados
│   ├── js/
│   │   └── main.js      # JavaScript principal
│   └── images/          # Imágenes y logos
└── templates/
    ├── base.html        # Plantilla base
    ├── index.html       # Página de inicio/login
    ├── dashboard.html   # Dashboard principal
    └── eje.html         # Página de evaluación
```

## 🎯 Uso de la Aplicación

### Para Usuarios (Empresas)
1. **Acceso**: Ingresar email, nombre y tipo de empresa
2. **Evaluación**: Seleccionar ejes y responder preguntas
3. **Resultados**: Ver puntaje y recomendaciones inmediatas
4. **Informes**: Descargar PDFs individuales o informe ejecutivo

### Para Consultores
1. **Configuración**: Personalizar logo y marca
2. **Análisis**: Revisar resultados en base de datos
3. **Seguimiento**: Generar estrategias basadas en evaluaciones

## 🔧 Personalización

### Cambiar Logo
Reemplazar el placeholder en `templates/dashboard.html` línea 45:
```html
<div class="bg-light p-3 rounded">
    <img src="{{ url_for('static', filename='images/tu-logo.png') }}" alt="Logo" class="img-fluid">
</div>
```

### Modificar Preguntas
Editar el diccionario `PREGUNTAS_EJES` en `app.py` líneas 60-150.

### Personalizar Estilos
Modificar `static/css/style.css` para cambiar colores, fuentes y efectos.

## 📊 Base de Datos

### Tabla `usuarios`
- id, email, nombre_empresa, tipo_empresa, fecha_registro

### Tabla `evaluaciones`
- id, usuario_id, eje_id, respuestas, puntaje, pdf_path, fecha_evaluacion

## 🔒 Seguridad y Privacidad

- **Datos mínimos**: Solo se solicita información esencial
- **No spam**: Compromiso de no usar emails para promociones
- **Almacenamiento local**: Base de datos SQLite local
- **Sesiones seguras**: Manejo seguro de sesiones de usuario

## 🌟 Características Destacadas

### Experiencia de Usuario
- ✅ Interfaz intuitiva y responsive
- ✅ Efectos visuales y animaciones suaves
- ✅ Indicadores de progreso en tiempo real
- ✅ Validación de formularios interactiva

### Inteligencia Artificial
- ✅ Recomendaciones contextualizadas por tipo de empresa
- ✅ Análisis específico para el mercado centroamericano
- ✅ Sugerencias accionables y prácticas

### Reportes Profesionales
- ✅ PDFs con diseño profesional
- ✅ Branding personalizable
- ✅ Recomendaciones específicas por eje
- ✅ Informe ejecutivo consolidado

## 🚀 Próximas Mejoras

- [ ] Envío de PDFs por correo electrónico
- [ ] Dashboard para consultores
- [ ] Comparativas entre empresas del mismo sector
- [ ] Integración con más APIs de IA
- [ ] Exportación a Excel
- [ ] Sistema de notificaciones
- [ ] Análisis de tendencias temporales

## 📞 Soporte

Para soporte técnico o consultas sobre personalización, contactar al desarrollador.

## 📄 Licencia

Este proyecto está desarrollado para uso comercial. Todos los derechos reservados.

---

**Desarrollado con ❤️ para PYMEs en Centroamérica**