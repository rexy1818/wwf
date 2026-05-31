#!/usr/bin/env python3
"""
Prueba específica de la mejora quirúrgica:
- Máximo 3 fotos por especie
- 1 foto con bounding box (la mejor)
- 2 fotos limpias (sin marcas)
"""
import requests
import json
from pathlib import Path
import time

def test_surgical_improvement():
    """Probar la mejora quirúrgica del detector"""
    print("🔬 PROBANDO MEJORA QUIRÚRGICA DEL DETECTOR")
    print("="*60)
    print("📋 Características a probar:")
    print("   • Máximo 3 fotos por especie detectada")
    print("   • 1 foto con bounding box verde + etiqueta")
    print("   • 2 fotos limpias (sin marcas)")
    print("   • Selección basada en nitidez y confianza")
    
    # Verificar servidor
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor no disponible")
            return
        print("✅ Servidor activo")
    except:
        print("❌ No se puede conectar al servidor")
        return
    
    # Seleccionar video de prueba
    video_dir = Path("camara-1")
    if not video_dir.exists():
        print(f"❌ Directorio de videos no encontrado: {video_dir}")
        return
    
    video_files = list(video_dir.glob("*.mp4"))
    if not video_files:
        print(f"❌ No se encontraron videos en {video_dir}")
        return
    
    # Usar el primer video
    test_video = video_files[0]
    print(f"\n📹 Video de prueba: {test_video.name}")
    
    # Subir y analizar
    print(f"\n🚀 SUBIENDO VIDEO PARA ANÁLISIS QUIRÚRGICO...")
    
    url = "http://localhost:8000/analyze/upload"
    
    try:
        with open(test_video, 'rb') as video_file:
            files = {
                'file': (test_video.name, video_file, 'video/mp4')
            }
            
            response = requests.post(url, files=files, timeout=300)
        
        if response.status_code == 201:
            result = response.json()
            video_id = result.get('video_id')
            
            print(f"✅ Video analizado exitosamente!")
            print(f"🆔 Video ID: {video_id}")
            
            # Mostrar estadísticas
            analysis = result.get('analysis', {})
            stats = analysis.get('estadisticas', {})
            
            print(f"\n📊 ESTADÍSTICAS:")
            print(f"   🐾 Total detecciones: {stats.get('total_animales', 0)}")
            print(f"   🦎 Especies: {', '.join(stats.get('especies_encontradas', []))}")
            print(f"   📊 Confianza promedio: {stats.get('confianza_promedio', 0):.3f}")
            
            # Esperar procesamiento
            print(f"\n⏳ Esperando 3 segundos para completar procesamiento...")
            time.sleep(3)
            
            # Obtener detalles del análisis
            print(f"\n🔍 OBTENIENDO DETALLES DEL ANÁLISIS...")
            
            detail_response = requests.get(f"http://localhost:8000/analyze/results/{video_id}")
            
            if detail_response.status_code == 200:
                details = detail_response.json()
                detecciones = details.get('detecciones', [])
                
                print(f"✅ Detalles obtenidos: {len(detecciones)} detecciones")
                
                # Analizar estructura de fotos por especie
                species_photos = {}
                
                for det in detecciones:
                    especie = det.get('especie')
                    photo_rank = det.get('photo_rank', 1)
                    has_bbox = det.get('has_bounding_box', False)
                    photo_type = det.get('photo_type', 'unknown')
                    ruta = det.get('ruta_evidencia', '')
                    
                    if especie not in species_photos:
                        species_photos[especie] = []
                    
                    species_photos[especie].append({
                        'rank': photo_rank,
                        'has_bbox': has_bbox,
                        'type': photo_type,
                        'path': ruta,
                        'confidence': det.get('confianza', 0),
                        'quality': det.get('calidad_frame', 0)
                    })
                
                # Mostrar resultados de la mejora quirúrgica
                print(f"\n🔬 RESULTADOS DE LA MEJORA QUIRÚRGICA:")
                print("="*50)
                
                for especie, photos in species_photos.items():
                    print(f"\n🦎 {especie.upper()}:")
                    print(f"   📸 Total fotos: {len(photos)}")
                    
                    if len(photos) <= 3:
                        print(f"   ✅ Límite respetado (≤3 fotos)")
                    else:
                        print(f"   ❌ Límite excedido ({len(photos)} fotos)")
                    
                    # Verificar estructura de fotos
                    bbox_photos = [p for p in photos if p['has_bbox']]
                    clean_photos = [p for p in photos if not p['has_bbox']]
                    
                    print(f"   📦 Fotos con bounding box: {len(bbox_photos)}")
                    print(f"   🖼️ Fotos limpias: {len(clean_photos)}")
                    
                    if len(bbox_photos) == 1:
                        print(f"   ✅ Exactamente 1 foto con bbox")
                    else:
                        print(f"   ❌ Debería haber 1 foto con bbox, encontradas: {len(bbox_photos)}")
                    
                    # Mostrar detalles de cada foto
                    for i, photo in enumerate(sorted(photos, key=lambda x: x['rank']), 1):
                        bbox_indicator = "📦 CON BBOX" if photo['has_bbox'] else "🖼️ LIMPIA"
                        filename = Path(photo['path']).name if photo['path'] else 'N/A'
                        
                        print(f"      {i}. {bbox_indicator}")
                        print(f"         Archivo: {filename}")
                        print(f"         Confianza: {photo['confidence']:.3f}")
                        print(f"         Calidad: {photo['quality']:.3f}")
                        print(f"         Rank: #{photo['rank']}")
                
                # Verificar archivos generados
                print(f"\n📁 VERIFICANDO ARCHIVOS GENERADOS...")
                
                evidencias_dir = Path("video_analysis/analysis")
                
                if evidencias_dir.exists():
                    # Buscar directorio del video
                    video_dirs = list(evidencias_dir.glob(f"*{video_id}*"))
                    
                    if video_dirs:
                        video_dir = video_dirs[0]
                        evidencias_path = video_dir / "evidencias"
                        
                        if evidencias_path.exists():
                            print(f"✅ Directorio de evidencias encontrado: {evidencias_path}")
                            
                            # Listar archivos por especie
                            for species_dir in evidencias_path.iterdir():
                                if species_dir.is_dir():
                                    species_name = species_dir.name
                                    image_files = list(species_dir.glob("*.jpg"))
                                    
                                    print(f"\n   📂 {species_name}:")
                                    print(f"      📸 Archivos generados: {len(image_files)}")
                                    
                                    bbox_files = [f for f in image_files if '_bbox' in f.name]
                                    clean_files = [f for f in image_files if '_clean' in f.name]
                                    
                                    print(f"      📦 Con bbox: {len(bbox_files)}")
                                    print(f"      🖼️ Limpias: {len(clean_files)}")
                                    
                                    # Mostrar nombres de archivos
                                    for img_file in image_files:
                                        file_type = "📦 BBOX" if '_bbox' in img_file.name else "🖼️ LIMPIA"
                                        print(f"         {file_type}: {img_file.name}")
                        else:
                            print(f"❌ No se encontró directorio de evidencias")
                    else:
                        print(f"❌ No se encontró directorio del video")
                else:
                    print(f"❌ No se encontró directorio de análisis")
                
                # Resumen final
                print(f"\n" + "="*60)
                print(f"🎯 RESUMEN DE LA MEJORA QUIRÚRGICA")
                print("="*60)
                
                total_species = len(species_photos)
                total_photos = sum(len(photos) for photos in species_photos.values())
                total_bbox = sum(len([p for p in photos if p['has_bbox']]) for photos in species_photos.values())
                total_clean = sum(len([p for p in photos if not p['has_bbox']]) for photos in species_photos.values())
                
                print(f"📊 Especies detectadas: {total_species}")
                print(f"📸 Total fotos generadas: {total_photos}")
                print(f"📦 Fotos con bounding box: {total_bbox}")
                print(f"🖼️ Fotos limpias: {total_clean}")
                
                # Verificar cumplimiento de reglas
                rules_ok = True
                
                for especie, photos in species_photos.items():
                    if len(photos) > 3:
                        print(f"❌ {especie}: {len(photos)} fotos (máximo 3)")
                        rules_ok = False
                    
                    bbox_count = len([p for p in photos if p['has_bbox']])
                    if bbox_count != 1:
                        print(f"❌ {especie}: {bbox_count} fotos con bbox (debe ser 1)")
                        rules_ok = False
                
                if rules_ok:
                    print(f"\n🎉 ¡MEJORA QUIRÚRGICA IMPLEMENTADA CORRECTAMENTE!")
                    print(f"✅ Todas las reglas se cumplen:")
                    print(f"   • Máximo 3 fotos por especie ✅")
                    print(f"   • 1 foto con bounding box por especie ✅")
                    print(f"   • Fotos limpias adicionales ✅")
                else:
                    print(f"\n⚠️ Algunas reglas no se cumplen. Revisar implementación.")
                
            else:
                print(f"❌ Error obteniendo detalles: {detail_response.status_code}")
        
        else:
            print(f"❌ Error subiendo video: {response.status_code}")
            try:
                error = response.json()
                print(f"   Detalle: {error.get('detail')}")
            except:
                print(f"   Respuesta: {response.text}")
    
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    test_surgical_improvement()