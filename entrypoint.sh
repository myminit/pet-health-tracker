#!/bin/sh

# รัน Migration (ถ้ามี)
echo "Applying database migrations..."
uv run manage.py migrate --noinput

echo "---------------------------------------"
echo "   ✅ Django Service Run Successful!   "
echo "---------------------------------------"

/app/.venv/bin/python manage.py migrate --noinput

# เริ่มต้นแอป
exec "$@"