from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import sqlite3
import json
import os
from datetime import datetime
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Line
from reportlab.platypus.flowables import HRFlowable
import io
import base64
import logging

app = Flask(__name__)
app.secret_key = 'tu-clave-secreta-super-segura-aqui'

# Configuración de la ruta de la base de datos
# En producción (Render), usa el disco persistente
# En desarrollo, usa la ruta local
DB_PATH = os.path.join(
    os.environ.get('DB_MOUNT_PATH', '/opt/render/project/src/data') 
    if os.environ.get('RENDER') 
    else os.path.dirname(os.path.abspath(__file__)),
    'diagnostico.db'
)

def get_db_connection():
    """Obtener conexión a la base de datos con la ruta correcta"""
    # Crear directorio si no existe (para Render Disk)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Ruta de base de datos: {DB_PATH}")

# Configurar Gemini
try:
    gemini_api_key = os.environ.get('GEMINI_API_KEY') or 'tu-api-key-real-aqui'
    logger.info(f"API Key detectada: {'Sí' if gemini_api_key != 'tu-api-key-real-aqui' else 'No'}")
    
    if gemini_api_key != 'TU_API_KEY_DE_GEMINI' and gemini_api_key != 'tu-api-key-real-aqui':
        genai.configure(api_key=gemini_api_key)
        # Usar gemini-pro (v1beta) - es el único modelo disponible con esta API key
        model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini AI configurado correctamente con gemini-pro")
    else:
        model = None
        logger.warning("Gemini AI no configurado - API key no válida")
except Exception as e:
    model = None
    logger.error(f"Error configurando Gemini AI: {e}")

# Definición de los 10 vectores de Estrategia Digital
EJES_EVALUACION = {
    1: {
        'nombre': 'Estrategia Digital',
        'descripcion': 'Evalúa la claridad del modelo de negocio digital, propuesta de valor y enfoque en escalabilidad',
        'icono': '⚙️'
    },
    2: {
        'nombre': 'Cultura Digital',
        'descripcion': 'Mide la mentalidad digital-first, apertura a experimentación y orientación a métricas',
        'icono': '💡'
    },
    3: {
        'nombre': 'Procesos Digital-First',
        'descripcion': 'Evalúa el diseño de procesos automatizados desde el inicio',
        'icono': '🔄'
    },
    4: {
        'nombre': 'Tecnología (Arquitectura Inicial)',
        'descripcion': 'Mide la selección de tecnologías, viabilidad del MVP y escalabilidad',
        'icono': '🖥️'
    },
    5: {
        'nombre': 'Datos',
        'descripcion': 'Evalúa el diseño del modelo de datos, fuentes futuras y KPIs iniciales',
        'icono': '📊'
    },
    6: {
        'nombre': 'Cliente',
        'descripcion': 'Mide el customer journey digital, validación de mercado y experiencia digital',
        'icono': '👥'
    },
    7: {
        'nombre': 'Talento',
        'descripcion': 'Evalúa las competencias digitales del equipo fundador y necesidades de contratación',
        'icono': '🎓'
    },
    8: {
        'nombre': 'Innovación',
        'descripcion': 'Mide la capacidad para iterar, prototipar y aplicar aprendizaje validado',
        'icono': '💡'
    },
    9: {
        'nombre': 'Ciberseguridad Inicial',
        'descripcion': 'Evalúa las medidas mínimas de seguridad para lanzar un MVP',
        'icono': '🔒'
    },
    10: {
        'nombre': 'Gobierno Digital',
        'descripcion': 'Mide los roles digitales, responsabilidades y criterios para decisiones digitales',
        'icono': '⚖️'
    }
}

# Preguntas para cada vector de Estrategia Digital
PREGUNTAS_EJES = {
    1: [  # Estrategia Digital
        {'tipo': 'sino', 'pregunta': '¿El modelo de negocio incorpora elementos digitales desde el inicio?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan definida está la propuesta de valor digital de su emprendimiento?'},
        {'tipo': 'sino', 'pregunta': '¿Existe un roadmap digital a 12-24 meses?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida su estrategia considera escalabilidad y automatización?'}
    ],
    2: [  # Cultura Digital
        {'tipo': 'likert', 'pregunta': '¿Qué tan abierto está el equipo a experimentar con nuevas tecnologías?'},
        {'tipo': 'sino', 'pregunta': '¿El equipo valora los experimentos rápidos y el aprendizaje continuo?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida las decisiones se basan en métricas y datos?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan fuerte es la mentalidad digital-first en el equipo fundador?'}
    ],
    3: [  # Procesos Digital-First
        {'tipo': 'sino', 'pregunta': '¿Se han identificado procesos que deben ser automatizados desde el inicio?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan documentados están los procesos clave aunque sea a nivel básico?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida se han diseñado los procesos pensando en automatización?'},
        {'tipo': 'sino', 'pregunta': '¿Se han minimizado los procesos manuales en el diseño inicial?'}
    ],
    4: [  # Tecnología (Arquitectura Inicial)
        {'tipo': 'sino', 'pregunta': '¿El emprendimiento ha seleccionado las herramientas tecnológicas clave?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan clara es la viabilidad técnica del MVP?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida se entienden las tecnologías que serán críticas en 1-2 años?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan considerados están los aspectos de costo, escalabilidad y mantenibilidad?'}
    ],
    5: [  # Datos
        {'tipo': 'likert', 'pregunta': '¿Qué tan claro está qué datos serán vitales para aprender del cliente?'},
        {'tipo': 'sino', 'pregunta': '¿Existe un diseño del modelo de datos inicial?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida se ha planificado cómo recolectar datos desde el MVP?'},
        {'tipo': 'sino', 'pregunta': '¿Se han definido las métricas y KPIs iniciales?'}
    ],
    6: [  # Cliente
        {'tipo': 'sino', 'pregunta': '¿Existe un mapa del customer journey digital?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan avanzada está la validación digital del problema y la solución?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida se ha diseñado la experiencia digital del cliente?'},
        {'tipo': 'sino', 'pregunta': '¿Se ha realizado validación de mercado con herramientas digitales?'}
    ],
    7: [  # Talento
        {'tipo': 'likert', 'pregunta': '¿Qué tan adecuadas son las competencias digitales del equipo fundador?'},
        {'tipo': 'sino', 'pregunta': '¿El equipo tiene las habilidades mínimas para construir un MVP?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan claras están las brechas de habilidades digitales críticas?'},
        {'tipo': 'sino', 'pregunta': '¿Se han identificado las necesidades de contratación o outsourcing para los próximos 12 meses?'}
    ],
    8: [  # Innovación
        {'tipo': 'sino', 'pregunta': '¿Existe un proceso definido para experimentar y aprender?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan desarrollada está la capacidad de prototipado rápido?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida se aplican técnicas tipo Lean Startup?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan ágil es el emprendimiento para iterar basándose en aprendizaje validado?'}
    ],
    9: [  # Ciberseguridad Inicial
        {'tipo': 'likert', 'pregunta': '¿Qué tan robustas son las medidas mínimas de seguridad planeadas para el MVP?'},
        {'tipo': 'sino', 'pregunta': '¿Se ha considerado la protección de datos del usuario en el diseño?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida se han identificado los riesgos digitales tempranos?'},
        {'tipo': 'sino', 'pregunta': '¿Existen políticas básicas de seguridad aunque no estén completamente implementadas?'}
    ],
    10: [  # Gobierno Digital
        {'tipo': 'sino', 'pregunta': '¿Está claro quién decide qué se construye digitalmente?'},
        {'tipo': 'likert', 'pregunta': '¿Qué tan definidos están los roles digitales en el equipo?'},
        {'tipo': 'likert', 'pregunta': '¿En qué medida existen criterios claros para priorizar funcionalidades?'},
        {'tipo': 'sino', 'pregunta': '¿Se han asignado responsables de tecnología, datos y procesos?'}
    ]
}

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE,
                  nombre_empresa TEXT,
                  tipo_empresa TEXT,
                  tamano_empresa TEXT,
                  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Agregar columna tamano_empresa si no existe
    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN tamano_empresa TEXT')
        logger.info("Columna tamano_empresa agregada a la base de datos")
    except sqlite3.OperationalError:
        logger.info("Columna tamano_empresa ya existe en la base de datos")
    
    # Verificar estructura de la tabla
    c.execute('PRAGMA table_info(usuarios)')
    columns = c.fetchall()
    logger.info(f"Estructura de tabla usuarios: {columns}")
    
    c.execute('''CREATE TABLE IF NOT EXISTS evaluaciones
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  eje_id INTEGER,
                  respuestas TEXT,
                  puntaje INTEGER,
                  pdf_path TEXT,
                  fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (usuario_id) REFERENCES usuarios (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS objetivos_negocio
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  objetivo1 TEXT,
                  objetivo2 TEXT,
                  objetivo3 TEXT,
                  fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (usuario_id) REFERENCES usuarios (id))''')
    
    conn.commit()
    conn.close()

def calcular_puntaje(respuestas):
    total = 0
    count = 0
    for respuesta in respuestas:
        if respuesta['tipo'] == 'likert':
            total += int(respuesta['valor'])
            count += 1
        elif respuesta['tipo'] == 'sino':
            total += 5 if respuesta['valor'] == 'si' else 1
            count += 1
    return round(total / count) if count > 0 else 1

