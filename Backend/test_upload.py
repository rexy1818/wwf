#!/usr/bin/env python3
"""
Script para probar la API de análisis de videos
"""
import requests
import json
from pathlib import Path

def test_upload_video():
    """Probar subida y análisis de video"""
    
    # URL del endpoint
    url = "http://localhost:8000/analyze/upload"
    
    # Archivo de video a subir
    video_path = Path("camara-1/WhatsApp Video 2026-05-30 at 12.38.25.mp4")
    
    if not video_path.exists():
        print(f"❌ Error: No se encontró el video {video_path}")
        return
    
    print(f"📹 Subiendo video: {video_path.name}")
    print(f"📁 Tamaño: {video_path.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        # Preparar archivo para subida
        with open(video_path, 'rb') as video_file:
            files = {
                'file': (video_path.name, video_file, 'video/mp4')
            }
            
            print("🚀 Enviando video para análisis...")
            response = requests.post(url, files=files, timeout=300)  # 5 minutos timeout
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ ¡Video analizado exitosamente!")
            print(f"🆔 Video ID: {result.get('video_id')}")
            print(f"📄 Filename: {result.get('filename')}")
            print(f"⏰ Upload time: {result.get('upload_time')}")
            
            # Mostrar análisis si está disponible
            analysis = result.get('analysis', {})
            if analysis:
                metadata = analysis.get('metadata', {})
                stats = analysis.get('estadisticas', {})
                
                print("\n📋 METADATOS EXTRAÍDOS:")
                print(f"   🎥 Cámara ID: {metadata.get('camara_id', 'No detectado')}")
                print(f"   📅 Fecha: {metadata.get('fecha_video', 'No detectada')}")
                print(f"   🕐 Hora: {metadata.get('hora_video', 'No detectada')}")
                print(f"   🌡️ Temperatura: {metadata.get('temperatura', 'No detectada')}°C")
                print(f"   📐 Resolución: {metadata.get('resolution', 'No detectada')}")
                print(f"   ⏱️ Duración: {metadata.get('duration', 'No detectada')}s")
                
                print("\n🐾 DETECCIONES:")
                print(f"   🔢 Total animales: {stats.get('total_animales', 0)}")
                print(f"   🦎 Especies: {', '.join(stats.get('especies_encontradas', []))}")
                print(f"   📊 Confianza promedio: {stats.get('confianza_promedio', 0):.3f}")
                
                # Mostrar detecciones por especie
                detecciones_por_especie = stats.get('detecciones_por_especie', {})
                if detecciones_por_especie:
                    print("   📈 Por especie:")
                    for especie, cantidad in detecciones_por_especie.items():
                        print(f"      • {especie}: {cantidad}")
            
            return result.get('video_id')
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Detalle: {error_detail.get('detail', 'Error desconocido')}")
            except:
                print(f"   Respuesta: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ Error: Timeout - El análisis está tomando demasiado tiempo")
        return None
    except requests.exceptions.ConnectionError:
        print("🔌 Error: No se pudo conectar al servidor. ¿Está corriendo en puerto 8000?")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def test_system_stats():
    """Probar estadísticas del sistema"""
    print("\n" + "="*50)
    print("📊 PROBANDO ESTADÍSTICAS DEL SISTEMA")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:8000/system/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Estadísticas obtenidas:")
            print(f"   📹 Total videos: {stats.get('total_videos', 0)}")
            print(f"   🐾 Total detecciones: {stats.get('total_detecciones', 0)}")
            print(f"   📷 Cámaras identificadas: {len(stats.get('camaras_identificadas', []))}")
            print(f"   🦎 Especies encontradas: {len(stats.get('especies_encontradas', []))}")
            
            if stats.get('camaras_identificadas'):
                print(f"   📷 IDs de cámaras: {', '.join(stats['camaras_identificadas'])}")
            
            if stats.get('especies_encontradas'):
                print(f"   🦎 Especies: {', '.join(stats['especies_encontradas'])}")
                
        else:
            print(f"❌ Error obteniendo estadísticas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_cameras_list():
    """Probar lista de cámaras identificadas"""
    print("\n" + "="*50)
    print("📷 PROBANDO LISTA DE CÁMARAS")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:8000/system/cameras")
        if response.status_code == 200:
            cameras = response.json()
            print(f"✅ Encontradas {len(cameras)} cámaras:")
            
            for i, camera in enumerate(cameras, 1):
                print(f"\n   📷 Cámara {i}:")
                print(f"      🆔 ID: {camera.get('camara_id')}")
                print(f"      📹 Videos procesados: {camera.get('videos_procesados', 0)}")
                print(f"      🐾 Total detecciones: {camera.get('total_detecciones', 0)}")
                print(f"      🦎 Especies: {', '.join(camera.get('especies_encontradas', []))}")
                print(f"      🌡️ Temp. promedio: {camera.get('temperatura_promedio')}°C")
                
        else:
            print(f"❌ Error obteniendo cámaras: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_video_result(video_id):
    """Probar obtener resultado de análisis"""
    if not video_id:
        print("⚠️ No hay video_id para probar resultados")
        return
        
    print("\n" + "="*50)
    print(f"📋 PROBANDO RESULTADO DE ANÁLISIS: {video_id}")
    print("="*50)
    
    try:
        response = requests.get(f"http://localhost:8000/analyze/results/{video_id}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Resultado detallado obtenido:")
            
            # Mostrar detecciones individuales
            detecciones = result.get('detecciones', [])
            print(f"   🔍 {len(detecciones)} detecciones individuales:")
            
            for i, det in enumerate(detecciones[:5], 1):  # Mostrar solo las primeras 5
                print(f"      {i}. {det.get('especie')} - Confianza: {det.get('confianza', 0):.3f}")
                print(f"         Frame: {det.get('frame_numero')}, Tiempo: {det.get('timestamp_video', 0):.1f}s")
                if det.get('ruta_evidencia'):
                    print(f"         📸 Evidencia: {Path(det['ruta_evidencia']).name}")
            
            if len(detecciones) > 5:
                print(f"      ... y {len(detecciones) - 5} detecciones más")
                
        else:
            print(f"❌ Error obteniendo resultado: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎬 INICIANDO PRUEBAS DE LA API DE ANÁLISIS DE FAUNA")
    print("="*60)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Servidor activo - Status: {health.get('status')}")
        else:
            print("❌ Servidor no responde correctamente")
            exit(1)
    except:
        print("❌ No se puede conectar al servidor. ¿Está corriendo en puerto 8000?")
        exit(1)
    
    # Ejecutar pruebas
    print("\n" + "="*50)
    print("📤 PROBANDO SUBIDA Y ANÁLISIS DE VIDEO")
    print("="*50)
    
    video_id = test_upload_video()
    
    # Esperar un poco para que se complete el procesamiento
    if video_id:
        import time
        print("\n⏳ Esperando 3 segundos para que se complete el procesamiento...")
        time.sleep(3)
    
    # Probar otros endpoints
    test_system_stats()
    test_cameras_list()
    test_video_result(video_id)
    
    print("\n" + "="*60)
    print("🎉 ¡PRUEBAS COMPLETADAS!")
    print("="*60)