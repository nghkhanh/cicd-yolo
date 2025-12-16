### 1. Giai đoạn BUILDER (Xây dựng)

* **`FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder`**: Sử dụng Image của `uv` (viết bằng Rust) giúp tốc độ cài đặt thư viện nhanh gấp nhiều lần `pip`. Bản `slim` giúp Image Builder nhẹ hơn.
* **`ENV UV_COMPILE_BYTECODE=1`**: Yêu cầu `uv` biên dịch code Python sang bytecode (`.pyc`). Việc này giúp ứng dụng khi khởi chạy ở Runtime nhanh hơn vì không mất công biên dịch lại.
* **`ENV UV_LINK_MODE=copy`**: Buộc `uv` phải copy các thư viện vào folder `.venv` thay vì dùng "hardlink". Điều này giúp khi bạn copy folder `.venv` sang Stage khác, các file sẽ không bị lỗi đường dẫn.
* **`RUN apt-get update ... install ... build-essential gcc`**: Cài đặt các công cụ biên dịch mã nguồn C/C++. Một số thư viện Python (như `torch` hoặc `numpy`) cần các công cụ này để cài đặt thành công.
* **`COPY uv.lock README.md pyproject.toml ./`**: Chỉ copy các file cấu hình dự án trước. 
* **`RUN --mount=type=cache,target=/root/.cache/uv uv sync ... --no-install-project`**: 
    * **`--mount=type=cache`**: Đây là kỹ thuật đỉnh cao để Docker giữ lại cache của `uv`. Nếu bạn build lại lần sau, nó sẽ không tải lại những thư viện đã có.
    * **`--no-install-project`**: Lệnh này bảo `uv`: "Chỉ cài thư viện bên ngoài thôi, đừng cài code của tôi vào venv vội". Điều này giúp Docker lưu cache của các thư viện nặng (như Torch) riêng biệt.
* **`COPY ./src /app/src`**: Sau khi đã cài xong thư viện nặng, mới copy code dự án vào.
* **`RUN ... uv sync ...`**: Lúc này mới thực sự cài đặt chính dự án của bạn vào môi trường ảo.



---

### 2. Giai đoạn RUNTIME (Chạy ứng dụng)

* **`FROM python:3.11-slim-bookworm AS runtime`**: Sử dụng Image Python sạch. Lưu ý bạn đã đồng nhất bản **3.11** ở cả 2 Stage (điều này rất quan trọng để tránh lỗi không tương thích).
* **`RUN apt-get install ... libgl1-mesa-glx libglib2.0-0`**: Đây là các thư viện hệ thống cần thiết để chạy OpenCV. Nếu thiếu 2 dòng này, YOLO sẽ báo lỗi `ImportError` vì không xử lý được hình ảnh.
* **`RUN useradd -m -u 1000 user`**: Tạo một user thường tên là `user`. Chạy app bằng user thường thay vì `root` giúp container của bạn cực kỳ bảo mật.
* **`COPY --from=builder --chown=1000 /app/.venv /app/.venv`**: 
    * **`--from=builder`**: Chỉ lấy folder `.venv` đã build xong từ Stage trước.
    * **`--chown=1000`**: Giao quyền sở hữu folder này cho user thường mà bạn vừa tạo.
* **`ENV PATH="/app/.venv/bin:$PATH"`**: Thêm đường dẫn môi trường ảo vào hệ thống. Từ nay bạn có thể gõ trực tiếp `python` hoặc `uvicorn` mà không cần kích hoạt venv.
* **`USER user`**: Chuyển sang quyền user thường. Từ dòng này trở đi, mọi lệnh đều không dùng quyền root.
* **`RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`**: Lệnh này cực kỳ khôn ngoan. Nó tải sẵn file model YOLO (`.pt`) về Image ngay lúc build. Khi bạn mang Image này đi deploy, container sẽ chạy ngay lập tức mà không cần chờ tải model từ internet.
* **`CMD ["uvicorn", "cicd_yolo.model:app", ...]`**: Lệnh mặc định để khởi động FastAPI server.
