import os
import shutil
import subprocess
import sys

def crear_ejecutable():
    print("🔨 Creando ejecutable para distribución...")
    
    # Instalar PyInstaller si no está instalado
    try:
        import PyInstaller
    except ImportError:
        print("📦 Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Crear spec file personalizado
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('VERSION', '.'),
    ],
    hiddenimports=[
        'google.generativeai',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.platypus',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DiagnosticoDigital',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('diagnostico.spec', 'w') as f:
        f.write(spec_content)
    
    # Ejecutar PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',
        '--add-data', 'templates;templates',
        '--add-data', 'static;static',
        '--add-data', 'VERSION;.',
        '--name', 'DiagnosticoDigital',
        'app.py'
    ]
    
    subprocess.run(cmd)
    
    print("✅ Ejecutable creado en dist/DiagnosticoDigital.exe")
    print("📋 Instrucciones para usuarios:")
    print("   1. Descargar DiagnosticoDigital.exe")
    print("   2. Ejecutar el archivo")
    print("   3. Abrir navegador en http://localhost:5000")

if __name__ == "__main__":
    crear_ejecutable()