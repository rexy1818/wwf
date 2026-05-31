from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from app.services.video_service import VideoService

router = APIRouter()
video_service = VideoService()

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # Crear carpetas si no existen
    os.makedirs("storage/uploads", exist_ok=True)
    
    file_path = os.path.join("storage/uploads", file.filename)
    
    # Guardar archivo de forma segura
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    return {"success": True, "filename": file.filename}

@router.get("/process/{video_name}")
def process_video(video_name: str):
    try:
        video_path = f"storage/uploads/{video_name}"
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
            
        result = video_service.process_video(video_path)
        
        return {
            "success": True,
            "video": video_name,
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}