def generar_recomendaciones(eje_id, respuestas, tipo_empresa, puntaje=None, tamano_empresa=None):
    eje_nombre = EJES_EVALUACION[eje_id]['nombre']
    
    # Calcular puntaje si no se proporciona
    if puntaje is None:
        puntaje = calcular_puntaje(respuestas)
    
    # Determinar el enfoque según el puntaje - ENFOQUE PARA EMPRENDIMIENTOS
    if puntaje <= 2:
        enfoque = "ESTABLECIMIENTO INICIAL"
        contexto_puntaje = f"Con un puntaje de {puntaje}/4, tu emprendimiento necesita establecer este vector desde cero. Las recomendaciones se enfocan en crear las bases fundamentales."
    elif puntaje == 3:
        enfoque = "CONSOLIDACIÓN"
        contexto_puntaje = f"Con un puntaje de {puntaje}/4, tu emprendimiento tiene fundamentos básicos. Las recomendaciones se enfocan en consolidar y estructurar este vector."
    else:  # puntaje >= 4
        enfoque = "AVANZADO"
        contexto_puntaje = f"Con un puntaje de {puntaje}/4, tu emprendimiento tiene bases sólidas. Las recomendaciones se enfocan en optimizar y escalar este vector."
    
    # Determinar nivel de recomendaciones según puntaje
    if puntaje <= 2:
        nivel = 'inicial'
        nivel_dict = 'bajo'  # Mapeo al diccionario existente
    elif puntaje == 3:
        nivel = 'consolidacion'
        nivel_dict = 'medio'  # Mapeo al diccionario existente
    else:
        nivel = 'avanzado'
        nivel_dict = 'alto'  # Mapeo al diccionario existente
    
    # Recomendaciones específicas por eje y nivel de puntaje
    recomendaciones_por_eje = {
        1: {  # Cultura Digital Empresarial
            'bajo': "1. Establezca una mentalidad digital desde la dirección. Designe un líder de transformación digital y establezca reuniones semanales para evaluar el progreso. Implemente herramientas básicas como Google Workspace o Microsoft 365 para toda la organización y capacite a los directivos en su uso durante las próximas 4 semanas.\n\n2. Cree una cultura de apertura al cambio tecnológico. Organice sesiones de sensibilización sobre beneficios de la digitalización, establezca incentivos para empleados que adopten nuevas tecnologías y documente casos de éxito internos. Dedique 2 horas semanales a compartir experiencias digitales exitosas.\n\n3. Desarrolle un plan básico de transformación digital con objetivos claros a 6 meses. Identifique 3 procesos críticos para digitalizar, asigne responsables y establezca un presupuesto mínimo del 5% de ingresos para tecnología. Revise el progreso mensualmente.\n\n4. Implemente políticas básicas de uso de tecnología. Cree manuales simples de herramientas digitales, establezca protocolos de comunicación digital interna y defina roles tecnológicos básicos. Capacite al personal en estas políticas durante 1 hora semanal.",
            'medio': "1. Fortalezca el liderazgo digital implementando un comité de transformación digital con representantes de todas las áreas. Establezca KPIs digitales, realice evaluaciones trimestrales de madurez digital y cree un programa de mentores digitales internos. Invierta en capacitación gerencial especializada en liderazgo digital.\n\n2. Desarrolle una estrategia integral de cambio cultural. Implemente programas de gamificación para adopción tecnológica, cree comunidades de práctica digital y establezca reconocimientos para innovadores digitales. Dedique 10% del tiempo laboral a experimentación con nuevas herramientas.\n\n3. Expanda el plan de transformación digital incluyendo objetivos a mediano plazo (1-2 años). Integre sistemas existentes, automatice procesos intermedios y establezca métricas de productividad digital. Aumente el presupuesto tecnológico al 8-10% de ingresos.\n\n4. Cree un ecosistema de aprendizaje continuo. Establezca alianzas con universidades locales, implemente plataformas de e-learning y certifique al personal en competencias digitales. Asigne 4 horas mensuales por empleado para capacitación digital.",
            'alto': "1. Posicione el emprendimiento como líder en cultura digital del sector. Documente y comparta las mejores prácticas, participe en eventos de transformación digital y ofrezca mentoría a otros emprendimientos. Implemente tecnologías emergentes como IA y automatización avanzada para mantener la ventaja competitiva.\n\n2. Optimice la cultura de innovación creando laboratorios de innovación internos. Establezca fondos para proyectos experimentales, implemente metodologías ágiles y cree equipos multidisciplinarios de innovación. Destine 15% del tiempo laboral a proyectos de innovación digital.\n\n3. Escale el modelo de transformación digital hacia la excelencia operativa. Implemente sistemas de inteligencia empresarial, automatice la toma de decisiones rutinarias y desarrolle capacidades de análisis predictivo. Aumente la inversión en I+D digital al 12-15% de ingresos.\n\n4. Conviértase en un hub de conocimiento digital para el ecosistema empresarial. Cree contenido educativo, desarrolle cursos especializados y establezca alianzas estratégicas con empresas tecnológicas. Genere ingresos adicionales a través de servicios de consultoría digital."
        },
        2: {  # Presencia en Internet y Redes Sociales
            'bajo': "1. Establezca inmediatamente una presencia digital básica. Cree perfiles profesionales en Facebook, Instagram y LinkedIn con información completa, fotos de calidad y descripción clara de servicios. Publique contenido 3 veces por semana y responda mensajes en menos de 4 horas durante horario laboral.\n\n2. Desarrolle un sitio web básico usando plataformas como WordPress, Wix o Squarespace. Incluya información de contacto, servicios, galería de trabajos y testimonios de clientes. Asegúrese de que sea responsive para móviles y actualice el contenido semanalmente.\n\n3. Implemente herramientas básicas de comunicación digital. Configure WhatsApp Business con catálogo de productos, mensajes automáticos y horarios de atención. Cree un correo electrónico empresarial profesional y establezca firmas digitales corporativas.\n\n4. Inicie actividades básicas de marketing digital. Cree contenido visual simple con herramientas como Canva, publique ofertas y promociones regularmente, y use hashtags relevantes para su sector. Dedique 1 hora diaria a interacción en redes sociales.",
            'medio': "1. Fortalezca su estrategia de redes sociales desarrollando un calendario editorial estructurado. Cree contenido diversificado (educativo, promocional, entretenimiento), use herramientas de programación como Hootsuite o Buffer, y analice métricas de engagement mensualmente. Aumente la frecuencia de publicación a 5-7 veces por semana.\n\n2. Optimice su sitio web para mejorar la experiencia del usuario y SEO. Implemente Google Analytics, optimice velocidad de carga, cree contenido de blog relevante y establezca formularios de contacto efectivos. Actualice el contenido 2-3 veces por semana y monitoree el tráfico web.\n\n3. Expanda sus canales de comunicación digital integrando múltiples plataformas. Implemente chatbots básicos, cree newsletters mensuales, use Google My Business activamente y establezca un sistema de CRM simple. Responda a todas las consultas en menos de 2 horas.\n\n4. Desarrolle campañas de marketing digital dirigidas. Use Facebook Ads e Instagram Ads con presupuestos pequeños, cree contenido de video simple, implemente email marketing y colabore con influencers locales. Mida el ROI de cada campaña y ajuste estrategias mensualmente.",
            'alto': "1. Maximice su presencia digital como líder en el sector. Implemente estrategias omnicanal avanzadas, use marketing automation, desarrolle contenido premium y establezca partnerships digitales estratégicos. Conviértase en referente de contenido de su industria con publicaciones diarias de alta calidad.\n\n2. Optimice su ecosistema web con tecnologías avanzadas. Implemente e-commerce completo, use inteligencia artificial para personalización, desarrolle aplicaciones móviles y cree experiencias interactivas. Mantenga métricas de conversión superiores al promedio de la industria.\n\n3. Lidera la innovación en comunicación digital. Implemente realidad aumentada, use chatbots con IA, desarrolle podcasts o webinars especializados y cree comunidades online exclusivas. Genere ingresos adicionales a través de contenido premium y servicios digitales.\n\n4. Escale su impacto digital hacia mercados internacionales. Desarrolle contenido multidioma, use plataformas globales, implemente estratégias de growth hacking y cree alianzas internacionales. Genere al menos 30% de leads a través de canales digitales y mantenga presencia en 5+ plataformas digitales."
        },
        3: {  # Adopción de Tecnologías Emergentes
            'bajo': "1. Comience explorando tecnologías básicas como computación en la nube. Migre el almacenamiento de archivos a Google Drive o OneDrive, implemente herramientas de videoconferencia como Zoom o Teams, y use aplicaciones móviles básicas para gestión empresarial. Dedique 2 horas semanales a investigar nuevas herramientas tecnológicas relevantes para su sector.\n\n2. Establezca un proceso básico de evaluación tecnológica. Cree una lista de necesidades tecnológicas prioritarias, investigue 3 herramientas por mes, realice pruebas gratuitas antes de comprar y documente los resultados. Asigne un responsable para evaluar nuevas tecnologías mensualmente.\n\n3. Inicie la automatización básica con herramientas simples. Use Zapier o Microsoft Power Automate para conectar aplicaciones, automatice respuestas de correo electrónico, implemente formularios digitales y use plantillas automatizadas. Comience con 1-2 procesos simples de automatización.\n\n4. Prepare a su equipo para adoptar nuevas tecnologías. Organice sesiones de demostración de herramientas, cree un fondo básico para experimentación tecnológica (2-3% de ingresos), establezca políticas de prueba de nuevas herramientas y documente lecciones aprendidas.",
            'medio': "1. Expanda el uso de tecnologías emergentes implementando inteligencia artificial básica. Use chatbots simples como Tidio o Intercom, implemente herramientas de análisis predictivo básico, automatice la clasificación de correos y use asistentes virtuales para programación. Invierta 5-8% de ingresos en tecnologías emergentes.\n\n2. Desarrolle capacidades de Internet de las Cosas (IoT). Implemente sensores básicos para monitoreo, use dispositivos inteligentes para control de acceso, automatice el control de iluminación y temperatura, y establezca dashboards de monitoreo en tiempo real. Comience con 2-3 dispositivos IoT básicos.\n\n3. Fortalezca sus capacidades de análisis de datos con herramientas avanzadas. Use Google Analytics 4, implemente Power BI o Tableau, cree reportes automatizados y establezca alertas basadas en datos. Capacite a 2-3 empleados en análisis de datos y dedique 4 horas semanales a análisis.\n\n4. Implemente tecnologías de colaboración avanzada. Use plataformas como Slack o Microsoft Teams, implemente gestión de proyectos con Asana o Monday, use herramientas de co-creación en tiempo real y establezca espacios de trabajo virtuales. Integre todas las herramientas en un ecosistema cohesivo.",
            'alto': "1. Lidere la adopción de tecnologías emergentes en su sector. Implemente inteligencia artificial avanzada, use machine learning para optimización, desarrolle soluciones de realidad aumentada o virtual, y experimente con blockchain para procesos específicos. Destine 12-15% de ingresos a I+D tecnológico.\n\n2. Desarrolle soluciones tecnológicas propias. Cree APIs personalizadas, desarrolle aplicaciones móviles específicas, implemente sistemas de automatización avanzada y use tecnologías de edge computing. Establezca un equipo interno de desarrollo tecnológico.\n\n3. Conviértase en un hub de innovación tecnológica. Organice hackathons, colabore con universidades en proyectos de investigación, participe en incubadoras tecnológicas y comparta conocimiento en conferencias. Genere ingresos adicionales licenciando sus innovaciones.\n\n4. Escale sus capacidades tecnológicas hacia mercados globales. Implemente tecnologías de computación cuántica experimental, use gemelos digitales para optimización, desarrolle soluciones de IA generativa y explore tecnologías emergentes como Web3. Establezca alianzas estratégicas con empresas tecnológicas globales."
        },
        4: {  # Digitalización de Procesos Empresariales
            'bajo': "1. Inicie la digitalización básica de procesos eliminando el papel. Digitalice formularios usando Google Forms o Microsoft Forms, implemente firmas electrónicas con DocuSign o Adobe Sign, use aplicaciones móviles para captura de datos y cree archivos digitales organizados. Comience digitalizando 3 procesos críticos.\n\n2. Implemente un sistema básico de gestión empresarial. Use herramientas como Zoho One, Odoo Community o Monday.com para gestionar clientes, inventario y finanzas básicas. Capacite a todo el equipo en el uso del sistema durante 2 semanas y migre gradualmente todos los procesos.\n\n3. Automatice los procesos más repetitivos. Configure respuestas automáticas de correo, use plantillas para documentos recurrentes, automatice la facturación básica y implemente recordatorios automáticos. Use herramientas como Zapier para conectar diferentes aplicaciones.\n\n4. Establezca flujos de trabajo digitales básicos. Defina procesos paso a paso, asigne responsables digitalmente, cree notificaciones automáticas de tareas pendientes y establezca tiempos límite. Use herramientas como Trello o Asana para gestión básica de flujos de trabajo.",
            'medio': "1. Expanda la digitalización de procesos integrando sistemas avanzados. Implemente un ERP completo como Odoo Enterprise o SAP Business One, integre todos los departamentos en una sola plataforma, automatice reportes financieros y establezca dashboards de control. Invierta en capacitación especializada para el equipo.\n\n2. Desarrolle procesos de automatización inteligente. Use RPA (Robotic Process Automation) con herramientas como UiPath o Automation Anywhere, automatice la entrada de datos, implemente validaciones automáticas y cree flujos de aprobación digitales. Automatice al menos 60% de procesos repetitivos.\n\n3. Implemente gestión avanzada de documentos. Use sistemas como SharePoint o Google Workspace, establezca control de versiones, implemente búsqueda avanzada de documentos y cree bibliotecas digitales organizadas. Elimine completamente el archivo físico y establezca políticas de retención digital.\n\n4. Optimice la experiencia del cliente con procesos digitales. Cree portales de autoservicio, implemente seguimiento en tiempo real de servicios, automatice comunicaciones con clientes y establezca sistemas de feedback digital. Mida la satisfacción del cliente y optimice continuamente los procesos.",
            'alto': "1. Lidere la excelencia en digitalización de procesos en el sector. Implemente procesos completamente autónomos, use inteligencia artificial para optimización continua, desarrolle APIs para integración con partners y cree ecosistemas digitales complejos. Alcance 95% de automatización en procesos rutinarios.\n\n2. Desarrolle capacidades de proceso mining y optimización continua. Use herramientas como Celonis o ProcessGold para analizar procesos, implemente mejora continua basada en datos, use simulación de procesos y establezca optimización predictiva. Reduzca tiempos de proceso en 40-60%.\n\n3. Implemente arquitecturas de microservicios y APIs. Desarrolle servicios modulares, cree integraciones complejas, implemente arquitecturas cloud-native y use contenedores para escalabilidad. Establezca un ecosistema tecnológico que sirva como plataforma para otros negocios.\n\n4. Conviértase en proveedor de soluciones de digitalización para otras empresas. Documente y empaquete sus procesos digitales, ofrezca consultoría especializada, desarrolle software como servicio (SaaS) y cree marketplace de soluciones digitales. Genere ingresos recurrentes vendiendo sus capacidades digitales."
        },
        5: {  # Competencia Digital de Colaboradores
            'bajo': "1. Evalúe urgentemente las competencias digitales básicas de su equipo. Realice un diagnóstico individual de habilidades, identifique brechas críticas en uso de computadoras, internet y aplicaciones básicas. Cree perfiles de competencia por puesto y establezca niveles mínimos requeridos. Documente las necesidades de capacitación de cada empleado.\n\n2. Implemente un programa intensivo de alfabetización digital. Capacite en uso básico de computadoras, navegación en internet, correo electrónico y aplicaciones de oficina. Use tutoriales gratuitos de YouTube, cursos de Google Digital Garage y capacitación presencial básica. Dedique 3 horas semanales por empleado durante 8 semanas.\n\n3. Establezca un sistema de apoyo y mentoría digital. Identifique empleados con mejores habilidades digitales como mentores, cree parejas de aprendizaje, establezca sesiones de práctica supervisada y proporcione soporte técnico básico. Cree un ambiente seguro para hacer preguntas y cometer errores.\n\n4. Cree incentivos y reconocimientos para el aprendizaje digital. Establezca certificaciones básicas internas, reconozca públicamente los avances, ofrezca pequeños bonos por completar capacitaciones y cree competencias amigables de habilidades digitales. Celebre cada logro para mantener la motivación.",
            'medio': "1. Desarrolle un programa estructurado de competencias digitales intermedias. Implemente capacitación en herramientas especializadas del sector, análisis básico de datos, uso avanzado de redes sociales empresariales y colaboración digital. Use plataformas como Coursera, Udemy o LinkedIn Learning. Establezca 4 horas mensuales de capacitación por empleado.\n\n2. Cree rutas de aprendizaje personalizadas para cada rol. Defina competencias específicas por puesto, establezca niveles progresivos de habilidad, cree planes de desarrollo individual y use evaluaciones periódicas. Implemente un sistema de badges o certificaciones internas para reconocer el progreso.\n\n3. Establezca comunidades de práctica digital. Cree grupos de interés por herramientas o temas, organice sesiones de intercambio de conocimiento, implemente wikis internos para documentar aprendizajes y fomente la experimentación colaborativa. Dedique 2 horas mensuales a sesiones de intercambio.\n\n4. Implemente evaluación continua y feedback de competencias digitales. Use herramientas de assessment digital, realice evaluaciones trimestrales, proporcione feedback constructivo y ajuste planes de capacitación según resultados. Vincule el desarrollo digital con evaluaciones de desempeño y planes de carrera.",
            'alto': "1. Posiciónese como centro de excelencia en competencias digitales. Desarrolle programas de certificación avanzada, cree contenido educativo propio, establezca alianzas con universidades y ofrezca capacitación a otras empresas. Convierta las competencias digitales en una ventaja competitiva y fuente de ingresos adicionales.\n\n2. Implemente programas de innovación y experimentación digital liderados por empleados. Establezca fondos para proyectos de innovación, cree laboratorios de experimentación, implemente metodologías de design thinking y fomente el intraemprendimiento digital. Destine 10% del tiempo laboral a proyectos de innovación.\n\n3. Desarrolle capacidades de liderazgo digital en todos los niveles. Capacite en transformación digital, gestión de equipos remotos, toma de decisiones basada en datos y liderazgo de cambio tecnológico. Cree un pipeline de líderes digitales y establezca programas de mentoría inversa donde empleados jóvenes enseñen a directivos.\n\n4. Cree un ecosistema de aprendizaje continuo y adaptativo. Implemente inteligencia artificial para personalizar el aprendizaje, use realidad virtual para capacitación inmersiva, establezca partnerships con empresas tecnológicas globales y cree intercambios internacionales. Mantenga a su equipo en la vanguardia tecnológica mundial."
        },
        6: {  # Gestión de Información y Toma de Decisiones
            'bajo': "1. Establezca un sistema básico de recolección y organización de datos. Implemente herramientas simples como Google Sheets o Excel para registrar información clave de ventas, clientes y operaciones. Cree formularios digitales para capturar datos consistentemente y establezca rutinas diarias de actualización. Capacite a 2-3 empleados en el manejo básico de estas herramientas durante 2 semanas.\n\n2. Desarrolle dashboards simples para visualizar información crítica. Use herramientas gratuitas como Google Data Studio o Power BI para crear reportes visuales de ventas mensuales, satisfacción del cliente y indicadores operativos básicos. Actualice estos reportes semanalmente y revíselos en reuniones gerenciales para tomar decisiones informadas.\n\n3. Implemente procesos básicos de análisis de datos. Identifique 3-5 métricas clave para su negocio, establezca metas numéricas simples y revise el progreso mensualmente. Use análisis básicos como comparaciones mes a mes, identificación de tendencias simples y análisis de causas de variaciones importantes.\n\n4. Cree una cultura de toma de decisiones basada en datos. Establezca la regla de respaldar decisiones importantes con datos, documente las decisiones tomadas y sus resultados, y revise trimestralmente la efectividad de las decisiones. Capacite al equipo directivo en interpretación básica de datos y análisis de tendencias.",
            'medio': "1. Implemente un sistema integrado de business intelligence. Use herramientas como Power BI, Tableau o Zoho Analytics para conectar múltiples fuentes de datos, crear dashboards interactivos y generar reportes automatizados. Establezca KPIs específicos por área y revise el desempeño semanalmente con reportes automatizados.\n\n2. Desarrolle capacidades de análisis predictivo básico. Use herramientas de forecasting para predecir ventas, demanda de productos y necesidades de inventario. Implemente análisis de cohortes para entender el comportamiento del cliente y use análisis de tendencias para identificar oportunidades de crecimiento. Dedique 4 horas semanales a análisis avanzado.\n\n3. Cree un sistema de gestión de datos centralizado. Implemente un data warehouse básico, establezca procesos de limpieza y validación de datos, y cree políticas de calidad de datos. Use herramientas como Google Cloud, AWS o Azure para almacenamiento seguro y accesible de información crítica.\n\n4. Establezca procesos avanzados de toma de decisiones. Implemente metodologías de análisis de decisiones, use técnicas de A/B testing para validar estrategias, y cree comités de datos para decisiones importantes. Capacite al equipo gerencial en análisis estadístico básico y interpretación de datos complejos.",
            'alto': "1. Lidera la excelencia en gestión de datos en el sector. Implemente arquitecturas de datos avanzadas, use machine learning para insights predictivos, desarrolle modelos de análisis propietarios y cree ventajas competitivas basadas en datos. Establezca un equipo dedicado de científicos de datos y analistas especializados.\n\n2. Desarrolle capacidades de inteligencia artificial para toma de decisiones. Implemente algoritmos de machine learning para optimización automática, use procesamiento de lenguaje natural para análisis de sentimientos, y desarrolle sistemas de recomendación personalizados. Invierta 15-20% de ingresos en tecnologías de IA y análisis avanzado.\n\n3. Cree ecosistemas de datos que generen valor para partners. Desarrolle APIs de datos, implemente data monetization strategies, cree marketplace de insights y establezca alianzas estratégicas basadas en intercambio de datos. Genere ingresos adicionales vendiendo insights y análisis especializados.\n\n4. Conviértase en referente de innovación en analytics. Publique estudios de mercado basados en sus datos, participe en conferencias de big data, colabore con universidades en investigación y desarrolle soluciones de analytics como servicio. Establezca centros de excelencia en análisis de datos."
        },
        7: {  # Canales de Venta Online y Experiencia del Usuario
            'bajo': "1. Establezca inmediatamente una presencia básica de ventas online. Cree perfiles de venta en Facebook Marketplace, Instagram Shopping y WhatsApp Business con catálogos de productos completos. Configure métodos de pago simples como transferencias bancarias y use herramientas gratuitas como Linktree para centralizar todos sus canales de venta.\n\n2. Desarrolle un sitio web básico con capacidades de e-commerce. Use plataformas como Shopify, WooCommerce o Tienda Nube para crear una tienda online simple. Incluya fotos de calidad de productos, descripciones claras, precios visibles y formularios de contacto. Asegúrese de que funcione correctamente en dispositivos móviles.\n\n3. Implemente sistemas básicos de atención al cliente digital. Configure respuestas automáticas en WhatsApp Business, cree FAQ en su sitio web, establezca horarios claros de atención y use herramientas como Calendly para programar citas. Responda a consultas en menos de 2 horas durante horario laboral.\n\n4. Inicie actividades básicas de marketing digital para impulsar ventas. Publique contenido de productos regularmente en redes sociales, use hashtags relevantes, colabore con influencers locales pequeños y cree promociones especiales para seguidores. Dedique $50-100 mensuales a publicidad digital básica en Facebook e Instagram.",
            'medio': "1. Optimice su plataforma de e-commerce para mejorar la experiencia del usuario. Implemente búsqueda avanzada de productos, filtros por categorías, sistema de reseñas de clientes y checkout simplificado. Use herramientas como Google Analytics para analizar el comportamiento del usuario y optimizar la conversión. Mantenga una tasa de conversión superior al 2%.\n\n2. Desarrolle estrategias omnicanal integradas. Conecte ventas online y offline, implemente click & collect, cree programas de fidelización digital y use CRM para gestionar clientes across channels. Establezca inventario sincronizado entre todos los canales y ofrezca experiencias consistentes.\n\n3. Implemente herramientas avanzadas de marketing digital. Use email marketing automation, retargeting ads, Google Ads, SEO avanzado y marketing de contenidos. Cree funnels de ventas estructurados, segmente audiencias y personalice comunicaciones. Invierta 8-12% de ingresos en marketing digital y mida ROI de cada canal.\n\n4. Optimice continuamente la experiencia del cliente. Implemente chatbots inteligentes, use herramientas de feedback como surveys post-compra, analice customer journey mapping y optimice puntos de fricción. Mantenga Net Promoter Score superior a 50 y tiempo de respuesta menor a 1 hora.",
            'alto': "1. Lidera la innovación en e-commerce en el sector. Implemente tecnologías emergentes como realidad aumentada para prueba de productos, inteligencia artificial para recomendaciones personalizadas, y voice commerce. Desarrolle aplicaciones móviles nativas y use progressive web apps para experiencias superiores.\n\n2. Cree experiencias de cliente hiperpersonalizadas. Use machine learning para personalización en tiempo real, implemente dynamic pricing, desarrolle productos customizados bajo demanda y cree experiencias inmersivas con VR/AR. Mantenga tasas de conversión superiores al 5% y customer lifetime value 3x superior al promedio.\n\n3. Expanda a mercados internacionales con e-commerce global. Implemente multi-currency, multi-language, logística internacional y compliance con regulaciones globales. Use marketplaces internacionales como Amazon Global, eBay y Alibaba. Genere al menos 25% de ingresos de mercados internacionales.\n\n4. Conviértase en plataforma de e-commerce para otras empresas. Desarrolle marketplace propio, ofrezca servicios de fulfillment, cree APIs para integraciones y establezca programa de afiliados. Genere ingresos recurrentes a través de comisiones, subscripciones y servicios de e-commerce como servicio."
        },
        8: {  # Gestión de Calidad y Ciberseguridad
            'bajo': "1. Implemente medidas básicas de ciberseguridad inmediatamente. Configure contraseñas fuertes y únicas para todas las cuentas, active autenticación de dos factores en servicios críticos, instale antivirus actualizado en todas las computadoras y establezca respaldos automáticos diarios en la nube. Capacite a todo el personal en reconocimiento de phishing y fraudes digitales.\n\n2. Establezca políticas básicas de seguridad digital. Cree un manual simple de buenas prácticas de seguridad, defina roles de acceso a sistemas críticos, establezca protocolos para el uso de dispositivos personales y cree procedimientos básicos para reportar incidentes de seguridad. Revise y actualice estas políticas trimestralmente.\n\n3. Implemente controles básicos de calidad en procesos digitales. Establezca checklists para procesos críticos, cree formularios de verificación de calidad, implemente revisiones por pares en tareas importantes y documente errores comunes para prevención. Use herramientas simples como Google Forms para tracking de calidad.\n\n4. Cree un plan básico de respuesta a incidentes. Identifique contactos de emergencia técnica, establezca procedimientos simples para diferentes tipos de incidentes, cree respaldos de información crítica y defina responsabilidades claras. Practique el plan de respuesta semestralmente con simulacros básicos.",
            'medio': "1. Fortalezca significativamente la ciberseguridad con herramientas avanzadas. Implemente firewall empresarial, sistemas de detección de intrusiones, monitoreo de red 24/7 y gestión centralizada de parches de seguridad. Use herramientas como endpoint protection, email security y web filtering. Realice auditorías de seguridad trimestrales.\n\n2. Desarrolle un programa integral de gestión de riesgos. Realice evaluaciones de riesgo regulares, implemente matriz de riesgos digitales, cree planes de continuidad de negocio y establezca seguros de ciberseguridad. Use frameworks como ISO 27001 básico para estructurar el programa de seguridad.\n\n3. Implemente sistemas avanzados de gestión de calidad digital. Use herramientas de quality management como Monday.com o Asana para tracking, implemente métricas de calidad automatizadas, cree dashboards de indicadores de calidad y establezca procesos de mejora continua. Certifique procesos críticos con estándares de calidad.\n\n4. Establezca capacidades avanzadas de respuesta a incidentes. Cree un equipo de respuesta a incidentes, implemente herramientas de forensics digital, establezca comunicación de crisis y desarrolle playbooks detallados para diferentes escenarios. Realice ejercicios de respuesta a incidentes mensualmente.",
            'alto': "1. Lidera la excelencia en ciberseguridad en el sector. Implemente security operations center (SOC), use threat intelligence avanzada, desarrolle capacidades de ethical hacking interno y cree programas de bug bounty. Obtenga certificaciones como ISO 27001, SOC 2 y ofrezca servicios de ciberseguridad a otras empresas.\n\n2. Desarrolle capacidades de ciberseguridad de nivel empresarial. Implemente zero trust architecture, use inteligencia artificial para detección de amenazas, desarrolle capacidades de threat hunting y cree red team interno. Invierta 10-15% de presupuesto IT en ciberseguridad y mantenga cyber resilience superior.\n\n3. Conviértase en referente de calidad digital. Implemente quality 4.0 con IoT y AI, use digital twins para optimización de calidad, desarrolle predictive quality analytics y cree sistemas de calidad autónomos. Publique benchmarks de calidad de la industria y ofrezca consultoría en calidad digital.\n\n4. Cree ecosistemas de seguridad y calidad que generen valor. Desarrolle threat intelligence sharing, cree comunidades de práctica en ciberseguridad, establezca partnerships con vendors de seguridad y genere ingresos adicionales con servicios de security as a service. Lidera iniciativas de ciberseguridad sectorial."
        },
        9: {  # Inversión en Tecnología
            'bajo': "1. Establezca un presupuesto básico dedicado para tecnología. Destine al menos 3-5% de ingresos mensuales para inversiones tecnológicas, cree una cuenta separada para gastos de tecnología y priorice inversiones según necesidades críticas. Comience con herramientas básicas como software de contabilidad, antivirus y almacenamiento en la nube.\n\n2. Desarrolle un proceso simple de evaluación de inversiones tecnológicas. Cree una lista de necesidades tecnológicas prioritarias, investigue 2-3 opciones para cada necesidad, compare costos vs beneficios básicos y documente decisiones de compra. Establezca criterios simples como facilidad de uso, costo mensual y soporte técnico disponible.\n\n3. Busque fuentes de financiamiento básico para tecnología. Investigue programas gubernamentales de apoyo a PYMEs, explore opciones de financiamiento de proveedores tecnológicos, considere leasing de equipos costosos y evalúe créditos bancarios específicos para tecnología. Mantenga un registro de todas las opciones de financiamiento disponibles.\n\n4. Implemente un sistema básico de seguimiento de ROI tecnológico. Documente el costo de cada herramienta tecnológica, mida beneficios simples como tiempo ahorrado o errores reducidos, y revise trimestralmente si cada inversión está generando valor. Cree un registro simple de inversiones tecnológicas y sus resultados.",
            'medio': "1. Desarrolle una estrategia integral de inversión tecnológica. Cree un plan tecnológico a 2-3 años, establezca roadmap de inversiones por prioridad, aumente el presupuesto tecnológico al 8-12% de ingresos y diversifique inversiones entre software, hardware e infraestructura. Revise y ajuste la estrategia semestralmente.\n\n2. Implemente procesos avanzados de evaluación de ROI tecnológico. Use métricas financieras como NPV y payback period, mida impactos cualitativos como satisfacción del cliente, implemente tracking de productividad por herramienta y cree dashboards de performance tecnológico. Establezca KPIs específicos para cada inversión tecnológica.\n\n3. Diversifique fuentes de financiamiento para tecnología. Explore venture capital para startups tecnológicas, considere partnerships estratégicos con proveedores, evalúe opciones de equity financing y cree fondos internos de innovación. Mantenga un portfolio balanceado entre inversiones de bajo y alto riesgo.\n\n4. Cree un centro de excelencia tecnológica. Establezca un equipo dedicado para evaluación tecnológica, implemente procesos de innovation management, cree laboratorios de prueba para nuevas tecnologías y desarrolle capacidades de technology scouting. Invierta en capacitación especializada del equipo tecnológico.",
            'alto': "1. Lidera la inversión estratégica en tecnología en el sector. Desarrolle capacidades de venture capital interno, cree fondos de corporate venture capital, invierta en startups tecnológicas complementarias y establezca aceleradoras de innovación. Destine 15-20% de ingresos a inversiones tecnológicas estratégicas y genere retornos superiores al 25% anual.\n\n2. Conviértase en technology investor y advisor para otras empresas. Ofrezca servicios de consultoría en inversión tecnológica, cree fondos de inversión especializados en tecnología, desarrolle expertise en due diligence tecnológico y establezca network de inversores tecnológicos. Genere ingresos adicionales a través de advisory fees y carried interest.\n\n3. Desarrolle ecosistemas de innovación tecnológica. Cree innovation hubs, establezca partnerships con universidades para I+D, desarrolle programas de open innovation y cree marketplace de tecnologías. Lidera consorcios de innovación sectorial y participa en iniciativas de smart cities o industry 4.0.\n\n4. Cree valor a través de intellectual property y technology licensing. Desarrolle patentes propias, cree portfolio de IP, establezca licensing agreements y genere ingresos recurrentes a través de royalties. Invierta en technology transfer offices y desarrolle capacidades de commercialization de tecnologías propias."
        },
        10: {  # Protección de Datos y Propiedad Intelectual
            'bajo': "1. Implemente políticas básicas de protección de datos inmediatamente. Cree procedimientos simples para manejo de información de clientes, establezca controles de acceso básicos a datos sensibles, implemente respaldos seguros de información crítica y capacite al personal en principios básicos de privacidad. Use herramientas como Google Drive con permisos restringidos para almacenamiento seguro.\n\n2. Establezca cumplimiento básico con regulaciones de protección de datos. Investigue las leyes locales de protección de datos, cree avisos de privacidad simples para clientes, implemente procesos básicos de consentimiento y establezca procedimientos para solicitudes de información personal. Consulte con abogado especializado en protección de datos.\n\n3. Inicie la protección básica de propiedad intelectual. Documente y registre marcas comerciales básicas, proteja logos y nombres comerciales, cree contratos simples de confidencialidad para empleados y establezca políticas básicas de uso de información propietaria. Registre dominios web relevantes para proteger la marca.\n\n4. Cree procedimientos básicos de manejo de información sensible. Clasifique información según nivel de sensibilidad, establezca protocolos simples para compartir información, implemente destrucción segura de documentos físicos y digitales, y cree políticas básicas de uso de dispositivos personales. Capacite al personal en manejo seguro de información.\n\n",
            'medio': "1. Fortalezca significativamente el sistema de protección de datos. Implemente data loss prevention (DLP), use encryption para datos sensibles, establezca access controls granulares y cree audit trails completos. Implemente herramientas como Microsoft Information Protection o Google Cloud DLP para protección automatizada de datos.\n\n2. Desarrolle compliance avanzado con regulaciones de privacidad. Implemente frameworks como GDPR o CCPA según aplicabilidad, cree privacy impact assessments, establezca data protection officer role y desarrolle procesos de breach notification. Realice auditorías de privacidad semestrales y mantenga documentación completa de compliance.\n\n3. Cree una estrategia integral de protección de propiedad intelectual. Desarrolle portfolio de patentes, implemente trade secret protection, cree licensing agreements y establezca IP monitoring systems. Use herramientas de IP management y trabaje con abogados especializados en propiedad intelectual para protección avanzada.\n\n4. Implemente data governance avanzado. Cree data stewardship roles, establezca data quality management, implemente master data management y desarrolle data lineage tracking. Use herramientas como Collibra o Informatica para governance automatizado y establezca data governance council.\n\n",
            'alto': "1. Lidera la excelencia en protección de datos en el sector. Implemente privacy by design en todos los procesos, use privacy-enhancing technologies como differential privacy, desarrolle zero-knowledge architectures y cree privacy-preserving analytics. Obtenga certificaciones como ISO 27701 y ofrezca servicios de privacy consulting.\n\n2. Desarrolle capacidades de data governance de nivel empresarial. Implemente data fabric architectures, use AI para data discovery y classification, desarrolle automated compliance monitoring y cree self-service data governance. Establezca data governance as a service para otras empresas y genere ingresos adicionales.\n\n3. Conviértase en innovador en protección de propiedad intelectual. Desarrolle blockchain-based IP protection, use AI para patent analytics, cree IP monetization strategies y establezca IP-backed financing. Genere ingresos significativos a través de licensing, IP sales y IP-as-a-service offerings.\n\n4. Cree ecosistemas de datos que generen valor mientras protegen privacidad. Desarrolle privacy-preserving data sharing, implemente federated learning, cree data trusts y establezca data cooperatives. Lidera iniciativas de responsible AI y ethical data use en su sector, generando ventaja competitiva a través de trust y transparency."
        }
    }
    
    prompt = f"""
    Eres un consultor senior especializado en estrategia digital para emprendimientos en etapa de gestación en Latinoamérica.
    
    EMPRENDIMIENTO ANALIZADO:
    Tipo/Industria: {tipo_empresa}
    Etapa: {tamano_empresa if tamano_empresa else 'No especificado'}
    Vector evaluado: {eje_nombre}
    Puntaje obtenido: {puntaje}/4
    Nivel de preparación: {enfoque}
    
    CONTEXTO DEL PUNTAJE:
    {contexto_puntaje}
    
    CONTEXTO DE ETAPAS DE EMPRENDIMIENTO:
    - Ideación (0-1 puntos): Solo idea, necesita establecer todo desde cero, recursos mínimos
    - MVP en desarrollo (2 puntos): Construyendo prototipo, necesita estructurar vectores digitales
    - MVP lanzado (3 puntos): Primeros usuarios/clientes, necesita consolidar y optimizar
    - Tracción temprana (4 puntos): Validación inicial, listo para escalar capacidades digitales
    
    RESPUESTAS DE LA EVALUACIÓN:
    {json.dumps(respuestas, indent=2)}
    
    INSTRUCCIONES:
    Basado en el puntaje de {puntaje}/4 y la etapa {tamano_empresa if tamano_empresa else 'No especificado'}, genera 4 recomendaciones de ACCIONES PARA ESTABLECER este vector:
    
    - Si es ESTABLECIMIENTO INICIAL (0-2 puntos): Acciones fundamentales para crear el vector desde cero
    - Si es CONSOLIDACIÓN (3 puntos): Acciones para estructurar y formalizar el vector
    - Si es AVANZADO (4 puntos): Acciones para escalar y optimizar el vector establecido
    
    ENFOQUE: Las recomendaciones deben ser sobre ESTABLECER/CREAR (no mejorar lo existente), considerando que es un emprendimiento nuevo.
    
    CADA RECOMENDACIÓN DEBE:
    - Ser accionable para el emprendimiento (industria: {tipo_empresa}, etapa: {tamano_empresa if tamano_empresa else 'No especificado'})
    - Considerar presupuesto limitado típico de startups
    - Incluir herramientas accesibles o gratuitas cuando sea posible
    - Ser implementable con equipo pequeño/fundadores
    - Enfocarse en ESTABLECER el vector (no mejorar lo existente)
    - 70-90 palabras por recomendación
    - NO repetir el nombre o tipo de empresa en cada recomendación - usar redacción fluida y directa
    
    FORMATO REQUERIDO (sin repetir tipo de empresa en cada punto):
    1. [Acción específica y directa para ESTABLECER este vector]
    
    2. [Acción específica y directa para ESTABLECER este vector]
    
    3. [Acción específica y directa para ESTABLECER este vector]
    
    4. [Acción específica y directa para ESTABLECER este vector]
    
    IMPORTANTE: Evite frases como "para su empresa", "en su negocio", "su emprendimiento" repetidamente. Use redacción directa en imperativo.
    """
    
    # Debug: verificar estado de Gemini
    logger.info(f"Estado de Gemini: {'Disponible' if model else 'No disponible'}")
    logger.info(f"Generando recomendaciones para eje {eje_id}, empresa: {tipo_empresa}")
    
    # Siempre intentar usar Gemini primero
    if model is not None:
        try:
            logger.info("Enviando prompt a Gemini...")
            response = model.generate_content(prompt)
            logger.info(f"Respuesta recibida de Gemini: {len(response.text) if response.text else 0} caracteres")
            
            if response.text and len(response.text.strip()) > 200:
                logger.info("="*50)
                logger.info("✅ USANDO GEMINI AI PARA RECOMENDACIONES")
                logger.info(f"Eje: {eje_id}, Empresa: {tipo_empresa}, Nivel: {nivel}")
                logger.info("="*50)
                return f"*G\n\n{response.text}"
            else:
                logger.warning(f"Respuesta de Gemini muy corta ({len(response.text) if response.text else 0} chars), usando recomendaciones por defecto")
                if response.text:
                    logger.warning(f"Contenido recibido: {response.text[:100]}...")
        except Exception as e:
            logger.error(f"Error con Gemini: {str(e)}")
    else:
        logger.warning("Modelo Gemini no está disponible")
    
    # Usar recomendaciones específicas por eje y puntaje
    logger.info("="*50)
    logger.info("📋 USANDO RECOMENDACIONES PREDEFINIDAS")
    logger.info(f"Eje: {eje_id}, Nivel: {nivel_dict}, Empresa: {tipo_empresa}")
    logger.info("="*50)
    
    if eje_id in recomendaciones_por_eje:
        return f"*P\n\n{recomendaciones_por_eje[eje_id][nivel_dict]}"
    else:
        return f"*P\n\n{recomendaciones_genericas.get(eje_id, f'Recomendaciones para {eje_nombre} en {tipo_empresa} con enfoque de {enfoque}.')}"

