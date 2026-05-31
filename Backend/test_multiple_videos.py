#!/usr/bin/env python3
"""
Script para probar múltiples videos y generar reporte
"""
import requests
import json
from pathlib import Path
import time

def upload_video(video_path):
    """Subir un video específico"""
    url = "http://localhost:8000/analyze/upload"
    
    print(f"📹 Subiendo: {video_path.name}")
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {
                'file': (video_path.name, video_file, 'video/mp4')
            }
            
            response = requests.post(url, files=files, timeout=300)
        
        if response.status_code == 201:
            result = response.json()
            video_id = result.get('video_id')
            analysis = result.get('analysis', {})
            metadata = analysis.get('metadata', {})
            stats = analysis.get('estadisticas', {})
            
            print(f"   ✅ ID: {video_id}")
            print(f"   📷 Cámara: {metadata.get('camara_id', 'No detectada')}")
            print(f"   🐾 Animales: {stats.get('total_animales', 0)}")
            if stats.get('especies_encontradas'):
                print(f"   🦎 Especies: {', '.join(stats['especies_encontradas'])}")
            
            return video_id, stats.get('total_animales', 0)
        else:
            print(f"   ❌ Error: {response.status_code}")
            return None, 0
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, 0

def test_multiple_videos():
    """Probar con múltiples videos"""
    print("🎬 PROBANDO MÚLTIPLES VIDEOS")
    print("="*50)
    
    video_dir = Path("camara-1")
    video_files = list(video_dir.glob("*.mp4"))[:5]  # Probar solo 5 videos
    
    print(f"📁 Encontrados {len(video_files)} videos para probar")
    
    video_ids = []
    total_detections = 0
    
    for i, video_path in enumerate(video_files, 1):
        print(f"\n{i}/{len(video_files)} - {video_path.name}")
        video_id, detections = upload_video(video_path)
        
        if video_id:
            video_ids.append(video_id)
            total_detections += detections
        
        # Pequeña pausa entre videos
        time.sleep(1)
    
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ Videos procesados: {len(video_ids)}")
    print(f"   🐾 Total detecciones: {total_detections}")
    
    return video_ids

def test_generate_report():
    """Probar generación de reporte Excel"""
    print("\n" + "="*50)
    print("📊 PROBANDO GENERACIÓN DE REPORTE EXCEL")
    print("="*50)
    
    try:
        response = requests.post("http://localhost:8000/analyze/report")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Reporte Excel generado:")
            print(f"   📄 Archivo: {result.get('filename')}")
            print(f"   📹 Videos incluidos: {result.get('videos_incluidos')}")
        else:
            print(f"❌ Error generando reporte: {response.status_code}")
            try:
                error = response.json()
                print(f"   Detalle: {error.get('detail')}")
            except:
                print(f"   Respuesta: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def test_final_stats():
    """Mostrar estadísticas finales"""
    print("\n" + "="*50)
    print("📊 ESTADÍSTICAS FINALES DEL SISTEMA")
    print("="*50)
    
    try:
        # Estadísticas generales
        response = requests.get("http://localhost:8000/system/stats")
        if response.status_code == 200:
            stats = response.json()
            print("📈 ESTADÍSTICAS GENERALES:")
            print(f"   📹 Total videos analizados: {stats.get('total_videos', 0)}")
            print(f"   🐾 Total detecciones: {stats.get('total_detecciones', 0)}")
            print(f"   📷 Cámaras identificadas: {len(stats.get('camaras_identificadas', []))}")
            print(f"   🦎 Especies encontradas: {len(stats.get('especies_encontradas', []))}")
            
            if stats.get('camaras_identificadas'):
                print(f"   📷 IDs de cámaras: {', '.join(stats['camaras_identificadas'])}")
            
            if stats.get('especies_encontradas'):
                print(f"   🦎 Especies detectadas: {', '.join(stats['especies_encontradas'])}")
            
            # Detecciones por especie
            detecciones_por_especie = stats.get('detecciones_por_especie', {})
            if detecciones_por_especie:
                print("   📊 Detecciones por especie:")
                for especie, cantidad in detecciones_por_especie.items():
                    print(f"      • {especie}: {cantidad}")
        
        # Lista de cámaras
        response = requests.get("http://localhost:8000/system/cameras")
        if response.status_code == 200:
            cameras = response.json()
            print(f"\n📷 CÁMARAS IDENTIFICADAS ({len(cameras)}):")
            
            for camera in cameras:
                print(f"   🆔 {camera.get('camara_id')}:")
                print(f"      📹 Videos: {camera.get('videos_procesados', 0)}")
                print(f"      🐾 Detecciones: {camera.get('total_detecciones', 0)}")
                if camera.get('especies_encontradas'):
                    print(f"      🦎 Especies: {', '.join(camera['especies_encontradas'])}")
                if camera.get('temperatura_promedio'):
                    print(f"      🌡️ Temp. promedio: {camera['temperatura_promedio']}°C")
                    
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")

if __name__ == "__main__":
    print("🎬 PRUEBA COMPLETA DE MÚLTIPLES VIDEOS")
    print("="*60)
    
    # Verificar servidor
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor no disponible")
            exit(1)
        print("✅ Servidor activo")
    except:
        print("❌ No se puede conectar al servidor")
        exit(1)
    
    # Ejecutar pruebas
    video_ids = test_multiple_videos()
    test_generate_report()
    test_final_stats()
    
    print("\n" + "="*60)
    print("🎉 ¡PRUEBA COMPLETA FINALIZADA!")
    print("="*60)