import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
import torch
from ultralytics import YOLO
from fastapi.responses import JSONResponse
from PIL import Image
import io
import numpy as np


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ml_models = {}
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading YOLO model...")
    try:
        from ultralytics.nn.tasks import DetectionModel
        torch.serialization.add_safe_globals([DetectionModel])
    except Exception as e:
        logger.warning(f"Could not add safe global: {e}")
    
    ml_models["yolov8n"] = YOLO('yolov8n.pt')
    logger.info("Model loaded successfully!")
    yield
    ml_models.clear()

app = FastAPI(
    title="API nhận diện đối tượng sử dụng YOLO.",
    description="FastAPI service cho nhận diện đối tượng.",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check"""
    return {
        "message": "YOLO object detection API",
        "status": "running",
        "model": "YOLOv8n"
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "model_loaded": "yolov8n" in ml_models
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> JSONResponse:
    """
    Predict objects in uploaded image
    
        :param file: Image file
        :type file: UploadFile

    Returns:
        Json with detected objects and their bounding boxes.
    """
    if "yolov8n" not in ml_models:
        raise HTTPException(status_code=503, detail="Model not loaded")

    model = ml_models["yolov8n"]

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        img_array = np.array(image)

        logger.info(f"Running inference on image: {file.filename}")
        results = model(img_array)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                detection = {
                    "class": result.name[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": {
                        "x1": float(box.xyxy[0][0]),
                        "y1": float(box.xyxy[0][1]),
                        "x2": float(box.xyxy[0][2]),
                        "y2": float(box.xyxy[0][3])
                    }
                }
                detections.append(detection)
        logger.info(f"Found {len(detections)} objects")
        return JSONResponse(content={
            "filename": file.filename,
            "detections": detections,
            "count": len(detections)
        })
    except Exception as e:
        logger.error(f"Error durring prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")        
    
@app.get("/model-infor")
async def model_info() -> JSONResponse:
    """Get model information."""
    if "yolov8n" not in ml_models:
        raise HTTPException(status_code=503, detail="Model not loaded")
    model = ml_models["yolov8n"]
    return JSONResponse(content={
        "model_name": "Yolov8n",
        "classes": list(model.names.values()),
        "num_classes": len(model.names)
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app=app, host="0.0.0.0", port=8001)