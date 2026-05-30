#!/usr/bin/env python3
"""
Script de instalación y prueba del Sistema de Monitoreo de Fauna
"""

import subprocess
import sys
import os
import requests
import time
import json
from pathlib import Path

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🔄 {description}")
    print(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Exitoso")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}...")
        else:
            print(f"❌ {description} - Error")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Excepción: {e}")
        return False
    
    return True

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 8:
        print("❌ Se requiere Python 3.8 o superior")
        return False
    
    print("✅ Versión de Python compatible")
    return True

def install_dependencies():
    """Instalar dependencias"""
    print("\n📦 Instalando dependencias...")
    
    # Actualizar pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Actualizando pip"):
        return False
    
    # Instalar dependencias
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Instalando dependencias"):
        return False
    
    return True

def create_test_structure():
    """Crear estructura de prueba"""
    print("\n📁 Creando estructura de directorios...")
    
    # Crear directorio storage si no existe
    storage_path = Path("storage")
    storage_path.mkdir(exist_ok=True)
    
    print("✅ Estructura de directorios creada")
    return True

def start_server():
    """Iniciar servidor FastAPI"""
    print("\n🚀 Iniciando servidor FastAPI...")
    
    # Iniciar servidor en background
    try:
        import uvicorn
        import threading
        from main import app
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Esperar a que el servidor inicie
        time.sleep(5)
        
        # Verificar que el servidor está corriendo
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ Servidor iniciado correctamente")
                return True
            else:
                print(f"❌ Servidor respondió con código: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ No se pudo conectar al servidor: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return False

def test_api_endpoints():
    """Probar endpoints de la API"""
    print("\n🧪 Probando endpoints de la API...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check - OK")
        else:
            print(f"❌ Health check - Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check - Excepción: {e}")
        return False
    
    # Test 2: Crear cámara
    try:
        camera_data = {
            "nombre": "Cámara de Prueba",
            "ubicacion": "Laboratorio de Testing"
        }
        response = requests.post(f"{base_url}/cameras", json=camera_data)
        if response.status_code == 201:
            camera_info = response.json()
            camera_id = camera_info['id']
            print(f"✅ Crear cámara - OK (ID: {camera_id})")
        else:
            print(f"❌ Crear cámara - Error {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Crear cámara - Excepción: {e}")
        return False
    
    # Test 3: Listar cámaras
    try:
        response = requests.get(f"{base_url}/cameras")
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ Listar cámaras - OK ({len(cameras)} cámaras)")
        else:
            print(f"❌ Listar cámaras - Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Listar cámaras - Excepción: {e}")
        return False
    
    # Test 4: Obtener información de cámara
    try:
        response = requests.get(f"{base_url}/cameras/{camera_id}")
        if response.status_code == 200:
            print("✅ Obtener cámara - OK")
        else:
            print(f"❌ Obtener cámara - Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Obtener cámara - Excepción: {e}")
        return False
    
    # Test 5: Listar videos (debería estar vacío)
    try:
        response = requests.get(f"{base_url}/videos/{camera_id}")
        if response.status_code == 200:
            videos = response.json()
            print(f"✅ Listar videos - OK ({len(videos)} videos)")
        else:
            print(f"❌ Listar videos - Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Listar videos - Excepción: {e}")
        return False
    
    # Test 6: Obtener resultados (debería estar vacío)
    try:
        response = requests.get(f"{base_url}/process/camera/{camera_id}/results")
        if response.status_code == 200:
            results = response.json()
            print("✅ Obtener resultados - OK (sin datos)")
        else:
            print(f"❌ Obtener resultados - Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Obtener resultados - Excepción: {e}")
        return False
    
    print("\n🎉 Todos los tests de API pasaron correctamente!")
    return True

def show_next_steps():
    """Mostrar próximos pasos"""
    print("\n" + "="*60)
    print("🎉 INSTALACIÓN Y PRUEBAS COMPLETADAS EXITOSAMENTE!")
    print("="*60)
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("\n1. 🌐 Acceder a la documentación:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    
    print("\n2. 🎬 Para probar con videos reales:")
    print("   - Subir un video usando POST /videos/upload")
    print("   - Procesar con POST /process/camera/{camera_id}")
    
    print("\n3. 🔧 Configuración avanzada:")
    print("   - Editar app/utils/yolo_detector.py para cambiar modelo YOLO")
    print("   - Ajustar intervalos y umbrales de confianza")
    
    print("\n4. 📊 Estructura de archivos:")
    print("   - Videos: storage/camera_id/videos/")
    print("   - Evidencias: storage/camera_id/evidencias/")
    print("   - Reportes: storage/camera_id/excel/")
    
    print("\n5. 🐛 Logs y debugging:")
    print("   - Revisar app.log para logs detallados")
    print("   - Health check: http://localhost:8000/health")
    
    print("\n" + "="*60)

def main():
    """Función principal"""
    print("🦎 Sistema de Monitoreo de Fauna - Instalación y Pruebas")
    print("="*60)
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Crear estructura
    if not create_test_structure():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_dependencies():
        sys.exit(1)
    
    # Iniciar servidor
    if not start_server():
        sys.exit(1)
    
    # Probar API
    if not test_api_endpoints():
        sys.exit(1)
    
    # Mostrar próximos pasos
    show_next_steps()

if __name__ == "__main__":
    main()