@app.route('/')
def index():
    # Limpiar sesión si es necesario
    if request.args.get('reset') == '1':
        session.clear()
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    nombre_empresa = data.get('nombre_empresa')
    tipo_empresa = data.get('tipo_empresa')
    tamano_empresa = data.get('tamano_empresa')
    
    # Verificar si es consultor
    es_consultor = (email == 'alejandroaguilar1000@gmail.com' and nombre_empresa == 'consultor1')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if es_consultor:
        # Para consultor: siempre crear/actualizar sin cargar datos anteriores
        c.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
        usuario_existente = c.fetchone()
        
        if usuario_existente:
            # Actualizar datos del consultor
            c.execute('UPDATE usuarios SET nombre_empresa = ?, tipo_empresa = ?, tamano_empresa = ? WHERE email = ?',
                      (nombre_empresa, tipo_empresa, tamano_empresa, email))
            usuario_id = usuario_existente[0]
        else:
            # Crear nuevo consultor
            c.execute('INSERT INTO usuarios (email, nombre_empresa, tipo_empresa, tamano_empresa) VALUES (?, ?, ?, ?)',
                      (email, nombre_empresa, tipo_empresa, tamano_empresa))
            usuario_id = c.lastrowid
        
        session['usuario_id'] = usuario_id
        session['email'] = email
        session['nombre_empresa'] = nombre_empresa
        session['tipo_empresa'] = tipo_empresa
        session['tamano_empresa'] = tamano_empresa
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'usuario_existente': False,  # Siempre como nuevo para no cargar datos
            'evaluaciones': {},
            'es_consultor': True
        })
    
    else:
        # Para usuarios normales: comportamiento original
        c.execute('SELECT id, email, nombre_empresa, tipo_empresa, tamano_empresa FROM usuarios WHERE email = ?', (email,))
        usuario = c.fetchone()
        
        if usuario:
            # Actualizar datos del usuario existente con los nuevos valores del formulario
            c.execute('UPDATE usuarios SET nombre_empresa = ?, tipo_empresa = ?, tamano_empresa = ? WHERE email = ?',
                      (nombre_empresa, tipo_empresa, tamano_empresa, email))
            
            session['usuario_id'] = usuario[0]
            session['email'] = usuario[1]
            session['nombre_empresa'] = nombre_empresa  # Usar valor del formulario
            session['tipo_empresa'] = tipo_empresa      # Usar valor del formulario
            session['tamano_empresa'] = tamano_empresa  # Usar valor del formulario
            
            # Debug: verificar el valor de tamano_empresa
            logger.info(f"Tamano empresa actualizado: {session['tamano_empresa']}")
            
            # Obtener evaluaciones existentes
            c.execute('SELECT eje_id, puntaje FROM evaluaciones WHERE usuario_id = ?', (usuario[0],))
            evaluaciones = {row[0]: row[1] for row in c.fetchall()}
            
            conn.commit()
            conn.close()
            return jsonify({
                'success': True,
                'usuario_existente': True,
                'nombre_empresa': nombre_empresa,
                'tipo_empresa': tipo_empresa,
                'tamano_empresa': tamano_empresa,
                'evaluaciones': evaluaciones
            })
        else:
            # Crear nuevo usuario
            c.execute('INSERT INTO usuarios (email, nombre_empresa, tipo_empresa, tamano_empresa) VALUES (?, ?, ?, ?)',
                      (email, nombre_empresa, tipo_empresa, tamano_empresa))
            usuario_id = c.lastrowid
            
            session['usuario_id'] = usuario_id
            session['email'] = email
            session['nombre_empresa'] = nombre_empresa
            session['tipo_empresa'] = tipo_empresa
            session['tamano_empresa'] = tamano_empresa
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'usuario_existente': False,
                'evaluaciones': {}
            })

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT eje_id, puntaje FROM evaluaciones WHERE usuario_id = ?', (session['usuario_id'],))
    evaluaciones = {row[0]: row[1] for row in c.fetchall()}
    
    # Obtener objetivos de negocio
    c.execute('SELECT objetivo1, objetivo2, objetivo3 FROM objetivos_negocio WHERE usuario_id = ?', (session['usuario_id'],))
    objetivos_result = c.fetchone()
    tiene_objetivos = objetivos_result is not None
    
    # Verificar si es consultor
    es_consultor = (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
                   session.get('nombre_empresa') == 'consultor1')
    
    conn.close()
    
    return render_template('dashboard.html', 
                         ejes=EJES_EVALUACION, 
                         evaluaciones=evaluaciones,
                         nombre_empresa=session.get('nombre_empresa'),
                         tiene_evaluaciones=len(evaluaciones) > 0,
                         tiene_objetivos=tiene_objetivos,
                         es_consultor=es_consultor)

