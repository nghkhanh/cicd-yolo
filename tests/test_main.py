from fastapi.testclient import TestClient
from cicd_yolo import app, ml_models
import pytest
from ultralytics import YOLO
from PIL import Image
import io

client = TestClient(app=app)

@pytest.fixture(scope="module", autouse=True)
def load_model():
    """Load model before running tests"""
    ml_models["yolov8n"] = YOLO('yolov8n.pt')
    yield
    ml_models.clear()

def creat_test_image():
    """Creat a simple test image"""
    img = Image.new('RGB', (640, 480), color='RED')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_predict_endpoint():
    """Test prediction endpoint with test image"""
    test_img = creat_test_image()
    response = client.post(
        "/predict",
        files={"file": ("test.jpg", test_img, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "detections" in data
    assert "count" in data
    assert isinstance(data["detections"], list)

def test_predict_without_file():
    """Test prediction endpoint without file"""
    response = client.post("/predict")
    assert response.status_code == 422
