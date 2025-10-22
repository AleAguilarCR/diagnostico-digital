#!/usr/bin/env python3
"""
Script de configuración inicial para la aplicación de Diagnóstico de Madurez Digital
"""

import os
import sys
import sqlite3
import subprocess

def check_python_version():
    """Verificar que la versión de Python sea compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - Compatible")
    return True

def install_dependencies():
    """Instalar dependencias del proyecto"""
    print("\n📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error al instalar dependencias")
        return False

def create_directories():
    """Crear directorios necesarios"""
    print("\n📁 Creando directorios...")
    directories = [
        'uploads',
        'pdfs',
        'static/images',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directorio creado: {directory}")

def initialize_database():
    """Inicializar la base de datos"""
    print("\n🗄️ Inicializando base de datos...")
    try:
        conn = sqlite3.connect('diagnostico.db')
        c = conn.cursor()
        
        # Crear tabla de usuarios
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      email TEXT UNIQUE,
                      nombre_empresa TEXT,
                      tipo_empresa TEXT,
                      fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Crear tabla de evaluaciones
        c.execute('''CREATE TABLE IF NOT EXISTS evaluaciones
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      usuario_id INTEGER,
                      eje_id INTEGER,
                      respuestas TEXT,
                      puntaje INTEGER,
                      pdf_path TEXT,
                      fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (usuario_id) REFERENCES usuarios (id))''')
        
        # Crear tabla de configuración
        c.execute('''CREATE TABLE IF NOT EXISTS configuracion
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      clave TEXT UNIQUE,
                      valor TEXT,
                      descripcion TEXT,
                      fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Insertar configuración inicial
        configuraciones = [
            ('app_name', 'Diagnóstico de Madurez Digital', 'Nombre de la aplicación'),
            ('app_version', '1.0.0', 'Versión de la aplicación'),
            ('logo_path', 'static/images/logo.png', 'Ruta del logo'),
            ('empresa_consultora', 'Tu Empresa Consultora', 'Nombre de la empresa consultora'),
            ('email_contacto', 'contacto@tuempresa.com', 'Email de contacto'),
            ('gemini_configured', 'false', 'Estado de configuración de Gemini AI')
        ]
        
        for config in configuraciones:
            c.execute('INSERT OR IGNORE INTO configuracion (clave, valor, descripcion) VALUES (?, ?, ?)', config)
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        return False

def check_gemini_config():
    """Verificar configuración de Gemini AI"""
    print("\n🤖 Verificando configuración de Gemini AI...")
    
    # Leer el archivo app.py para verificar la API key
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'TU_API_KEY_DE_GEMINI' in content:
                print("⚠️  IMPORTANTE: Debes configurar tu API Key de Gemini")
                print("   1. Ve a https://makersuite.google.com/app/apikey")
                print("   2. Crea una nueva API Key")
                print("   3. Reemplaza 'TU_API_KEY_DE_GEMINI' en app.py línea 15")
                print("   4. O configura la variable de entorno GEMINI_API_KEY")
                return False
            else:
                print("✅ Configuración de Gemini AI detectada")
                return True
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo app.py")
        return False

def create_sample_logo():
    """Crear un logo de ejemplo"""
    print("\n🎨 Creando logo de ejemplo...")
    logo_content = '''
    <svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="100" fill="#0d6efd"/>
        <text x="100" y="35" font-family="Arial" font-size="16" fill="white" text-anchor="middle">
            Tu Logo Aquí
        </text>
        <text x="100" y="55" font-family="Arial" font-size="12" fill="white" text-anchor="middle">
            Diagnóstico Digital
        </text>
        <text x="100" y="75" font-family="Arial" font-size="10" fill="white" text-anchor="middle">
            PYMEs Centroamérica
        </text>
    </svg>
    '''
    
    try:
        with open('static/images/logo-sample.svg', 'w', encoding='utf-8') as f:
            f.write(logo_content.strip())
        print("✅ Logo de ejemplo creado en static/images/logo-sample.svg")
    except Exception as e:
        print(f"⚠️  No se pudo crear el logo de ejemplo: {e}")

def create_env_file():
    """Crear archivo .env de ejemplo"""
    print("\n⚙️ Creando archivo de configuración...")
    env_content = '''# Configuración de la aplicación
SECRET_KEY=tu-clave-secreta-super-segura-aqui
FLASK_ENV=development
FLASK_DEBUG=True

# Configuración de Gemini AI
GEMINI_API_KEY=tu-api-key-de-gemini-aqui

# Configuración de correo (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-password-de-aplicacion

# Configuración de la empresa
EMPRESA_NOMBRE=Tu Empresa Consultora
EMPRESA_EMAIL=contacto@tuempresa.com
EMPRESA_TELEFONO=+506-1234-5678
'''
    
    try:
        with open('.env.example', 'w', encoding='utf-8') as f:
            f.write(env_content.strip())
        print("✅ Archivo .env.example creado")
        print("   Copia este archivo a .env y configura tus valores")
    except Exception as e:
        print(f"⚠️  No se pudo crear .env.example: {e}")

def show_next_steps():
    """Mostrar los siguientes pasos"""
    print("\n" + "="*60)
    print("🎉 ¡CONFIGURACIÓN INICIAL COMPLETADA!")
    print("="*60)
    print("\n📋 PRÓXIMOS PASOS:")
    print("\n1. 🔑 Configurar API de Gemini:")
    print("   - Ve a: https://makersuite.google.com/app/apikey")
    print("   - Crea una API Key")
    print("   - Edita app.py línea 15 o configura GEMINI_API_KEY")
    
    print("\n2. 🎨 Personalizar tu marca:")
    print("   - Reemplaza el logo en static/images/")
    print("   - Edita templates/dashboard.html para tu branding")
    
    print("\n3. 🚀 Ejecutar la aplicación:")
    print("   python app.py")
    
    print("\n4. 🌐 Acceder a la aplicación:")
    print("   http://localhost:5000")
    
    print("\n📚 DOCUMENTACIÓN:")
    print("   - Lee README.md para más detalles")
    print("   - Revisa config.py para configuraciones avanzadas")
    
    print("\n💡 CONSEJOS:")
    print("   - Usa un entorno virtual para Python")
    print("   - Configura HTTPS para producción")
    print("   - Haz backup regular de la base de datos")
    
    print("\n" + "="*60)

def main():
    """Función principal de configuración"""
    print("🚀 CONFIGURACIÓN INICIAL - DIAGNÓSTICO DE MADUREZ DIGITAL")
    print("="*60)
    
    # Verificar Python
    if not check_python_version():
        return False
    
    # Instalar dependencias
    if not install_dependencies():
        return False
    
    # Crear directorios
    create_directories()
    
    # Inicializar base de datos
    if not initialize_database():
        return False
    
    # Verificar Gemini
    gemini_ok = check_gemini_config()
    
    # Crear archivos de ejemplo
    create_sample_logo()
    create_env_file()
    
    # Mostrar siguientes pasos
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Configuración completada exitosamente!")
        else:
            print("\n❌ Configuración completada con errores")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)