@app.route('/objetivos_negocio')
def objetivos_negocio():
    if 'usuario_id' not in session:
        return redirect('/')
    
    # Obtener objetivos existentes
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT objetivo1, objetivo2, objetivo3 FROM objetivos_negocio WHERE usuario_id = ?', (session['usuario_id'],))
    resultado = c.fetchone()
    conn.close()
    
    objetivos_anteriores = {
        'objetivo1': resultado[0] if resultado and resultado[0] else '',
        'objetivo2': resultado[1] if resultado and resultado[1] else '',
        'objetivo3': resultado[2] if resultado and resultado[2] else ''
    }
    
    return render_template('objetivos_negocio.html', objetivos_anteriores=objetivos_anteriores)

@app.route('/guardar_objetivos', methods=['POST'])
def guardar_objetivos():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    data = request.json
    objetivo1 = data.get('objetivo1', '').strip()
    objetivo2 = data.get('objetivo2', '').strip()
    objetivo3 = data.get('objetivo3', '').strip()
    
    # Validar que al menos un objetivo esté completo
    if not objetivo1:
        return jsonify({'success': False, 'error': 'Debe completar al menos el primer objetivo'})
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Verificar si ya existen objetivos
    c.execute('SELECT id FROM objetivos_negocio WHERE usuario_id = ?', (session['usuario_id'],))
    existe = c.fetchone()
    
    if existe:
        # Actualizar objetivos existentes
        c.execute('''UPDATE objetivos_negocio 
                     SET objetivo1 = ?, objetivo2 = ?, objetivo3 = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                     WHERE usuario_id = ?''',
                  (objetivo1, objetivo2, objetivo3, session['usuario_id']))
    else:
        # Insertar nuevos objetivos
        c.execute('''INSERT INTO objetivos_negocio (usuario_id, objetivo1, objetivo2, objetivo3) 
                     VALUES (?, ?, ?, ?)''',
                  (session['usuario_id'], objetivo1, objetivo2, objetivo3))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/reportes_consultor')
