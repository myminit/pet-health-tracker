FROM python:3.12-slim

# ตั้งค่า Environment มาตรฐาน
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

# Layer Caching สำหรับ Dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy โค้ดทั้งหมด
COPY . .

# ตั้งค่าสิทธิ์และเรียกใช้ Entrypoint (สำหรับพ่น Run Successful และ Migrate)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

ENV PATH="/app/.venv/bin:$PATH"

# 2. แก้ไข CMD ให้เรียกใช้ python ผ่าน uv run เพื่อความชัวร์
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]