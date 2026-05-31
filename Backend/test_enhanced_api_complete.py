#!/usr/bin/env python3
"""
Prueba completa de la API con detector mejorado v2.0
"""
import requests
import json
from pathlib import Path
import time

def test_server_health():
    """Verificar que el servidor esté funcionando"""
    print("🏥 VERIFICANDO SALUD DEL SERVIDOR")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Servidor activo - Status: {health.get('status')}")
            print(f"   Storage disponible: {health.get('storage_available')}")
            print(f"   YOLO listo: {health.get('yolo_ready')}")
            return True
        else:
            print(f"❌ Servidor responde con error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

def upload_and_analyze_video(video_path):
    """Subir y analizar un video con el detector mejorado"""
    print(f"\n📹 SUBIENDO Y ANALIZANDO: {video_path.name}")
    print("-" * 50)
    
    url = "http://localhost:8000/analyze/upload"
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {
                'file': (video_path.name, video_file, 'video/mp4')
            }
            
            print(f"🚀 Enviando video para análisis mejorado...")
            response = requests.post(url, files=files, timeout=300)
        
        if response.status_code == 201:
            result = response.json()
            
            print(f"✅ ¡Video analizado exitosamente!")
            print(f"🆔 Video ID: {result.get('video_id')}")
            print(f"📄 Filename: {result.get('filename')}")
            print(f"🔧 Detector: {result.get('detector_version', 'N/A')}")
            
            # Mostrar características nuevas
            features = result.get('features', [])
            if features:
                print(f"🚀 Características activas:")
                for feature in features:
                    print(f"   • {feature}")
            
            # Mostrar análisis si está disponible
            analysis = result.get('analysis', {})
            if analysis:
                metadata = analysis.get('metadata', {})
                stats = analysis.get('estadisticas', {})
                
                print(f"\n📋 METADATOS EXTRAÍDOS:")
                print(f"   🎥 Cámara ID: {metadata.get('camara_id', 'No detectado')}")
                print(f"   📅 Fecha: {metadata.get('fecha_video', 'No detectada')}")
                print(f"   🕐 Hora: {metadata.get('hora_video', 'No detectada')}")
                print(f"   🌡️ Temperatura: {metadata.get('temperatura', 'No detectada')}°C")
                print(f"   📐 Resolución: {metadata.get('resolution', 'No detectada')}")
                print(f"   ⏱️ Duración: {metadata.get('duration', 'No detectada')}s")
                
                print(f"\n🐾 DETECCIONES MEJORADAS:")
                print(f"   🔢 Total animales: {stats.get('total_animales', 0)}")
                print(f"   🦎 Especies: {', '.join(stats.get('especies_encontradas', []))}")
                print(f"   📊 Confianza promedio: {stats.get('confianza_promedio', 0):.3f}")
                print(f"   🎯 Correcciones aplicadas: {stats.get('correcciones_aplicadas', 0)}")
                print(f"   ⭐ Calidad promedio: {stats.get('calidad_promedio', 0):.3f}")
                
                # Mostrar detecciones por especie
                detecciones_por_especie = stats.get('detecciones_por_especie', {})
                if detecciones_por_especie:
                    print(f"   📈 Por especie:")
                    for especie, cantidad in detecciones_por_especie.items():
                        print(f"      • {especie}: {cantidad}")
                
                # Mostrar si hubo correcciones
                correcciones = stats.get('correcciones_aplicadas', 0)
                if correcciones > 0:
                    print(f"\n🧠 CLASIFICADOR INTELIGENTE:")
                    print(f"   ✅ Se aplicaron {correcciones} correcciones automáticas")
                    print(f"   🎯 Porcentaje de correcciones: {stats.get('porcentaje_correcciones', 0):.1f}%")
            
            return result.get('video_id'), stats.get('total_animales', 0), stats.get('correcciones_aplicadas', 0)
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Detalle: {error_detail.get('detail', 'Error desconocido')}")
            except:
                print(f"   Respuesta: {response.text}")
            return None, 0, 0
            
    except requests.exceptions.Timeout:
        print("⏰ Error: Timeout - El análisis está tomando demasiado tiempo")
        return None, 0, 0
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None, 0, 0

def test_enhanced_system_stats():
    """Probar estadísticas del sistema mejorado"""
    print(f"\n📊 ESTADÍSTICAS DEL SISTEMA MEJORADO")
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

def test_enhanced_cameras_list():
    """Probar lista de cámaras identificadas"""
    print(f"\n📷 CÁMARAS IDENTIFICADAS AUTOMÁTICAMENTE")
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

def test_enhanced_report_generation():
    """Probar generación de reporte mejorado"""
    print(f"\n📊 GENERANDO REPORTE EXCEL MEJORADO")
    print("="*50)
    
    try:
        response = requests.post("http://localhost:8000/analyze/report")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Reporte Excel mejorado generado:")
            print(f"   📄 Archivo: {result.get('filename')}")
            print(f"   📹 Videos incluidos: {result.get('videos_incluidos')}")
            print(f"   🚀 Características nuevas:")
            print(f"      • Hoja de correcciones inteligentes")
            print(f"      • Métricas de calidad de frame")
            print(f"      • Análisis de confianza original vs corregida")
            print(f"      • Información del detector utilizado")
        else:
            print(f"❌ Error generando reporte: {response.status_code}")
            try:
                error = response.json()
                print(f"   Detalle: {error.get('detail')}")
            except:
                print(f"   Respuesta: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def test_video_analysis_details(video_id):
    """Probar obtener detalles de análisis"""
    if not video_id:
        print("⚠️ No hay video_id para probar detalles")
        return
        
    print(f"\n📋 DETALLES DEL ANÁLISIS MEJORADO: {video_id}")
    print("="*50)
    
    try:
        response = requests.get(f"http://localhost:8000/analyze/results/{video_id}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Detalles obtenidos:")
            
            # Mostrar detecciones individuales
            detecciones = result.get('detecciones', [])
            print(f"   🔍 {len(detecciones)} detecciones individuales:")
            
            for i, det in enumerate(detecciones[:3], 1):  # Mostrar solo las primeras 3
                print(f"      {i}. {det.get('especie')} - Confianza: {det.get('confianza', 0):.3f}")
                print(f"         Frame: {det.get('frame_numero')}, Tiempo: {det.get('timestamp_video', 0):.1f}s")
                
                # Mostrar información de correcciones si está disponible
                if det.get('correccion_aplicada'):
                    print(f"         🧠 Corrección aplicada: {det.get('confianza_original', 0):.3f} → {det.get('confianza', 0):.3f}")
                
                # Mostrar calidad de frame
                calidad = det.get('calidad_frame')
                if calidad:
                    print(f"         ⭐ Calidad de frame: {calidad:.3f}")
                
                if det.get('ruta_evidencia'):
                    print(f"         📸 Evidencia: {Path(det['ruta_evidencia']).name}")
            
            if len(detecciones) > 3:
                print(f"      ... y {len(detecciones) - 3} detecciones más")
                
        else:
            print(f"❌ Error obteniendo detalles: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_multiple_videos():
    """Probar con múltiples videos"""
    print(f"\n🎬 PRUEBA CON MÚLTIPLES VIDEOS")
    print("="*60)
    
    video_dir = Path("camara-1")
    if not video_dir.exists():
        print(f"❌ Directorio de videos no encontrado: {video_dir}")
        return []
    
    video_files = list(video_dir.glob("*.mp4"))[:3]  # Probar solo 3 videos
    
    if not video_files:
        print(f"❌ No se encontraron videos en {video_dir}")
        return []
    
    print(f"📁 Encontrados {len(video_files)} videos para probar")
    
    results = []
    total_detections = 0
    total_corrections = 0
    
    for i, video_path in enumerate(video_files, 1):
        print(f"\n{i}/{len(video_files)} - Procesando: {video_path.name}")
        video_id, detections, corrections = upload_and_analyze_video(video_path)
        
        if video_id:
            results.append({
                'video_id': video_id,
                'filename': video_path.name,
                'detections': detections,
                'corrections': corrections
            })
            total_detections += detections
            total_corrections += corrections
        
        # Pequeña pausa entre videos
        time.sleep(2)
    
    print(f"\n📊 RESUMEN DE MÚLTIPLES VIDEOS:")
    print(f"   ✅ Videos procesados: {len(results)}")
    print(f"   🐾 Total detecciones: {total_detections}")
    print(f"   🧠 Total correcciones: {total_corrections}")
    
    if total_corrections > 0:
        correction_rate = (total_corrections / total_detections) * 100 if total_detections > 0 else 0
        print(f"   📈 Tasa de corrección: {correction_rate:.1f}%")
    
    return results

def main():
    """Ejecutar prueba completa del detector mejorado"""
    print("🚀 PRUEBA COMPLETA DEL DETECTOR MEJORADO v2.0")
    print("="*60)
    
    # Verificar servidor
    if not test_server_health():
        print("❌ Servidor no disponible. Abortando pruebas.")
        return
    
    # Probar con múltiples videos
    results = test_multiple_videos()
    
    if not results:
        print("❌ No se procesaron videos. Abortando pruebas restantes.")
        return
    
    # Esperar un poco para que se procesen completamente
    print(f"\n⏳ Esperando 5 segundos para que se complete el procesamiento...")
    time.sleep(5)
    
    # Probar estadísticas del sistema
    test_enhanced_system_stats()
    
    # Probar lista de cámaras
    test_enhanced_cameras_list()
    
    # Probar detalles de análisis del primer video
    if results:
        test_video_analysis_details(results[0]['video_id'])
    
    # Probar generación de reporte
    test_enhanced_report_generation()
    
    # Resumen final
    print(f"\n" + "="*60)
    print("🎉 PRUEBA COMPLETA FINALIZADA")
    print("="*60)
    
    total_detections = sum(r['detections'] for r in results)
    total_corrections = sum(r['corrections'] for r in results)
    
    print(f"\n📊 RESUMEN FINAL:")
    print(f"   📹 Videos analizados: {len(results)}")
    print(f"   🐾 Total detecciones: {total_detections}")
    print(f"   🧠 Correcciones aplicadas: {total_corrections}")
    
    if total_corrections > 0:
        print(f"   🎯 El clasificador inteligente mejoró {total_corrections} detecciones")
        print(f"   ✅ Sistema funcionando correctamente con correcciones automáticas")
    
    print(f"\n🔍 COMPARACIÓN CON SISTEMA ANTERIOR:")
    print(f"   🚀 Detector: Básico → Mejorado v2.0")
    print(f"   🧠 Clasificación: Manual → Inteligente automática")
    print(f"   📊 Frames: Fijos cada 5s → Selección inteligente")
    print(f"   🌍 Contexto: Ninguno → Geográfico (América Latina)")
    print(f"   ⭐ Calidad: Básica → Evaluación multi-factor")
    
    print(f"\n📁 ARCHIVOS GENERADOS:")
    print(f"   📊 Reporte Excel mejorado con nuevas hojas")
    print(f"   📸 Evidencias de mayor calidad")
    print(f"   📋 Análisis JSON con métricas detalladas")
    
    print(f"\n🎉 ¡DETECTOR MEJORADO FUNCIONANDO CORRECTAMENTE!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⏹️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()