def reportes_consultor():
    if 'usuario_id' not in session:
        return redirect('/')
    
    # Verificar acceso de consultor
    if not (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
            session.get('nombre_empresa') == 'consultor1'):
        return redirect('/dashboard')
    
    # Obtener todos los usuarios con sus datos
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT u.id, u.email, u.nombre_empresa, u.tipo_empresa, u.tamano_empresa,
                        COUNT(e.id) as num_evaluaciones
                 FROM usuarios u 
                 LEFT JOIN evaluaciones e ON u.id = e.usuario_id
                 WHERE u.email != 'alejandroaguilar1000@gmail.com'
                 GROUP BY u.id, u.email, u.nombre_empresa, u.tipo_empresa, u.tamano_empresa
                 ORDER BY u.fecha_registro DESC''')
    usuarios = c.fetchall()
    conn.close()
    
    return render_template('reportes_consultor.html', usuarios=usuarios)

@app.route('/generar_informe_cliente/<int:usuario_id>')
def generar_informe_cliente(usuario_id):
    if not (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
            session.get('nombre_empresa') == 'consultor1'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    # Obtener datos del usuario
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT email, nombre_empresa, tipo_empresa, tamano_empresa FROM usuarios WHERE id = ?', (usuario_id,))
    usuario = c.fetchone()
    
    if not usuario:
        conn.close()
        return render_template('error.html', 
                             mensaje='Usuario no encontrado',
                             descripcion='El usuario solicitado no existe en el sistema.'), 404
    
    # Obtener evaluaciones
    c.execute('SELECT eje_id, respuestas, puntaje FROM evaluaciones WHERE usuario_id = ?', (usuario_id,))
    evaluaciones = c.fetchall()
    conn.close()
    
    if not evaluaciones:
        return render_template('error.html', 
                             mensaje='Usuario no ha llenado la información',
                             descripcion=f'El usuario {usuario[1]} ({usuario[0]}) aún no ha completado ninguna evaluación de los ejes de madurez digital.'), 404
    
    # Verificar que tenga al menos 3 vectores completados
    if len(evaluaciones) < 3:
        return render_template('error.html', 
                             mensaje='Reporte ejecutivo aún no disponible',
                             descripcion=f'El usuario {usuario[1]} ({usuario[0]}) ha completado {len(evaluaciones)} vector(es). Se requieren mínimo 3 vectores para generar el reporte ejecutivo.'), 400
    
    # Generar informe similar al ejecutivo pero para el cliente
    return generar_pdf_cliente(usuario, evaluaciones)

@app.route('/generar_plan_consultoria/<int:usuario_id>')
def generar_plan_consultoria(usuario_id):
    if not (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
            session.get('nombre_empresa') == 'consultor1'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    # Obtener datos completos del usuario
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT email, nombre_empresa, tipo_empresa, tamano_empresa FROM usuarios WHERE id = ?', (usuario_id,))
    usuario = c.fetchone()
    
    if not usuario:
        conn.close()
        return render_template('error.html', 
                             mensaje='Usuario no encontrado',
                             descripcion='El usuario solicitado no existe en el sistema.'), 404
    
    # Obtener evaluaciones
    c.execute('SELECT eje_id, respuestas, puntaje FROM evaluaciones WHERE usuario_id = ?', (usuario_id,))
    evaluaciones = c.fetchall()
    
    # Obtener objetivos
    c.execute('SELECT objetivo1, objetivo2, objetivo3 FROM objetivos_negocio WHERE usuario_id = ?', (usuario_id,))
    objetivos = c.fetchone()
    
    conn.close()
    
    if not evaluaciones:
        return render_template('error.html', 
                             mensaje='Usuario no ha llenado la información',
                             descripcion=f'El usuario {usuario[1]} ({usuario[0]}) aún no ha completado ninguna evaluación de los ejes de madurez digital.'), 404
    
    # Verificar que tenga al menos 3 vectores completados
    if len(evaluaciones) < 3:
        return render_template('error.html', 
                             mensaje='Reporte ejecutivo aún no disponible',
                             descripcion=f'El usuario {usuario[1]} ({usuario[0]}) ha completado {len(evaluaciones)} vector(es). Se requieren mínimo 3 vectores para generar el plan de consultoría.'), 400
    
    return generar_pdf_consultoria(usuario, evaluaciones, objetivos)

@app.route('/eliminar_usuario/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario(usuario_id):
    if not (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
            session.get('nombre_empresa') == 'consultor1'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Eliminar en orden (por foreign keys)
    c.execute('DELETE FROM evaluaciones WHERE usuario_id = ?', (usuario_id,))
    c.execute('DELETE FROM objetivos_negocio WHERE usuario_id = ?', (usuario_id,))
    c.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/backup_database')
def backup_database():
    """Descargar backup de la base de datos"""
    if not (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
            session.get('nombre_empresa') == 'consultor1'):
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    try:
        # Verificar que existe la base de datos
        if not os.path.exists(DB_PATH):
            return jsonify({'error': 'Base de datos no encontrada'}), 404
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'rutadigital_backup_{timestamp}.db'
        
        # Enviar el archivo directamente
        return send_file(DB_PATH, 
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/x-sqlite3')
    except Exception as e:
        logger.error(f"Error al crear backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/restore_database', methods=['POST'])
def restore_database():
    """Restaurar base de datos desde un archivo de backup"""
    if not (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
            session.get('nombre_empresa') == 'consultor1'):
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    try:
        # Verificar que se envió un archivo
        if 'backup_file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió ningún archivo'}), 400
        
        file = request.files['backup_file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400
        
        # Verificar extensión
        if not file.filename.endswith(('.db', '.sqlite', '.sqlite3')):
            return jsonify({'success': False, 'error': 'Formato de archivo no válido'}), 400
        
        # Crear backup del archivo actual antes de restaurar
        if os.path.exists(DB_PATH):
            backup_path = DB_PATH + '.pre_restore_backup'
            import shutil
            shutil.copy2(DB_PATH, backup_path)
            logger.info(f"Backup de seguridad creado en: {backup_path}")
        
        # Guardar el archivo subido temporalmente
        temp_path = DB_PATH + '.temp_restore'
        file.save(temp_path)
        
        # Verificar que es una base de datos SQLite válida
        try:
            test_conn = sqlite3.connect(temp_path)
            test_cursor = test_conn.cursor()
            
            # Verificar que tiene las tablas necesarias
            test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in test_cursor.fetchall()]
            
            required_tables = ['usuarios', 'evaluaciones']
            if not all(table in tables for table in required_tables):
                test_conn.close()
                os.remove(temp_path)
                return jsonify({'success': False, 'error': 'El archivo no contiene las tablas necesarias'}), 400
            
            # Contar registros
            test_cursor.execute('SELECT COUNT(*) FROM usuarios')
            usuarios_count = test_cursor.fetchone()[0]
            
            test_cursor.execute('SELECT COUNT(*) FROM evaluaciones')
            evaluaciones_count = test_cursor.fetchone()[0]
            
            test_conn.close()
            
        except sqlite3.DatabaseError as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'success': False, 'error': f'Archivo de base de datos corrupto: {str(e)}'}), 400
        
        # Reemplazar la base de datos actual
        import shutil
        shutil.move(temp_path, DB_PATH)
        
        logger.info(f"Base de datos restaurada exitosamente. Usuarios: {usuarios_count}, Evaluaciones: {evaluaciones_count}")
        
        return jsonify({
            'success': True,
            'usuarios': usuarios_count,
            'evaluaciones': evaluaciones_count
        })
        
    except Exception as e:
        logger.error(f"Error al restaurar base de datos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/emergency_backup_db_download')
def emergency_backup_db_download():
    """Endpoint de emergencia para descargar backup de la base de datos"""
    if not (session.get('email') == 'alejandroaguilar1000@gmail.com' and 
            session.get('nombre_empresa') == 'consultor1'):
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    try:
        # Verificar que existe la base de datos
        if not os.path.exists('diagnostico.db'):
            return jsonify({'error': 'Base de datos no encontrada'}), 404
        
        # Enviar el archivo directamente
        return send_file('diagnostico.db', 
                        as_attachment=True,
                        download_name=f'diagnostico_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db',
                        mimetype='application/x-sqlite3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generar_pdf_cliente(usuario, evaluaciones):
    from datetime import datetime
    from reportlab.platypus import PageBreak
    
    email, nombre_empresa, tipo_empresa, tamano_empresa = usuario
    
    # Generar resumen ejecutivo
    resumen_ejecutivo = generar_resumen_ejecutivo(evaluaciones, tipo_empresa, tamano_empresa)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # === PORTADA ===
    story.append(Paragraph("<b>Transformacion Digital AA+</b>", 
                          ParagraphStyle('Header', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue, alignment=1)))
    story.append(Paragraph("Diagnóstico de Madurez Digital", 
                          ParagraphStyle('Subheader', parent=styles['Normal'], fontSize=14, textColor=colors.darkblue, alignment=1, spaceAfter=30)))
    
    # Título principal
    story.append(Paragraph("RESUMEN EJECUTIVO", 
                          ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.darkblue, alignment=1, spaceAfter=20)))
    
    # Información de la empresa
    story.append(Paragraph(f"<b>Empresa:</b> {nombre_empresa}", styles['Normal']))
    story.append(Paragraph(f"<b>Tipo de empresa:</b> {tipo_empresa}", styles['Normal']))
    story.append(Paragraph(f"<b>Tamaño:</b> {tamano_empresa}", styles['Normal']))
    story.append(Paragraph(f"<b>Email:</b> {email}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Puntuaciones por eje
    story.append(Paragraph("Puntuaciones por Eje de Evaluación", 
                          ParagraphStyle('ScoreTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=10)))
    
    for eje_id, _, puntaje in evaluaciones:
        story.append(Paragraph(f"<b>{EJES_EVALUACION[eje_id]['nombre']}:</b> {puntaje}/5", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Resumen ejecutivo
    story.append(Paragraph("Análisis y Recomendaciones Estratégicas", 
                          ParagraphStyle('AnalysisTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=15)))
    
    for linea in resumen_ejecutivo.split('\n'):
        if linea.strip():
            story.append(Paragraph(linea.strip(), styles['Normal']))
            story.append(Spacer(1, 6))
    
    # Salto de página después del resumen ejecutivo
    story.append(PageBreak())
    
    # Reportes individuales de cada eje en páginas separadas
    for i, (eje_id, respuestas_json, puntaje) in enumerate(evaluaciones):
        respuestas = json.loads(respuestas_json)
        recomendaciones = generar_recomendaciones(eje_id, respuestas, tipo_empresa, puntaje, tamano_empresa)
        
        # Salto de página antes de cada eje
        if i > 0:
            story.append(PageBreak())
        
        # Encabezado del eje
        story.append(Paragraph("<b>Transformacion Digital AA+</b>", 
                              ParagraphStyle('Header', parent=styles['Heading1'], fontSize=16, textColor=colors.darkblue, alignment=1)))
        story.append(Paragraph("Diagnóstico de Madurez Digital", 
                              ParagraphStyle('Subheader', parent=styles['Normal'], fontSize=12, textColor=colors.darkblue, alignment=1, spaceAfter=20)))
        
        # Título del eje
        story.append(Paragraph(EJES_EVALUACION[eje_id]['nombre'], 
                              ParagraphStyle('EjeTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.darkblue, alignment=1, spaceAfter=10)))
        
        # Línea divisoria
        story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=20))
        
        # Información de la empresa y puntaje
        story.append(Paragraph(f"<b>Empresa:</b> {nombre_empresa}", styles['Normal']))
        story.append(Paragraph(f"<b>Tipo de empresa:</b> {tipo_empresa}", styles['Normal']))
        story.append(Paragraph(f"<b>Tamaño:</b> {tamano_empresa}", styles['Normal']))
        story.append(Paragraph(f"<b>Puntaje obtenido:</b> <font size=16 color=blue><b>{puntaje}/5</b></font>", 
                              ParagraphStyle('PuntajeStyle', parent=styles['Normal'], fontSize=14, alignment=1, spaceAfter=20)))
        
        story.append(Spacer(1, 20))
        
        # Recomendaciones estratégicas
        story.append(Paragraph("Recomendaciones Estratégicas", 
                              ParagraphStyle('RecomTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=15)))
        
        # Línea divisoria antes de recomendaciones
        story.append(HRFlowable(width="100%", thickness=1, color=colors.lightblue, spaceAfter=15))
        
        # Formatear recomendaciones
        recom_style = ParagraphStyle('RecomStyle', parent=styles['Normal'], fontSize=11, spaceAfter=12, 
                                    leftIndent=15, rightIndent=15, alignment=0)
        
        for linea in recomendaciones.split('\n'):
            if linea.strip():
                story.append(Paragraph(linea.strip(), recom_style))
        
        # Línea divisoria final
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=10))
        
        # Pie de página del eje
        story.append(Paragraph(f"Eje {i+1} de {len(evaluaciones)} | {EJES_EVALUACION[eje_id]['nombre']}", 
                              ParagraphStyle('EjeFooter', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1)))
    
    # Pie de página final
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Informe generado el {datetime.now().strftime('%d/%m/%Y')} | Transformacion Digital AA+", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1)))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'informe_cliente_{nombre_empresa.replace(" ", "_")}.pdf'
    )

def generar_plan_consultoria_gemini(nombre_empresa, tipo_empresa, tamano_empresa, evaluaciones, objetivos):
    """Genera un plan de consultoría detallado usando Gemini AI"""
    
    # Preparar datos de evaluaciones
    ejes_evaluados = []
    puntajes = []
    for eje_id, _, puntaje in evaluaciones:
        ejes_evaluados.append({
            'nombre': EJES_EVALUACION[eje_id]['nombre'],
            'puntaje': puntaje,
            'eje_id': eje_id
        })
        puntajes.append(puntaje)
    
    promedio_general = round(sum(puntajes) / len(puntajes), 1)
    ejes_criticos = sorted(ejes_evaluados, key=lambda x: x['puntaje'])[:3]
    
    # Preparar objetivos
    objetivos_texto = ""
    if objetivos and any(objetivos):
        objetivos_lista = []
        if objetivos[0]: objetivos_lista.append(f"1. {objetivos[0]}")
        if objetivos[1]: objetivos_lista.append(f"2. {objetivos[1]}")
        if objetivos[2]: objetivos_lista.append(f"3. {objetivos[2]}")
        objetivos_texto = "\n".join(objetivos_lista)
    else:
        objetivos_texto = "No se proporcionaron objetivos específicos"
    
    prompt = f"""
    Eres un consultor senior especializado en transformación digital para PYMEs en Costa Rica y Centroamérica.
    
    INFORMACIÓN DEL CLIENTE:
    - Empresa: {nombre_empresa}
    - Tipo: {tipo_empresa}
    - Tamaño: {tamano_empresa}
    - Madurez digital: {promedio_general}/5
    
    RESTRICCIONES ESTRICTAS POR TAMAÑO:
    
    SI ES MICROEMPRESA (1-10 empleados):
    - Duración MÁXIMA: 2-4 semanas
    - Presupuesto MÁXIMO: $500-2000 total
    - Solo herramientas GRATUITAS o muy básicas
    - 1 persona máximo dedicada al proyecto
    - Enfoque en lo ESENCIAL únicamente
    
    SI ES PEQUEÑA (11-50 empleados):
    - Duración MÁXIMA: 6-20 semanas
    - Presupuesto MÁXIMO: $2000-8000 total
    - SaaS básicos y accesibles
    - 2-3 personas involucradas
    - Implementación gradual
    
    SI ES MEDIANA (51-200 empleados):
    - Duración MÁXIMA: 3-10 meses
    - Presupuesto MÁXIMO: $8000-25000 total
    - Sistemas integrados
    - Equipo dedicado pequeño
    - Transformación estructurada
    
    SI ES GRANDE (200+ empleados):
    - Duración MÁXIMA: 6-18 meses
    - Presupuesto MÁXIMO: $25000+ total
    - Soluciones empresariales
    - Departamento IT completo
    - Transformación integral
    
    EVALUACIONES POR EJE:
    {chr(10).join([f"- {eje['nombre']}: {eje['puntaje']}/5" for eje in ejes_evaluados])}
    
    EJES CRÍTICOS:
    {chr(10).join([f"- {eje['nombre']}: {eje['puntaje']}/5" for eje in ejes_criticos])}
    
    OBJETIVOS DEL CLIENTE:
    {objetivos_texto}
    
    INSTRUCCIONES CRÍTICAS:
    DEBES respetar ESTRICTAMENTE las limitaciones de {tamano_empresa}.
    NO sugieras duraciones, presupuestos o herramientas fuera del rango de {tamano_empresa}.
    
    Crea un plan de consultoría REALISTA para {tipo_empresa} tamaño {tamano_empresa}:
    
    **Fase I: Diagnóstico** - Duración y profundidad según {tamano_empresa}
    **Fase II: Estrategia** - Herramientas y presupuesto de {tamano_empresa}
    **Fase III: Implementación** - Capacidad de {tamano_empresa}
    **Fase IV: Sostenibilidad** - Recursos de {tamano_empresa}
    
    REQUISITOS OBLIGATORIOS:
    - Duración DENTRO del rango de {tamano_empresa}
    - Presupuesto DENTRO del rango de {tamano_empresa}
    - Herramientas APROPIADAS para {tamano_empresa}
    - Recursos humanos REALISTAS para {tamano_empresa}
    - Máximo 1000 palabras
    """
    
    # Intentar usar Gemini
    if model is not None:
        try:
            response = model.generate_content(prompt)
            if response.text and len(response.text.strip()) > 500:
                # Limpiar cualquier mención de duración incorrecta en la respuesta de Gemini
                texto_limpio = response.text
                # Remover menciones de duraciones largas para microempresas
                if "Microempresa" in tamano_empresa:
                    texto_limpio = texto_limpio.replace("6 meses", "4 semanas")
                    texto_limpio = texto_limpio.replace("12 meses", "2 meses")
                    texto_limpio = texto_limpio.replace("18 meses", "3 meses")
                    texto_limpio = texto_limpio.replace("año", "meses")
                return texto_limpio, prompt
        except Exception as e:
            logger.error(f"Error generando plan de consultoría con Gemini: {str(e)}")
    
    # Plan por defecto si Gemini no está disponible
    plan_default = f"""
    PLAN DE CONSULTORÍA PARA {nombre_empresa.upper()}
    
    **Fase I: Análisis y Diagnóstico**
    Para su {tipo_empresa}, iniciaremos con una evaluación integral enfocada en los ejes críticos identificados: {', '.join([eje['nombre'] for eje in ejes_criticos[:2]])}. 
    
    Actividades específicas:
    - Reunión inicial con líderes para alinear expectativas
    - Evaluación detallada de procesos actuales
    - Análisis de capacidad tecnológica existente
    - Identificación de brechas críticas
    
    **Fase II: Estrategia y Planificación**
    Desarrollaremos un plan de acción priorizado considerando sus objetivos de negocio y el presupuesto típico de una {tipo_empresa}.
    
    Actividades específicas:
    - Definición de objetivos SMART alineados con su visión
    - Priorización de iniciativas según impacto/esfuerzo
    - Selección de tecnologías SaaS apropiadas
    - Cronograma de implementación realista
    
    **Fase III: Implementación**
    Ejecutaremos las iniciativas priorizadas con enfoque en gestión del cambio, crítico para el éxito en PYMEs.
    
    Actividades específicas:
    - Implementación gradual de soluciones
    - Capacitación intensiva del personal
    - Aplicación de metodologías Lean para optimización
    - Implementación de herramientas de BI básico
    
    **Fase IV: Sostenibilidad y Mejora**
    Aseguraremos que los cambios sean sostenibles y generen valor continuo para su {tipo_empresa}.
    
    Actividades específicas:
    - Evaluación de resultados vs objetivos
    - Ajustes basados en feedback
    - Plan de seguimiento a largo plazo
    - Recomendaciones para escalamiento futuro
    """
    
    # Limpiar plan por defecto también
    if "Microempresa" in tamano_empresa:
        plan_default = plan_default.replace("3 - 6 meses", "1 - 2 meses")
        plan_default = plan_default.replace("6 - 12 meses", "2 - 3 meses")
    
    return plan_default, prompt

def generar_cronograma_consultoria(porcentaje_madurez, tamano_empresa):
    """Genera cronograma basado en madurez digital y tamaño de empresa"""
    
    if tamano_empresa == "Microempresa":
        if porcentaje_madurez <= 30:
            cronograma = [
                ("Semana 1", "Diagnóstico Rápido", "• Evaluación básica<br/>• Identificación de necesidades críticas"),
                ("Semana 2-3", "Implementación Básica", "• Herramientas gratuitas<br/>• Capacitación básica<br/>• Procesos esenciales"),
                ("Semana 4", "Seguimiento", "• Verificación de adopción<br/>• Ajustes menores<br/>• Plan de continuidad")
            ]
        elif porcentaje_madurez <= 60:
            cronograma = [
                ("Semana 1-2", "Análisis y Estrategia", "• Diagnóstico detallado<br/>• Plan de digitalización"),
                ("Semana 3-6", "Implementación", "• SaaS básicos<br/>• Automatización simple<br/>• Capacitación"),
                ("Semana 7-8", "Optimización", "• Ajustes<br/>• Medición de resultados<br/>• Sostenibilidad")
            ]
        else:
            cronograma = [
                ("Semana 1-2", "Estrategia Avanzada", "• Análisis profundo<br/>• Roadmap de innovación"),
                ("Semana 3-8", "Implementación Selectiva", "• Automatización inteligente<br/>• Integraciones<br/>• BI básico"),
                ("Semana 9-12", "Optimización y Escalamiento", "• Refinamiento<br/>• Expansión controlada<br/>• Monitoreo")
            ]
    elif tamano_empresa == "Pequeña":
        if porcentaje_madurez <= 30:
            cronograma = [
                ("Semana 1-3", "Diagnóstico Integral", "• Evaluación completa<br/>• Análisis de procesos<br/>• Identificación de brechas"),
                ("Semana 4-5", "Estrategia y Planificación", "• Plan estratégico<br/>• Selección de herramientas<br/>• Presupuesto"),
                ("Semana 6-8", "Implementación Fase 1", "• Sistemas básicos<br/>• Capacitación inicial<br/>• Procesos críticos"),
                ("Semana 9-10", "Consolidación", "• Ajustes<br/>• Evaluación<br/>• Plan de continuidad")
            ]
        elif porcentaje_madurez <= 60:
            cronograma = [
                ("Semana 1-4", "Análisis Estratégico", "• Diagnóstico profundo<br/>• Arquitectura de solución<br/>• Roadmap detallado"),
                ("Semana 5-8", "Diseño e Integración", "• Sistemas integrados<br/>• Flujos automatizados<br/>• Interfaces"),
                ("Semana 9-16", "Implementación Gradual", "• Despliegue por fases<br/>• Capacitación avanzada<br/>• Gestión del cambio"),
                ("Semana 17-20", "Optimización", "• Refinamiento<br/>• KPIs<br/>• Sostenibilidad")
            ]
        else:
            cronograma = [
                ("Semana 1-3", "Innovación y Estrategia", "• Visión digital<br/>• Tecnologías emergentes<br/>• Ventaja competitiva"),
                ("Semana 4-12", "Transformación Avanzada", "• IA y ML<br/>• Automatización inteligente<br/>• Analytics avanzado"),
                ("Semana 13-20", "Escalamiento", "• Expansión de capacidades<br/>• Integración ecosistema<br/>• Innovación continua"),
                ("Semana 21-24", "Excelencia Digital", "• Optimización continua<br/>• Liderazgo sectorial<br/>• Sostenibilidad")
            ]
    else:  # Mediana y Grande
        if porcentaje_madurez <= 30:
            cronograma = [
                ("Mes 1-2", "Diagnóstico Empresarial", "• Evaluación exhaustiva<br/>• Análisis organizacional<br/>• Arquitectura actual"),
                ("Mes 3", "Estrategia de Transformación", "• Visión digital<br/>• Roadmap estratégico<br/>• Governance"),
                ("Mes 4-8", "Implementación Estructurada", "• Sistemas empresariales<br/>• Integraciones complejas<br/>• Gestión del cambio"),
                ("Mes 9-12", "Consolidación y Mejora", "• Optimización<br/>• Escalamiento<br/>• Centro de excelencia")
            ]
        elif porcentaje_madurez <= 60:
            cronograma = [
                ("Mes 1-2", "Estrategia Digital Avanzada", "• Visión estratégica<br/>• Arquitectura empresarial<br/>• Innovation roadmap"),
                ("Mes 3-6", "Transformación Integral", "• Plataformas avanzadas<br/>• IA empresarial<br/>• Ecosistema digital"),
                ("Mes 7-10", "Escalamiento y Optimización", "• Expansión capacidades<br/>• Analytics avanzado<br/>• Automatización inteligente"),
                ("Mes 11-12", "Excelencia e Innovación", "• Liderazgo digital<br/>• Innovación continua<br/>• Ventaja competitiva")
            ]
        else:
            cronograma = [
                ("Mes 1-3", "Visión de Futuro Digital", "• Estrategia disruptiva<br/>• Tecnologías emergentes<br/>• Ecosistema de innovación"),
                ("Mes 4-8", "Implementación de Vanguardia", "• IA avanzada<br/>• Automatización autónoma<br/>• Plataformas inteligentes"),
                ("Mes 9-14", "Escalamiento Global", "• Expansión internacional<br/>• Ecosistemas complejos<br/>• Innovation labs"),
                ("Mes 15-18", "Liderazgo e Impacto", "• Transformación sectorial<br/>• Disrupción digital<br/>• Sostenibilidad avanzada")
            ]
    
    return cronograma

def generar_pdf_consultoria(usuario, evaluaciones, objetivos):
    from datetime import datetime
    
    email, nombre_empresa, tipo_empresa, tamano_empresa = usuario
    
    # Calcular promedio y determinar etapa basado en puntaje Y tamaño
    puntajes = [puntaje for _, _, puntaje in evaluaciones]
    promedio = sum(puntajes) / len(puntajes)
    porcentaje = (promedio / 5) * 100
    
    # Normalizar tamaño de empresa para comparación
    tamano_normalizado = tamano_empresa
    if "Microempresa" in tamano_empresa:
        tamano_normalizado = "Microempresa"
    elif "Pequeña" in tamano_empresa or "Peque" in tamano_empresa:
        tamano_normalizado = "Pequeña"
    elif "Mediana" in tamano_empresa:
        tamano_normalizado = "Mediana"
    else:
        tamano_normalizado = "Grande"
    
    # Determinar duración según puntaje y tamaño (prácticas de mercado)
    if tamano_normalizado == "Microempresa":
        if porcentaje <= 30:
            etapa = "Inicial - Microempresa"
            alcance = "Básico (Herramientas esenciales)"
            duracion = "2 - 4 semanas"
        elif porcentaje <= 60:
            etapa = "Desarrollo - Microempresa"
            alcance = "Intermedio (Digitalización básica)"
            duracion = "1 - 2 meses"
        else:
            etapa = "Optimización - Microempresa"
            alcance = "Avanzado (Automatización selectiva)"
            duracion = "2 - 3 meses"
    elif tamano_normalizado == "Pequeña":
        if porcentaje <= 30:
            etapa = "Inicial - Pequeña Empresa"
            alcance = "Estructurado (Bases sólidas)"
            duracion = "6 - 10 semanas"
        elif porcentaje <= 60:
            etapa = "Desarrollo - Pequeña Empresa"
            alcance = "Integral (Sistemas integrados)"
            duracion = "3 - 5 meses"
        else:
            etapa = "Optimización - Pequeña Empresa"
            alcance = "Avanzado (IA y automatización)"
            duracion = "4 - 6 meses"
    elif tamano_normalizado == "Mediana":
        if porcentaje <= 30:
            etapa = "Inicial - Mediana Empresa"
            alcance = "Completo (Transformación integral)"
            duracion = "3 - 4 meses"
        elif porcentaje <= 60:
            etapa = "Desarrollo - Mediana Empresa"
            alcance = "Estratégico (Ventaja competitiva)"
            duracion = "5 - 8 meses"
        else:
            etapa = "Optimización - Mediana Empresa"
            alcance = "Innovación (Liderazgo digital)"
            duracion = "6 - 10 meses"
    else:  # Grande
        if porcentaje <= 30:
            etapa = "Inicial - Gran Empresa"
            alcance = "Empresarial (Transformación completa)"
            duracion = "4 - 6 meses"
        elif porcentaje <= 60:
            etapa = "Desarrollo - Gran Empresa"
            alcance = "Estratégico (Ecosistema digital)"
            duracion = "8 - 12 meses"
        else:
            etapa = "Optimización - Gran Empresa"
            alcance = "Innovación (Disrupción digital)"
            duracion = "10 - 18 meses"
    
    # Identificar ejes críticos
    ejes_criticos = sorted(evaluaciones, key=lambda x: x[2])[:3]
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Encabezado
    story.append(Paragraph("<b>Transformacion Digital AA+</b>", 
                          ParagraphStyle('Header', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue, alignment=1)))
    story.append(Paragraph("Plan de Consultoría", 
                          ParagraphStyle('Subheader', parent=styles['Normal'], fontSize=14, textColor=colors.darkblue, alignment=1, spaceAfter=30)))
    
    # Título principal
    story.append(Paragraph("PLAN DE CONSULTORÍA", 
                          ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, textColor=colors.darkblue, alignment=1, spaceAfter=10)))
    story.append(Paragraph("Transformación Digital Empresarial", 
                          ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, alignment=1, spaceAfter=20)))
    
    # Info cliente
    story.append(Paragraph(f"<b>Cliente:</b> {nombre_empresa}", styles['Normal']))
    story.append(Paragraph(f"<b>Tipo de empresa:</b> {tipo_empresa}", styles['Normal']))
    story.append(Paragraph(f"<b>Tamaño:</b> {tamano_empresa}", styles['Normal']))
    story.append(Paragraph(f"<b>Madurez digital:</b> {porcentaje:.1f}% - {etapa}", styles['Normal']))
    story.append(Paragraph(f"<b>Alcance sugerido:</b> {alcance}", styles['Normal']))
    story.append(Paragraph(f"<b>Duración estimada:</b> {duracion}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Objetivos del cliente
    if objetivos and any(objetivos):
        story.append(Paragraph("Objetivos de Negocio del Cliente", 
                              ParagraphStyle('ObjTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=10)))
        
        if objetivos[0]: story.append(Paragraph(f"<b>1.</b> {objetivos[0]}", styles['Normal']))
        if objetivos[1]: story.append(Paragraph(f"<b>2.</b> {objetivos[1]}", styles['Normal']))
        if objetivos[2]: story.append(Paragraph(f"<b>3.</b> {objetivos[2]}", styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Ejes críticos
    story.append(Paragraph("Ejes Críticos Prioritarios", 
                          ParagraphStyle('CritTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=10)))
    
    for i, (eje_id, _, puntaje) in enumerate(ejes_criticos):
        prioridad = "Alta" if i == 0 else "Media" if i == 1 else "Baja"
        story.append(Paragraph(f"<b>{EJES_EVALUACION[eje_id]['nombre']}:</b> {puntaje}/5 - Prioridad {prioridad}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Generar plan detallado con Gemini (solo contenido, no duración)
    plan_detallado, prompt_usado = generar_plan_consultoria_gemini(nombre_empresa, tipo_empresa, tamano_empresa, evaluaciones, objetivos)
    
    # La duración ya está correctamente asignada arriba
    
    # Plan de consultoría detallado
    story.append(Paragraph("Plan de Consultoría Detallado", 
                          ParagraphStyle('PlanTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=15)))
    
    # Agregar el plan generado por Gemini
    for linea in plan_detallado.split('\n'):
        if linea.strip():
            if linea.startswith('**') and linea.endswith('**'):
                # Títulos de fase
                titulo = linea.replace('**', '')
                story.append(Paragraph(titulo, 
                                      ParagraphStyle('FaseTitle', parent=styles['Heading3'], fontSize=12, textColor=colors.darkblue, spaceAfter=5)))
            else:
                # Contenido normal
                story.append(Paragraph(linea.strip(), 
                                      ParagraphStyle('FaseDesc', parent=styles['Normal'], fontSize=10, spaceAfter=8, leftIndent=10)))
    
    story.append(Spacer(1, 20))
    
    # Cronograma estimado
    cronograma = generar_cronograma_consultoria(porcentaje, tamano_normalizado)
    
    story.append(Paragraph("Cronograma Estimado por Semanas", 
                          ParagraphStyle('CronoTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=15)))
    
    # Crear tabla de cronograma con Paragraphs para wrap de texto
    crono_data = [[
        Paragraph('<b>Período</b>', ParagraphStyle('CronoHeader', parent=styles['Normal'], fontSize=10, textColor=colors.whitesmoke)),
        Paragraph('<b>Fase</b>', ParagraphStyle('CronoHeader', parent=styles['Normal'], fontSize=10, textColor=colors.whitesmoke)),
        Paragraph('<b>Actividades Principales</b>', ParagraphStyle('CronoHeader', parent=styles['Normal'], fontSize=10, textColor=colors.whitesmoke))
    ]]
    
    for periodo, fase, actividades in cronograma:
        crono_data.append([
            Paragraph(periodo, ParagraphStyle('CronoPeriodo', parent=styles['Normal'], fontSize=9)),
            Paragraph(fase, ParagraphStyle('CronoFase', parent=styles['Normal'], fontSize=9)),
            Paragraph(actividades, ParagraphStyle('CronoActividades', parent=styles['Normal'], fontSize=9))
        ])
    
    crono_table = Table(crono_data, colWidths=[1.2*inch, 2*inch, 2.8*inch])
    crono_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(crono_table)
    story.append(Spacer(1, 20))
    
    # Agregar información del prompt usado
    story.append(Paragraph("Información Técnica del Análisis", 
                          ParagraphStyle('TechTitle', parent=styles['Heading3'], fontSize=12, textColor=colors.darkblue, spaceAfter=10)))
    story.append(Paragraph("Prompt utilizado para la generación del plan con Gemini AI:", 
                          ParagraphStyle('PromptLabel', parent=styles['Normal'], fontSize=9, textColor=colors.grey, spaceAfter=5)))
    
    # Agregar el prompt en texto pequeño
    prompt_style = ParagraphStyle('PromptStyle', parent=styles['Normal'], fontSize=8, textColor=colors.grey, 
                                 leftIndent=10, rightIndent=10, spaceAfter=5)
    for linea in prompt_usado.split('\n'):
        if linea.strip():
            story.append(Paragraph(linea.strip(), prompt_style))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'plan_consultoria_{nombre_empresa.replace(" ", "_")}.pdf'
    )

@app.route('/eje/<int:eje_id>')
def mostrar_eje(eje_id):
    if 'usuario_id' not in session or eje_id not in EJES_EVALUACION:
        return redirect('/')
    
    # Obtener respuestas anteriores si existen
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT respuestas FROM evaluaciones WHERE usuario_id = ? AND eje_id = ?', 
              (session['usuario_id'], eje_id))
    resultado = c.fetchone()
    conn.close()
    
    respuestas_anteriores = {}
    if resultado:
        respuestas_json = json.loads(resultado[0])
        for i, respuesta in enumerate(respuestas_json):
            respuestas_anteriores[f'pregunta_{i}'] = respuesta['valor']
    
    return render_template('eje.html', 
                         eje=EJES_EVALUACION[eje_id],
                         eje_id=eje_id,
                         preguntas=PREGUNTAS_EJES[eje_id],
                         respuestas_anteriores=respuestas_anteriores)

@app.route('/evaluar_eje', methods=['POST'])
def evaluar_eje():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    data = request.json
    eje_id = data.get('eje_id')
    respuestas = data.get('respuestas')
    
    puntaje = calcular_puntaje(respuestas)
    
    # Generar recomendaciones incluyendo el puntaje
    recomendaciones = generar_recomendaciones(eje_id, respuestas, session['tipo_empresa'], puntaje, session.get('tamano_empresa', 'No especificado'))
    
    # Guardar en base de datos
    conn = get_db_connection()
    c = conn.cursor()
    
    # Eliminar evaluación anterior si existe
    c.execute('DELETE FROM evaluaciones WHERE usuario_id = ? AND eje_id = ?', 
              (session['usuario_id'], eje_id))
    
    # Insertar nueva evaluación
    c.execute('''INSERT INTO evaluaciones (usuario_id, eje_id, respuestas, puntaje) 
                 VALUES (?, ?, ?, ?)''',
              (session['usuario_id'], eje_id, json.dumps(respuestas), puntaje))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'puntaje': puntaje,
        'recomendaciones': recomendaciones,
        'eje_nombre': EJES_EVALUACION[eje_id]['nombre'],
        'nombre_empresa': session.get('nombre_empresa', 'su empresa')
    })

@app.route('/generar_informe_ejecutivo')
def generar_informe_ejecutivo():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    # Obtener todas las evaluaciones del usuario
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT eje_id, respuestas, puntaje FROM evaluaciones 
                 WHERE usuario_id = ? ORDER BY eje_id''', 
              (session['usuario_id'],))
    evaluaciones = c.fetchall()
    conn.close()
    
    if not evaluaciones:
        return jsonify({'success': False, 'error': 'No hay evaluaciones completadas'})
    
    # Generar resumen ejecutivo con IA
    resumen_ejecutivo = generar_resumen_ejecutivo(evaluaciones, session['tipo_empresa'], session.get('tamano_empresa'))
    
    # Generar IA-Readiness Canvas
    ia_canvas = generar_ia_readiness_canvas(session['tipo_empresa'], session.get('tamano_empresa'), evaluaciones)
    
    # Generar PDF sin numeración compleja
    from datetime import datetime
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # === PORTADA ===
    # Encabezado simple
    story.append(Paragraph("<b>Transformacion Digital AA+</b>", 
                          ParagraphStyle('Header', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue, alignment=1)))
    story.append(Paragraph("Ruta de Estrategia Digital", 
                          ParagraphStyle('Subheader', parent=styles['Normal'], fontSize=14, textColor=colors.darkblue, alignment=1, spaceAfter=30)))
    
    # Título principal
    story.append(Paragraph("PLAN DE IMPLEMENTACIÓN", 
                          ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.darkblue, alignment=1, spaceAfter=20)))
    
    # Información del emprendimiento
    story.append(Paragraph(f"<b>Emprendimiento:</b> {session['nombre_empresa']}", styles['Normal']))
    story.append(Paragraph(f"<b>Tipo/Industria:</b> {session['tipo_empresa']}", styles['Normal']))
    story.append(Paragraph(f"<b>Etapa:</b> {session.get('tamano_empresa', 'No especificado')}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Puntuaciones por eje
    story.append(Paragraph("Puntuaciones por Eje de Evaluación", 
                          ParagraphStyle('ScoreTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=10)))
    
    for eje_id, _, puntaje in evaluaciones:
        story.append(Paragraph(f"<b>{EJES_EVALUACION[eje_id]['nombre']}:</b> {puntaje}/5", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Resumen ejecutivo
    story.append(Paragraph("Análisis y Recomendaciones Estratégicas", 
                          ParagraphStyle('AnalysisTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=15)))
    
    for linea in resumen_ejecutivo.split('\n'):
        if linea.strip():
            story.append(Paragraph(linea.strip(), styles['Normal']))
            story.append(Spacer(1, 6))
    
    # Salto de página antes del IA-Readiness Canvas
    from reportlab.platypus import PageBreak
    story.append(PageBreak())
    
    # === IA-READINESS CANVAS ===
    story.append(Paragraph("<b>Transformacion Digital AA+</b>", 
                          ParagraphStyle('Header', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue, alignment=1)))
    story.append(Paragraph("Ruta de Estrategia Digital", 
                          ParagraphStyle('Subheader', parent=styles['Normal'], fontSize=14, textColor=colors.darkblue, alignment=1, spaceAfter=30)))
    
    story.append(Paragraph("IA-READINESS CANVAS", 
                          ParagraphStyle('CanvasTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.darkblue, alignment=1, spaceAfter=10)))
    
    story.append(Paragraph("Para Emprendimientos que Quieren Integrar IA desde el Inicio", 
                          ParagraphStyle('CanvasSubtitle', parent=styles['Normal'], fontSize=12, textColor=colors.grey, alignment=1, spaceAfter=20)))
    
    # Línea divisoria
    story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=20))
    
    # Información de la empresa
    story.append(Paragraph(f"<b>Emprendimiento:</b> {session['nombre_empresa']}", styles['Normal']))
    story.append(Paragraph(f"<b>Tipo/Industria:</b> {session['tipo_empresa']}", styles['Normal']))
    story.append(Paragraph(f"<b>Etapa:</b> {session.get('tamano_empresa', 'No especificado')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Canvas content con formato especial
    canvas_style = ParagraphStyle('CanvasStyle', parent=styles['Normal'], fontSize=11, spaceAfter=10, 
                                 leftIndent=10, rightIndent=10, alignment=0)
    
    header_style = ParagraphStyle('CanvasHeaderStyle', parent=styles['Heading3'], fontSize=13, 
                                 textColor=colors.darkblue, spaceAfter=8, spaceBefore=12)
    
    for linea in ia_canvas.split('\n'):
        if linea.strip():
            # Detectar headers (líneas que empiezan con ===)
            if linea.strip().startswith('===') and linea.strip().endswith('==='):
                # Remover los === y agregar como header
                header_text = linea.strip().replace('===', '').strip()
                story.append(HRFlowable(width="80%", thickness=1, color=colors.lightgrey, spaceAfter=5))
                story.append(Paragraph(f"<b>{header_text}</b>", header_style))
            else:
                story.append(Paragraph(linea.strip(), canvas_style))
    
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=10))
    
    # Salto de página después del canvas
    story.append(PageBreak())
    
    # Reportes individuales de cada eje en páginas separadas
    for i, (eje_id, respuestas_json, puntaje) in enumerate(evaluaciones):
        respuestas = json.loads(respuestas_json)
        recomendaciones = generar_recomendaciones(eje_id, respuestas, session['tipo_empresa'], puntaje, session.get('tamano_empresa', 'No especificado'))
        
        # Salto de página antes de cada eje
        if i > 0:
            story.append(PageBreak())
        
        # Encabezado del eje
        story.append(Paragraph("<b>Transformacion Digital AA+</b>", 
                              ParagraphStyle('Header', parent=styles['Heading1'], fontSize=16, textColor=colors.darkblue, alignment=1)))
        story.append(Paragraph("Diagnóstico de Madurez Digital", 
                              ParagraphStyle('Subheader', parent=styles['Normal'], fontSize=12, textColor=colors.darkblue, alignment=1, spaceAfter=20)))
        
        # Título del eje
        story.append(Paragraph(EJES_EVALUACION[eje_id]['nombre'], 
                              ParagraphStyle('EjeTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.darkblue, alignment=1, spaceAfter=10)))
        
        # Línea divisoria
        story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=20))
        
        # Información de la empresa y puntaje
        story.append(Paragraph(f"<b>Empresa:</b> {session['nombre_empresa']}", styles['Normal']))
        story.append(Paragraph(f"<b>Tipo de empresa:</b> {session['tipo_empresa']}", styles['Normal']))
        story.append(Paragraph(f"<b>Tamaño:</b> {session.get('tamano_empresa', 'No especificado')}", styles['Normal']))
        story.append(Paragraph(f"<b>Puntaje obtenido:</b> <font size=16 color=blue><b>{puntaje}/5</b></font>", 
                              ParagraphStyle('PuntajeStyle', parent=styles['Normal'], fontSize=14, alignment=1, spaceAfter=20)))
        
        story.append(Spacer(1, 20))
        
        # Recomendaciones estratégicas
        story.append(Paragraph("Recomendaciones Estratégicas", 
                              ParagraphStyle('RecomTitle', parent=styles['Heading2'], fontSize=16, textColor=colors.darkblue, spaceAfter=15)))
        
        # Línea divisoria antes de recomendaciones
        story.append(HRFlowable(width="100%", thickness=1, color=colors.lightblue, spaceAfter=15))
        
        # Formatear recomendaciones
        recom_style = ParagraphStyle('RecomStyle', parent=styles['Normal'], fontSize=11, spaceAfter=12, 
                                    leftIndent=15, rightIndent=15, alignment=0)
        
        for linea in recomendaciones.split('\n'):
            if linea.strip():
                story.append(Paragraph(linea.strip(), recom_style))
        
        # Línea divisoria final
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=10))
        
        # Pie de página del eje
        story.append(Paragraph(f"Eje {i+1} de {len(evaluaciones)} | {EJES_EVALUACION[eje_id]['nombre']}", 
                              ParagraphStyle('EjeFooter', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1)))
    
    # Pie de página
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Informe generado el {datetime.now().strftime('%d/%m/%Y')} | Transformacion Digital AA+", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1)))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'informe_ejecutivo_{session["nombre_empresa"]}.pdf'
    )

def generar_ia_readiness_canvas(tipo_empresa, tamano_empresa, evaluaciones):
    """
    Genera el IA-Readiness Canvas para emprendimientos que quieren integrar IA desde el inicio.
    
    Dimensiones:
    1. Problemas que pueden resolverse con IA
    2. Disponibilidad o generación futura de datos
    3. Riesgos éticos o regulatorios
    4. Capacidades del equipo
    5. Indicadores clave
    """
    
    # Preparar contexto de evaluaciones
    contexto_evaluaciones = []
    for eje_id, _, puntaje in evaluaciones:
        contexto_evaluaciones.append(f"{EJES_EVALUACION[eje_id]['nombre']}: {puntaje}/4")
    
    prompt = f"""
    Eres un experto en inteligencia artificial aplicada a emprendimientos y estrategia digital.
    
    EMPRENDIMIENTO ANALIZADO:
    Tipo/Industria: {tipo_empresa}
    Etapa: {tamano_empresa}
    
    EVALUACIONES COMPLETADAS:
    {chr(10).join(contexto_evaluaciones)}
    
    INSTRUCCIONES:
    Genera un IA-Readiness Canvas específico para este emprendimiento {tipo_empresa} en etapa {tamano_empresa}.
    
    El canvas debe contener las siguientes 5 dimensiones con recomendaciones concretas y accionables:
    
    1. PROBLEMAS QUE PUEDEN RESOLVERSE CON IA:
       - Identifica 3-4 problemas específicos de este tipo de emprendimiento que la IA puede resolver
       - Prioriza por impacto y viabilidad para un emprendimiento en esta etapa
       - Sé específico con ejemplos aplicables (ej: "Automatizar clasificación de leads entrantes")
    
    2. DISPONIBILIDAD O GENERACIÓN FUTURA DE DATOS:
       - Qué datos necesita recolectar desde el MVP
       - Qué fuentes de datos son críticas
       - Cómo estructurar la captura de datos para futuros modelos de IA
       - Volúmenes mínimos necesarios para entrenar modelos básicos
    
    3. RIESGOS ÉTICOS O REGULATORIOS:
       - Riesgos éticos específicos del sector
       - Regulaciones de privacidad aplicables (GDPR, CCPA, leyes locales)
       - Sesgos algorítmicos a considerar
       - Mejores prácticas de IA responsable para esta industria
    
    4. CAPACIDADES DEL EQUIPO:
       - Habilidades técnicas necesarias en el equipo fundador
       - Gaps críticos que deben cerrarse (contratar vs capacitar vs outsourcing)
       - Herramientas no-code/low-code de IA recomendadas para comenzar
       - Roadmap de desarrollo de capacidades a 12 meses
    
    5. INDICADORES CLAVE (KPIs):
       - 4-5 métricas específicas para medir preparación de IA
       - KPIs de adopción y uso de IA
       - Métricas de calidad de datos
       - Indicadores de ROI de inversiones en IA
    
    FORMATO REQUERIDO:
    Usa este formato exacto con headers claros:
    
    === 1. PROBLEMAS QUE PUEDEN RESOLVERSE CON IA ===
    [Contenido...]
    
    === 2. DISPONIBILIDAD O GENERACIÓN FUTURA DE DATOS ===
    [Contenido...]
    
    === 3. RIESGOS ÉTICOS O REGULATORIOS ===
    [Contenido...]
    
    === 4. CAPACIDADES DEL EQUIPO ===
    [Contenido...]
    
    === 5. INDICADORES CLAVE (KPIs) ===
    [Contenido...]
    
    Cada sección debe tener 80-120 palabras. Total máximo: 500 palabras.
    """
    
    # Intentar usar Gemini
    if model is not None:
        try:
            response = model.generate_content(prompt)
            if response.text and len(response.text.strip()) > 200:
                logger.info("="*50)
                logger.info("✅ USANDO GEMINI AI PARA IA-READINESS CANVAS")
                logger.info(f"Empresa: {tipo_empresa}, Etapa: {tamano_empresa}")
                logger.info("="*50)
                return f"*G\n\n{response.text}"
        except Exception as e:
            logger.error(f"Error generando IA-Readiness Canvas con Gemini: {str(e)}")
    
    # Canvas por defecto si Gemini falla
    logger.info("="*50)
    logger.info("📋 USANDO IA-READINESS CANVAS PREDEFINIDO")
    logger.info(f"Empresa: {tipo_empresa}, Etapa: {tamano_empresa}")
    logger.info("="*50)
    return f"""*P

=== 1. PROBLEMAS QUE PUEDEN RESOLVERSE CON IA ===
Para su {tipo_empresa}, la IA puede resolver:
- Automatización de atención al cliente con chatbots inteligentes
- Análisis predictivo de comportamiento de usuarios/clientes
- Personalización de experiencias y recomendaciones
- Automatización de procesos repetitivos de clasificación y categorización

=== 2. DISPONIBILIDAD O GENERACIÓN FUTURA DE DATOS ===
Datos críticos a recolectar desde el MVP:
- Interacciones de usuarios (clicks, tiempo, flujos)
- Datos transaccionales y de conversión
- Feedback explícito e implícito de clientes
- Datos de rendimiento de producto/servicio
Estructure la captura con timestamps, IDs únicos y metadata contextual. Necesitará al menos 1000-5000 registros para modelos básicos.

=== 3. RIESGOS ÉTICOS O REGULATORIOS ===
Consideraciones para {tipo_empresa}:
- Cumplimiento con leyes de protección de datos (GDPR si opera en EU, CCPA en California)
- Transparencia en uso de IA con clientes
- Prevención de sesgos en algoritmos de recomendación/clasificación
- Consentimiento informado para uso de datos personales
- Políticas claras de privacidad y uso de IA

=== 4. CAPACIDADES DEL EQUIPO ===
Habilidades necesarias:
- Al menos un miembro con conocimientos básicos de IA/ML
- Capacidad de trabajar con APIs de IA (OpenAI, Google Cloud AI, AWS)
- Análisis de datos básico (Python/Excel avanzado)
Herramientas recomendadas: Zapier AI, Make.com, Bubble, ChatGPT API, Hugging Face
Roadmap: Capacitación en IA básica (3 meses), implementación de primera solución (6 meses), optimización (12 meses)

=== 5. INDICADORES CLAVE (KPIs) ===
Métricas para medir preparación de IA:
- Volumen de datos históricos recolectados (objetivo: 5000+ registros en 6 meses)
- Número de procesos candidatos para automatización con IA identificados (objetivo: 5+ procesos)
- % del equipo capacitado en herramientas básicas de IA (objetivo: 60%+ del equipo técnico)
- Tiempo de implementación de primera solución IA (objetivo: <3 meses desde decisión)
- ROI de inversiones en IA (objetivo: positivo en 12 meses)"""

def generar_resumen_ejecutivo(evaluaciones, tipo_empresa, tamano_empresa=None):
    # Preparar datos para el prompt
    ejes_evaluados = []
    puntajes = []
    
    for eje_id, _, puntaje in evaluaciones:
        ejes_evaluados.append({
            'nombre': EJES_EVALUACION[eje_id]['nombre'],
            'puntaje': puntaje,
            'eje_id': eje_id
        })
        puntajes.append(puntaje)
    
    promedio_general = round(sum(puntajes) / len(puntajes), 1)
    
    # Ordenar ejes por prioridad (menor puntaje = mayor prioridad de establecimiento)
    ejes_por_prioridad = sorted(ejes_evaluados, key=lambda x: x['puntaje'])
    
    prompt = f"""
    Eres un consultor senior especializado en estrategia digital para emprendimientos en gestación en Latinoamérica.
    
    EMPRENDIMIENTO ANALIZADO:
    Tipo/Industria: {tipo_empresa}
    Etapa: {tamano_empresa if tamano_empresa else 'No especificado'}
    Promedio de preparación digital: {promedio_general}/4
    
    CONTEXTO DE ETAPAS:
    - Ideación: Solo idea, necesita establecer todo desde cero
    - MVP en desarrollo: Construyendo prototipo, estructurar vectores digitales
    - MVP lanzado: Primeros usuarios, consolidar y optimizar
    - Tracción temprana: Validación inicial, listo para escalar
    
    VECTORES EVALUADOS Y PUNTUACIONES:
    {chr(10).join([f"- {eje['nombre']}: {eje['puntaje']}/4" for eje in ejes_evaluados])}
    
    VECTORES ORDENADOS POR PRIORIDAD DE IMPLEMENTACIÓN (menor puntaje = mayor prioridad):
    {chr(10).join([f"{i+1}. {eje['nombre']}: {eje['puntaje']}/4" for i, eje in enumerate(ejes_por_prioridad)])}
    
    INSTRUCCIONES:
    Genera un PLAN DE IMPLEMENTACIÓN ORDENADO POR PRIORIDADES (máximo 450 palabras) para este {tipo_empresa} en etapa {tamano_empresa if tamano_empresa else 'No especificado'}:
    
    1. ESTADO ACTUAL DE PREPARACIÓN:
       - Nivel de preparación digital general
       - Vectores que ya tienen bases vs vectores que necesitan establecerse desde cero
    
    2. PLAN DE IMPLEMENTACIÓN POR FASES:
       FASE 1 (Primeros 3 meses) - Fundamentos críticos:
       - Los 2-3 vectores más urgentes a establecer (menor puntaje)
       - Acciones específicas para cada uno
       - Recursos necesarios (tiempo, presupuesto estimado, equipo)
       
       FASE 2 (Meses 4-6) - Consolidación:
       - Vectores de prioridad media a establecer
       - Cómo se integran con Fase 1
       - Recursos necesarios
       
       FASE 3 (Meses 7-12) - Optimización y Escalamiento:
       - Vectores con mejor puntaje a optimizar
       - Preparación para escalar
       - Recursos necesarios
    
    3. ORDEN ADECUADO Y DEPENDENCIAS:
       - Por qué este orden específico
       - Qué vectores deben establecerse antes que otros
       - Sinergias entre vectores
    
    4. CONSIDERACIONES PARA {tamano_empresa if tamano_empresa else 'ESTE'} EMPRENDIMIENTO:
       - Restricciones presupuestarias típicas
       - Capacidad de implementación del equipo
       - Quick wins vs inversiones a largo plazo
       - Herramientas gratuitas/accesibles recomendadas
    
    El plan debe ser:
    - Específico y accionable para {tipo_empresa}
    - Realista para un emprendimiento en etapa {tamano_empresa if tamano_empresa else 'temprana'}
    - Ordenado por prioridades basadas en los puntajes
    - Incluir rangos de inversión apropiados para startups
    - Enfocarse en ESTABLECER vectores (no mejorar lo existente)
    """
    
    # Intentar usar Gemini
    if model is not None:
        try:
            response = model.generate_content(prompt)
            if response.text and len(response.text.strip()) > 100:
                logger.info("="*50)
                logger.info("✅ USANDO GEMINI AI PARA PLAN DE IMPLEMENTACIÓN")
                logger.info(f"Empresa: {tipo_empresa}, Promedio: {promedio_general:.1f}/4")
                logger.info("="*50)
                return f"*G\n\n{response.text}"
        except Exception as e:
            logger.error(f"Error generando plan de implementación con Gemini: {str(e)}")
    
    # Plan por defecto
    logger.info("="*50)
    logger.info("📋 USANDO PLAN DE IMPLEMENTACIÓN PREDEFINIDO")
    logger.info(f"Empresa: {tipo_empresa}, Promedio: {promedio_general:.1f}/4")
    logger.info("="*50)
    nivel_preparacion = "inicial" if promedio_general <= 1.5 else "intermedio" if promedio_general <= 2.5 else "avanzado"
    
    return f"""*P

ESTADO ACTUAL DE PREPARACIÓN:
Su {tipo_empresa} presenta un nivel de preparación digital {nivel_preparacion} con un promedio de {promedio_general}/4. Los vectores con menor puntaje representan las mayores oportunidades para establecer bases digitales sólidas desde el inicio.

PLAN DE IMPLEMENTACIÓN POR FASES:

FASE 1 (Primeros 3 meses) - Fundamentos Críticos:
Prioridad 1: {ejes_por_prioridad[0]['nombre']} ({ejes_por_prioridad[0]['puntaje']}/4)
- Establecer este vector es fundamental pues impacta directamente en la viabilidad del MVP
- Inversión estimada: $500-2000 en herramientas básicas
- Tiempo del equipo: 20-30 horas/semana durante el primer mes

Prioridad 2: {ejes_por_prioridad[1]['nombre']} ({ejes_por_prioridad[1]['puntaje']}/4)
- Complementa el primer vector y permite avanzar en construcción del MVP
- Inversión estimada: $300-1500
- Tiempo del equipo: 15-20 horas/semana

FASE 2 (Meses 4-6) - Consolidación:
Enfocarse en los vectores de prioridad media ({ejes_por_prioridad[2]['nombre']}, {ejes_por_prioridad[3]['nombre'] if len(ejes_por_prioridad) > 3 else 'otros vectores'})
- Estos vectores permiten estructurar mejor el emprendimiento
- Inversión estimada: $1000-3000 en esta fase
- Integrar con infraestructura de Fase 1

FASE 3 (Meses 7-12) - Optimización:
Optimizar vectores con mejor puntaje ({ejes_evaluados[-1]['nombre']}, {ejes_evaluados[-2]['nombre']})
- Preparar para escalamiento
- Automatizar procesos establecidos en fases anteriores
- Inversión estimada: $2000-5000 para escalar

ORDEN ADECUADO Y DEPENDENCIAS:
Este orden prioriza: 1) Viabilidad del MVP, 2) Fundamentos operacionales, 3) Escalabilidad. Los vectores de menor puntaje requieren atención inmediata pues son prerequisitos para los siguientes.

CONSIDERACIONES CLAVE:
- Use herramientas gratuitas o freemium en Fase 1 (Google Workspace, Trello, Canva)
- Invierta más en Fases 2-3 cuando tenga validación inicial
- Priorice quick wins que generen valor inmediato
- Revise este plan cada 2 meses según progreso y validación de mercado"""

@app.route('/generar_pdf/<int:eje_id>')
def generar_pdf_eje(eje_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    # Obtener datos de la evaluación
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT respuestas, puntaje FROM evaluaciones 
                 WHERE usuario_id = ? AND eje_id = ?''', 
              (session['usuario_id'], eje_id))
    resultado = c.fetchone()
    conn.close()
    
    if not resultado:
        return jsonify({'success': False, 'error': 'Evaluación no encontrada'})
    
    respuestas = json.loads(resultado[0])
    puntaje = resultado[1]
    recomendaciones = generar_recomendaciones(eje_id, respuestas, session['tipo_empresa'], puntaje, session.get('tamano_empresa', 'No especificado'))
    
    # Generar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # === ENCABEZADO CON LOGO ===
    # Crear tabla para encabezado con logo y título
    header_data = []
    
    # Intentar cargar logo
    logo_path = 'static/images/logo.png'
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.5*inch, height=0.75*inch)
            header_data.append([logo, 
                              Paragraph("<b>Transformacion Digital AA+</b><br/>Diagnóstico de Madurez Digital", 
                                      ParagraphStyle('HeaderText', parent=styles['Normal'], fontSize=14, textColor=colors.darkblue, alignment=2))])
        except:
            header_data.append(["", 
                              Paragraph("<b>Transformacion Digital AA+</b><br/>Diagnóstico de Madurez Digital", 
                                      ParagraphStyle('HeaderText', parent=styles['Normal'], fontSize=14, textColor=colors.darkblue, alignment=2))])
    else:
        header_data.append(["", 
                          Paragraph("<b>Transformacion Digital AA+</b><br/>Diagnóstico de Madurez Digital", 
                                  ParagraphStyle('HeaderText', parent=styles['Normal'], fontSize=14, textColor=colors.darkblue, alignment=2))])
    
    header_table = Table(header_data, colWidths=[2*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # === TÍTULO DEL EJE CON ICONO ===
    eje_icono = EJES_EVALUACION[eje_id]['icono']
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=10,
        textColor=colors.darkblue,
        alignment=1  # Centrado
    )
    
    # Crear título sin emoji para evitar problemas de renderizado en PDF
    story.append(Paragraph(EJES_EVALUACION[eje_id]['nombre'], title_style))
    
    # Línea divisoria después del título
    story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=20))
    
    # === CAJA ENMARCADA CON INFORMACIÓN DE LA EMPRESA ===
    tamano_valor = session.get('tamano_empresa', 'No especificado')
    logger.info(f"Valor de tamaño en PDF: {tamano_valor}")
    
    empresa_data = [
        [Paragraph(f"<b>Empresa:</b> {session['nombre_empresa']}", styles['Normal'])],
        [Paragraph(f"<b>Tipo de empresa:</b> {session['tipo_empresa']}", styles['Normal'])],
        [Paragraph(f"<b>Tamaño:</b> {tamano_valor}", styles['Normal'])],
        [Paragraph(f"<b>Puntaje obtenido:</b> <font size=18 color=blue><b>{puntaje}/5</b></font>", 
                  ParagraphStyle('PuntajeBox', parent=styles['Normal'], fontSize=14, alignment=1))]
    ]
    
    empresa_table = Table(empresa_data, colWidths=[6*inch], rowHeights=[0.4*inch, 0.4*inch, 0.4*inch, 0.6*inch])
    empresa_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.darkblue),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.lightblue),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightcyan),
        ('PADDING', (0, 0), (-1, -1), 18),  # Aumentado de 12 a 18
        ('TOPPADDING', (0, 2), (-1, 2), 20),  # Padding extra para la fila del puntaje
        ('BOTTOMPADDING', (0, 2), (-1, 2), 20),  # Padding extra para la fila del puntaje
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 2), (-1, 2), 'CENTER'),  # Centrar solo el puntaje
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(empresa_table)
    story.append(Spacer(1, 30))
    
    # === RECOMENDACIONES ===
    recom_title_style = ParagraphStyle(
        'RecomTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=15
    )
    
    story.append(Paragraph("📋 Recomendaciones Estratégicas", recom_title_style))
    
    # Línea divisoria antes de recomendaciones
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightblue, spaceAfter=15))
    
    # Separar y formatear recomendaciones
    recomendaciones_lineas = recomendaciones.split('\n')
    recom_style = ParagraphStyle(
        'RecomStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leftIndent=20,
        rightIndent=20,
        alignment=0  # Justificado
    )
    
    for linea in recomendaciones_lineas:
        if linea.strip():
            story.append(Paragraph(linea.strip(), recom_style))
    
    # Línea divisoria final
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=10))
    
    # Pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1  # Centrado
    )
    
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    story.append(Paragraph(f"Diagnóstico generado el {fecha_actual} | Transformacion Digital AA+ | PYMEs Centroamérica", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        io.BytesIO(buffer.read()),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'diagnostico_eje_{eje_id}_{session["nombre_empresa"]}.pdf'
    )

if __name__ == '__main__':
    # Inicializar base de datos
    init_db()
    
    # Crear directorios necesarios
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('pdfs', exist_ok=True)
    
    # Actualizar archivo de versión
    with open('VERSION', 'w') as f:
        f.write('1.5')
    
    # Mostrar información de inicio
    print("\n" + "="*60)
    print("🚀 DIAGNÓSTICO DE MADUREZ DIGITAL - INICIANDO")
    print("="*60)
    print(f"📊 Aplicación: Diagnóstico de Madurez Digital")
    print(f"📋 Versión: 1.5")
    print(f"🌐 URL: http://localhost:5000")
    print(f"🤖 Gemini AI: {'✅ Configurado' if model else '⚠️ No configurado'}")
    print(f"🗄️ Base de datos: diagnostico.db")
    print("="*60)
    print("💡 Presiona Ctrl+C para detener")
    print("="*60 + "\n")
    
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(debug=False, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n\n👋 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar la aplicación: {e}")