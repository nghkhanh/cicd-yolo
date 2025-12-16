yolo11n_url := "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"

default:
    @just --list

download-models:
    mkdir -p checkpoints
    wget -O checkpoints/yolo11n.pt {{yolo11n_url}}